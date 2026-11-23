---
title: LiteLLM 网关（已退役）
lifecycle: retired
evidence: configuration
last_reviewed: 2026-11-18
last_verified: null
---

# LiteLLM gateway（已退役）

**已于 2026-11-03 退役**（[b8f8e1f](https://git.ddupan.top/panxiao81/homelab-infra/commit/b8f8e1f)）。
不要再按本页接入；`apps/litellm-gateway/` 已从 homelab-infra main 删除。

## 退役原因

据退役 commit 说明：laptop 上的这套 LiteLLM 代理（ChatGPT 订阅 + HF embedding，宿主端口 `:4000`）
自 2026-07-10 起未再运行（数据库最后写入当日），容器已不存在；仓库内没有使用者
（research-auto 直接使用 litellm 库）；`4000` 端口现由 blocky 占用。
该 commit 同时删除了 compose 目录、Renovate 中为其 PostgreSQL 加的规则，并从监控覆盖清单去掉 LiteLLM。

## 现在用什么

需要模型 API 时使用 [AI gateway](ai-gateway.md)（homelab-infra `apps/ai-gateway/`，`https://ai.lab.ddupan.top`）：统一入口、按客户端发放 key，
`gpt-*`/`codex-*` 等模型经 CLIProxyAPI 走 ChatGPT 订阅，其余走 Anthropic API。
用法与 key 申请见该目录 README。退役 commit 未把它写成本服务的直接替代，这里只说明当前的模型 API 入口。

## 历史

本服务曾是 `apps/litellm-gateway/` 下的 Docker Compose：网关映射宿主 TCP `4000`，附带独立的 PostgreSQL 16
（卷 `postgres_data`，不是[共享 PostgreSQL](shared-postgresql.md)）与 Prometheus（卷 `prometheus_data`），
挂载配置文件和宿主 `auth.json`（上游认证材料）。模型别名包括 `chatgpt/gpt-5.4` 和
`hf/google/embeddinggemma-300m` 等。它与已退役的 codex-proxy 不是同一服务。

退役 commit 记录 `.gitignore` 中的 `auth.json` 条目暂留，直到本地凭据文件删除；该文件含上游凭据，
不进入 wiki、日志或 AI 上下文。
