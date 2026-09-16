---
title: LiteLLM 网关使用指南
lifecycle: unknown
evidence: configuration
last_reviewed: 2026-09-16
last_verified: null
---

# LiteLLM gateway

为客户端提供模型 API 代理。维护者于 2026-09-16 表示没有需要补充的动态改动或退役事项；
本页依据 `apps/litellm-gateway/docker-compose.yml` 与 `config.yaml` 整理，不代表已验证运行状态。

## 接入参数

Compose 映射宿主 TCP `4000` 到网关 `4000`，没有在这些文件中记录统一访问域名。
先由维护者提供实际 base URL、客户端认证要求及可用模型；不能把宿主端口自动当成公网入口。
网关客户端的认证与网关访问上游模型的认证是两层配置，不能把服务端认证文件交给消费者。

配置中的模型别名包括 `chatgpt/gpt-5.4` 和 `hf/google/embeddinggemma-300m` 等，
分别面向聊天和 embedding；这里只表示路由声明，不保证上游账号有权限或模型当下可用。
完整别名以 `config.yaml` 为准。不要因名字含有 codex，就把这个网关与已退役的 codex-proxy 混为一体。

## 第一次聊天请求

在已获授权的客户端环境中，将 `LITELLM_BASE_URL` 设置为维护者提供的 API 根地址，
`LITELLM_MODEL` 设置为获准使用的聊天模型别名。
如果该入口要求 Bearer key，通过既有秘密注入方式提供 `LITELLM_API_KEY`；是否需要 key 以实际接入约定为准。
下面使用 Python 标准库，token 不放在命令行中；请求会调用上游模型并消耗对应配额。

```python
import json
import os
import urllib.request

base = os.environ["LITELLM_BASE_URL"].rstrip("/")
headers = {"Content-Type": "application/json"}
key = os.environ.get("LITELLM_API_KEY")
if key:
    headers["Authorization"] = "Bearer " + key
payload = {
    "model": os.environ["LITELLM_MODEL"],
    "messages": [{"role": "user", "content": "Reply with OK."}],
}
request = urllib.request.Request(
    base + "/chat/completions",
    data=json.dumps(payload).encode(),
    headers=headers,
    method="POST",
)
with urllib.request.urlopen(request, timeout=60) as response:
    result = json.load(response)
print(result["choices"][0]["message"]["content"])
```

预期收到模型回复。接口结构参考 [LiteLLM 客户端文档](https://docs.litellm.ai/docs/proxy/user_keys)，
本轮没有执行请求。该示例面向聊天模型，不能直接拿 embedding 模型替换。

## 依赖与排障

这套 Compose 包含独立的 PostgreSQL 16 和 Prometheus，数据库卷为 `postgres_data`，
指标卷为 `prometheus_data`；这里的数据库不是[集群共享 PostgreSQL](shared-postgresql.md)。
Compose 还挂载配置文件及宿主 `auth.json`，后者属于上游认证材料，不进入 wiki、日志或 AI 上下文。
镜像配置使用 `dev` 标签，接入行为需与实际部署版本相符，不能仅凭最新上游文档认定功能已启用。

连接失败先核对宿主与端口；401/403 需区分网关认证和上游认证；模型错误先核对别名及上游权限；
超时或限额错误再检查上游响应。不要通过打印认证文件或完整带鉴权请求排障。
部署来源为 homelab-infra `apps/litellm-gateway/`；消费者清单与备份情况未在所读文件中记录。
