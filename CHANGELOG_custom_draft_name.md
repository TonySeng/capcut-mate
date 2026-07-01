# 自定义草稿名称功能 - 更新日志

## 版本信息
- **功能分支**: `feat/custom-draft-name`
- **提交日期**: 2026-07-01
- **GitHub**: https://github.com/TonySeng/capcut-mate/tree/feat/custom-draft-name

---

## 📋 功能概述

本次更新为 `create_draft` 接口新增了**自定义草稿名称**功能，并修复了中文/特殊字符草稿的下载问题。

---

## ✨ 新增功能

### 1. 自定义草稿名称
- **新增参数**: `draft_name`（可选）
- **命名格式**: `{自定义名称}_{时间戳}`
- **唯一性保证**: 时间戳后缀确保不重复
- **字符处理**:
  - 自动清理文件系统不安全字符：`\ / : * ? " < > |`
  - 空白字符（空格、制表符）转为下划线
  - 保留中文、emoji 等多语言字符
- **长度限制**: 自定义部分最多 50 字符
- **兜底机制**: 空名称使用 `draft` 作为默认值
- **向后兼容**: 不提供时保持原有自动生成行为（`{时间戳}{UUID}`）

### 2. 使用示例

```bash
# 使用自定义名称
curl -X POST http://localhost:30000/openapi/capcut-mate/v1/create_draft \
  -H "Content-Type: application/json" \
  -d '{
    "width": 1920,
    "height": 1080,
    "draft_name": "我的视频项目"
  }'

# 返回示例
{
  "code": 0,
  "message": "成功",
  "draft_url": "http://127.0.0.1/openapi/capcut-mate/v1/get_draft?draft_id=%E6%88%91%E7%9A%84%E8%A7%86%E9%A2%91%E9%A1%B9%E7%9B%AE_20260701005526",
  "tip_url": "https://docs.jcaigc.cn"
}
```

---

## 🐛 问题修复

### 1. 下载 URL 编码问题（根本原因）
**问题描述**:
- `get_draft` 返回的下载 URL 未做 percent-encode
- 中文/特殊字符草稿文件通过 nginx 下载时 404
- 表现为"草稿没生成"或"剪映无法打开"

**修复方案**:
- `src/service/get_draft.py`: 使用 `urllib.parse.quote(path, safe="/")` 对路径编码
- 修复后 URL 示例: `http://127.0.0.1/output/draft/%E6%88%91%E7%9A%84%E9%A1%B9%E7%9B%AE_20260701005526/draft_content.json`

**影响范围**:
- ✅ 新建中文草稿：创建、获取、下载全链路正常
- ✅ 已有中文草稿：修复前生成的草稿现在也能正常下载
- ✅ 无回归：纯英文草稿不受影响

### 2. draft_id 参数校验过严
**问题描述**:
- `get_draft` Schema 要求 `draft_id` 最小 20 字符
- 短名称草稿（如 `测试草稿_20260701005349` = 19 字符）被拒绝
- 返回错误: `String should have at least 20 characters`

**修复方案**:
- `src/schemas/get_draft.py`: 放宽为 `min_length=1, max_length=100`
- 原限制基于旧格式 `{时间戳14位}{UUID8位}` = 22 字符
- 新格式支持任意长度的自定义名称

### 3. create_draft 返回 URL 编码不完整
**问题描述**:
- 返回的 `draft_url` 查询参数中 `draft_id` 未编码
- 中文字符以裸字符形式出现在 URL 中

**修复方案**:
- `src/service/create_draft.py`: 使用 `quote(draft_id, safe="")` 对查询参数编码
- 后续接口使用 `parse_qs` 会自动解码，全链路编解码一致

---

## 📦 修改的文件

### 核心代码（5 个文件）
1. **src/schemas/create_draft.py**
   - 新增 `draft_name: Optional[str]` 参数
   - 添加参数说明和示例

2. **src/service/create_draft.py**
   - 新增 `_sanitize_draft_name()` 函数：清理不安全字符
   - 更新 `create_draft()` 函数：支持自定义名称逻辑
   - 返回 URL 对 `draft_id` 做 percent-encode
   - 导入 `urllib.parse.quote`

3. **src/service/get_draft.py**
   - `gen_download_url()` 对文件路径做 URL 编码
   - 导入 `urllib.parse.quote`
   - 添加详细注释说明编码原因

4. **src/schemas/get_draft.py**
   - `draft_id` 长度限制：`min_length=20, max_length=32` → `min_length=1, max_length=100`
   - 添加注释说明修改原因

5. **src/router/v1.py**
   - 传递 `draft_name` 参数到 `create_draft()` 函数

### 文档（3 个文件）
1. **docs/create_draft.zh.md**（中文）
   - 新增 `draft_name` 参数说明
   - 新增使用示例（4个场景）
   - 更新注意事项

2. **docs/create_draft.md**（英文）
   - 新增 `draft_name` 参数说明
   - 新增使用示例（4个场景）
   - 更新注意事项

3. **docs/自定义草稿名称功能说明.md**（新增）
   - 完整的功能说明文档
   - 包含应用场景、实现细节、版本历史

---

## ✅ 验证测试

### 测试场景
| 场景 | 输入 | 输出 | 状态 |
|------|------|------|------|
| 自定义英文名 | `draft_name: "test-project"` | `test-project_20260630135049` | ✅ 通过 |
| 自定义中文名 | `draft_name: "2026年中文测试"` | `2026年中文测试_20260630153533` | ✅ 通过 |
| 短中文名 | `draft_name: "短名"` | `短名_20260701005526` | ✅ 通过 |
| 特殊字符清理 | `draft_name: "project:2024/test*video?"` | `project_2024_test_video__20260630135105` | ✅ 通过 |
| 不提供名称 | 无 `draft_name` | `202606301350584990c473` | ✅ 通过 |
| 中文草稿下载 | 下载 `短名_20260701005526/draft_content.json` | HTTP 200, 4325 字节 | ✅ 通过 |
| 旧中文草稿下载 | 下载 `2026年_20260630151503/draft_content.json` | HTTP 200, 86893 字节 | ✅ 通过 |
| 英文草稿回归 | 下载 `test-project_20260630135049/draft_content.json` | HTTP 200, 4325 字节 | ✅ 通过 |

### 端到端流程
```bash
创建中文草稿 → 获取文件列表 → 下载文件
✅ 全链路通过（code=0, HTTP 200）
```

---

## 🔧 技术细节

### URL 编码处理
- **编码时机**: 
  - `create_draft` 返回时：对 `draft_id` 编码后拼入 `draft_url`
  - `get_draft` 返回时：对文件路径编码后生成下载 URL
- **编码方式**: `urllib.parse.quote(string, safe="/")`
  - 保留斜杠 `/` 作为路径分隔符
  - 中文字符转为 percent-encoding（如 `年` → `%E5%B9%B4`）
- **解码处理**: 后续接口使用 `urlparse` + `parse_qs` 自动解码

### 字符清理规则
```python
# 正则替换不安全字符
sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
# 空白字符转下划线
sanitized = re.sub(r'\s+', '_', sanitized)
# 去除首尾空格和点号
sanitized = sanitized.strip(' .')
# 长度限制
return sanitized[:50]
```

### 兼容性说明
- **向后兼容**: 不提供 `draft_name` 时行为完全不变
- **已有草稿**: 修复前生成的中文草稿现在也能正常下载
- **URL 解码**: 所有接口统一使用 `parse_qs`，自动处理 percent-encoding

---

## 🚀 部署说明

### Docker 部署（已验证）
```bash
# 使用卷挂载方式（开发推荐）
docker-compose -f docker-compose.local.yaml up -d

# 或使用本地构建镜像
docker build -f Dockerfile.local -t capcut-mate:local .
docker-compose -f docker-compose.local-build.yaml up -d
```

### 验证部署
```bash
# 创建中文草稿测试
curl -X POST http://localhost:30000/openapi/capcut-mate/v1/create_draft \
  -H "Content-Type: application/json" \
  -d '{"width": 1920, "height": 1080, "draft_name": "测试"}'

# 预期返回 code=0，draft_url 包含编码后的中文
```

---

## 📊 提交历史

### Commit 1: 核心功能代码
```
feat: 新增自定义草稿名称功能及中文路径下载修复

文件：
- src/schemas/create_draft.py
- src/schemas/get_draft.py
- src/service/create_draft.py
- src/service/get_draft.py
- src/router/v1.py

提交哈希: 72eb1ec
```

### Commit 2: 文档更新
```
docs: 更新 create_draft 文档，新增自定义草稿名称功能说明

文件：
- docs/create_draft.zh.md
- docs/create_draft.md
- docs/自定义草稿名称功能说明.md

提交哈希: 87368a6
```

---

## 📝 后续建议

### 可选优化
1. **测试覆盖**
   - 添加单元测试覆盖 `_sanitize_draft_name()`
   - 添加集成测试覆盖中文草稿全流程

2. **日志增强**
   - 记录字符清理前后的对比（便于调试）
   - 记录 URL 编码前后的对比

3. **文档完善**
   - 在主 README 中添加自定义草稿名称的快速示例
   - 添加常见问题 FAQ（如为什么要限制 50 字符）

### 已知限制
1. **长度限制**: 自定义名称最多 50 字符（考虑文件系统路径长度限制）
2. **字符限制**: 自动清理不安全字符，无法保留原始特殊符号
3. **唯一性**: 仅通过时间戳保证唯一性（秒级，同一秒创建多个草稿时可能冲突）

---

## 👥 贡献者
- **开发**: Claude Opus 4.8 (1M context)
- **测试**: qianshengTao
- **仓库**: https://github.com/TonySeng/capcut-mate

---

**更新时间**: 2026-07-01  
**文档版本**: v1.0