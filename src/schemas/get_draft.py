from pydantic import BaseModel, Field
from typing import List


class GetDraftRequest(BaseModel):
    """获取草稿请求参数"""
    # 放宽长度限制：支持自定义草稿名后，短名称+时间戳可能不足原来的 min_length=20
    # 只要草稿 ID 非空且不超过文件系统路径限制即可（Windows 单段限制 255，此处保守取 100）
    draft_id: str = Field(..., min_length=1, max_length=100, description="草稿ID")


class GetDraftResponse(BaseModel):
    """获取草稿响应参数"""
    files: List[str] = Field(default=[], description="文件列表")
