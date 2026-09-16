---
title: OpenViking 导入与查询指南
lifecycle: unknown
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# OpenViking

OpenViking 为文档和 agent 上下文提供导入与检索能力。
本页依据 homelab-infra `apps/openviking/README.md`、Compose 和上游接口文档整理，未访问实例。
仓库提供部署方案，未据此断言服务已上线或 wiki 已自动同步到索引。

## 入口与数据位置

| 用途 | Compose 默认值 |
|---|---|
| HTTP API | 宿主端口 `1933` |
| Console/UI | 宿主端口 `8020` |
| embedding endpoint | 宿主回环地址 `127.0.0.1:8081` |
| 持久数据与配置 | `./data` |
| embedding 模型缓存 | `./models` |

这些端口可被环境配置覆盖，实际宿主地址、客户端 key 与权限由维护者提供。
服务端 VLM 使用 `openai-codex` provider，本地 embedding 服务使用 llama.cpp CUDA 镜像；
客户端 API key 与服务端模型认证不是同一份凭据，不将服务端 OAuth 数据交给检索客户端。
当前镜像标签为 `latest`，接口需与实际部署版本核对。

## 导入、等待、查询与读取

先设置 `OPENVIKING_BASE_URL` 为已授权的 API 根地址；入口需要 key 时，通过既有秘密注入方式
提供 `OPENVIKING_API_KEY`。以下 Python 标准库片段共用同一会话；只处理一份公开上游 README，
会写入索引并触发模型处理。本轮没有执行导入或请求。

```python
import json
import os
import urllib.parse
import urllib.request

base = os.environ["OPENVIKING_BASE_URL"].rstrip("/")
headers = {"Content-Type": "application/json"}
if os.environ.get("OPENVIKING_API_KEY"):
    headers["X-API-Key"] = os.environ["OPENVIKING_API_KEY"]

def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(base + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)

result = request("/api/v1/resources", {
    "path": "https://raw.githubusercontent.com/volcengine/OpenViking/refs/heads/main/README.md"
})
print(json.dumps(result, ensure_ascii=False, indent=2))
```

从返回数据取得 `task_id` 与资源 URI。`accepted` 只表示已接收，随后用同一会话查询任务：

```python
task_id = "REPLACE_WITH_RETURNED_TASK_ID"
print(request("/api/v1/tasks/" + urllib.parse.quote(task_id, safe="")))
```

任务到达 `completed` 后再搜索；`failed` 或 `cancelled` 应先处理原因，不能当作入库成功。
避免因请求超时直接反复导入同一来源。参见上游
[资源 API](https://github.com/volcengine/OpenViking/blob/main/docs/en/api/02-resources.md) 和
[任务 API](https://github.com/volcengine/OpenViking/blob/main/docs/zh/api/17-tasks.md)。

```python
print(request("/api/v1/search/find", {
    "query": "What is OpenViking?", "limit": 5
}))
```

从搜索结果中选择一个文件 URI，读取正文：

```python
uri = "REPLACE_WITH_RETURNED_FILE_URI"
query = urllib.parse.urlencode({"uri": uri})
print(request("/api/v1/content/read?" + query))
```

检索和读取方式见[上游检索文档](https://github.com/volcengine/OpenViking/blob/main/docs/en/api/06-retrieval.md)。
返回目录时先查看其概览或子项再选文件，不把任意目录 URI 当正文文件使用。
HTTP 成功之外，还要检查各次响应中的应用状态与错误信息；响应封装以部署版本为准。

## 人与 AI 如何使用检索结果

检索结果用于定位资料，最终结论回到原始 Markdown、源码 README 或 ticket 核对日期与证据。
本 wiki 的 Git 仓库仍是正式文档来源；索引不是自动获得权威性的另一份状态记录。
尚未建立本库自动导入、增量更新或删除同步的已验证流程，不能把旧索引结果当作当前事实。

导入前明确资料范围及模型处理边界。不要将凭据、Terraform state 或含秘密的整个工作目录批量导入。
本地 embedding 不意味着所有语义处理都在本地完成，VLM 仍使用 README 所述的上游认证路径。

连接失败核对宿主端口；导入失败区分来源可达性与解析；任务卡住或结果缺失再查看 VLM、embedding
与队列处理。数据在 `./data`，模型缓存可重新下载，两者不能按同一种可丢弃缓存处理。
部署、模型初始化与认证维护回到 `apps/openviking/README.md`。
