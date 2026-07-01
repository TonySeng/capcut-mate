from src.utils.logger import logger
import config
import src.pyJianYingDraft as draft
from src.utils.draft_cache import update_cache
from exceptions import CustomException, CustomError
import datetime
import uuid
import os
import shutil
import re
from urllib.parse import quote
from typing import Optional


def _sanitize_draft_name(name: str) -> str:
    """
    清理草稿名称，移除文件系统不安全的字符

    保留中文等非 ASCII 字符（下载时 get_draft 会对 URL 做 percent-encode，
    因此中文草稿名可全链路正常工作）；仅处理文件系统不允许的字符与空白。

    Args:
        name: 原始草稿名称

    Returns:
        清理后的安全名称
    """
    # 移除或替换文件系统不允许的字符: \ / : * ? " < > |
    # 以及控制字符和其他特殊字符
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # 将空白字符（空格、制表符等）统一替换为下划线，避免 URL/路径中出现空格
    sanitized = re.sub(r'\s+', '_', sanitized)
    # 去除首尾空格和点号（Windows 不允许）
    sanitized = sanitized.strip(' .')
    # 如果清理后为空，返回默认名称
    if not sanitized:
        return "draft"
    # 限制长度（避免路径过长）
    return sanitized[:50]


def create_draft(width: int, height: int, draft_name: Optional[str] = None) -> str:
    """
    基于模板创建剪映草稿的业务逻辑

    Args:
        width: 草稿宽度
        height: 草稿高度
        draft_name: 自定义草稿名称（可选），不提供则自动生成

    Returns:
        draft_url: 草稿URL

    Raises:
        CustomException: 草稿创建失败
    """
    # 生成草稿ID
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    if draft_name:
        # 使用自定义名称 + 时间戳
        sanitized_name = _sanitize_draft_name(draft_name)
        draft_id = f"{sanitized_name}_{timestamp}"
        logger.info(f"Creating draft with custom name: {draft_name} -> {draft_id}")
    else:
        # 使用默认的时间戳 + UUID
        unique_id = uuid.uuid4().hex[:8]
        draft_id = f"{timestamp}{unique_id}"
        logger.info(f"Creating draft with auto-generated ID: {draft_id}")

    logger.info(f"draft_id: {draft_id}, width: {width}, height: {height}")

    # 使用模板创建草稿
    try:
        # 复制模板到新草稿目录
        template_path = os.path.join(config.TEMPLATE_DIR, "default2")
        draft_path = os.path.join(config.DRAFT_DIR, draft_id)
        if os.path.exists(draft_path): shutil.rmtree(draft_path)
        shutil.copytree(template_path, draft_path)
        
        # 在创建草稿时，确保两个文件都存在且内容相同
        draft_info_path = os.path.join(draft_path, "draft_info.json")
        draft_content_path = os.path.join(draft_path, "draft_content.json")
        
        # 加载模板草稿，然后修改配置
        script = draft.ScriptFile.load_template(draft_info_path)
        # 启用双文件兼容模式，这样保存时会自动同步两个文件
        script.dual_file_compatibility = True
        script.width, script.height = width, height
        script.content["canvas_config"]["width"], script.content["canvas_config"]["height"] = width, height
        
        # 保存修改后的草稿（会自动同步到两个文件）
        script.save_path = draft_content_path
        script.save()
        
        # 添加空的主轨道（仅当没有主轨道时添加）
        main_track_name = "main_track"
        script.add_track(track_type=draft.TrackType.video, track_name=main_track_name, relative_index=0)
        logger.info(f"Added empty main track: {main_track_name}")
        
        script.save()
        
    except Exception as e:
        logger.error(f"create draft failed: {e}")
        raise CustomException(CustomError.DRAFT_CREATE_FAILED)

    # 缓存草稿并返回URL
    update_cache(draft_id, script)
    logger.info(f"create draft success: {draft_id}")
    # 对 draft_id 做 URL 编码后再拼入查询参数，确保含中文/特殊字符时 URL 合法
    return config.DRAFT_URL + "?draft_id=" + quote(draft_id, safe="")