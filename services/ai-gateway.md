---
title: AI gateway（ai.lab.ddupan.top）
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/ai-gateway/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/828aafe5e2f3b2e3ac11caa0c55e0f6a2c23f940
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/85c9b920780f82ce8fa45efcbcd5999333b14295
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/e825e6a0864fea6a941fd1062816ae9266a03794
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/d0c6074b919e671c834c7b2951332aed801e72fc
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/b8f8e1f71d0e9640626699e6dd8c838a4fc3afeb
watch:
  - homelab-infra:apps/ai-gateway/
  - homelab-infra:platform/envoy-gateway/agent-router.yaml
---

# AI gateway

## 它解决什么问题

`https://ai.lab.ddupan.top` 是 LLM 的统一入口：每个客户端拿自己的 gateway key，
上游凭据不离开集群，撤销一个客户端不需要轮换上游凭据。按模型名分流：

| 模型 | 后端 | 计费 |
|---|---|---|
| `gpt-*`、`o<n>*`、`codex-*` | CLIProxyAPI | ChatGPT Plus 订阅 |
| 其他（Claude） | Anthropic API | Console 赠金 |

它取代了 2026-11-03 退役的 [litellm-gateway](litellm-gateway.md)
（[b8f8e1f](https://git.ddupan.top/panxiao81/homelab-infra/commit/b8f8e1f71d0e9640626699e6dd8c838a4fc3afeb)）。

## 从哪里使用

- 入口：挂在 LAN 入口 `eg` 的 `https-lab` listener 上（`apps/ai-gateway/httproute.yaml`），需要能到达 LAN。
- 登录：请求带 gateway key（`x-api-key` 或 `Authorization: Bearer`）；它**不是** Anthropic key。
- 申请 key：在 `https://ai-keys.lab.ddupan.top` 签发与撤销，需要 iam-login 登录且属于 `platform-admins`。
  key 只显示一次。
- 路径：Claude 只能走 `/anthropic`；OpenAI 兼容的 `/v1` **只服务 GPT 模型**（Agent Router 不能把
  OpenAI 风格请求翻译成 Anthropic 原生 API）。`/anthropic` 也可请求 GPT 模型。

## 第一次使用

让 Claude Code 或 Anthropic SDK 经网关调用：

```bash
export ANTHROPIC_BASE_URL=https://ai.lab.ddupan.top/anthropic
export ANTHROPIC_API_KEY=<你的 gateway key>
```

OpenAI 兼容客户端把 base URL 设为 `https://ai.lab.ddupan.top/v1`、API key 设为 gateway key，只用 GPT 模型。

## 日常操作与限制

- 网关不做限流。Anthropic 花费上限在 Console 设置；ChatGPT 侧受 Plus 套餐自身额度限制。
- key 管理界面显示创建者、创建时间、最后使用时间和 30 天请求/token 统计。撤销即删除 Bao 中的 key。
- 上游看到的客户端标识是请求头 `x-ai-client: <id>`。

## 出问题时

- `/v1/models` 不列出任何 `gpt-*`：ChatGPT 登录失效，需在 CLIProxyAPI 里重新做 device-code 登录
  （命令见源码 README「ChatGPT login」；须在 PTY 下运行，否则看不到验证码）。新凭据无需重启即生效。
- Claude 请求 401：先查 Anthropic Console 的 authentication history。签名错误通常是外部访问不到
  `https://spire-oidc.ddupan.top/keys`，Anthropic 看不到 SPIRE 轮换后的公钥。
- 需要立即刷新 Anthropic token：`kubectl --context default -n ai-gateway create job --from=cronjob/anthropic-wif wif-manual`。

## 运维入口

- 源码：[apps/ai-gateway/](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/ai-gateway)，Flux 部署。
  控制面是 Agent Router（原 Envoy AI Gateway，`platform/envoy-gateway/agent-router.yaml`）；独立 Gateway `ai`
  与 LAN 入口 `eg` 分开，避免 Agent Router 的 fail-closed webhook 阻塞 `eg` 的滚动更新。
- Anthropic 凭据：没有 `sk-ant-` key。CronJob `anthropic-wif` 每 15 分钟用 [SPIRE](spire.md) JWT-SVID
  经 Workload Identity Federation 换 1 小时 access token（`anthropic-wif.yaml`）。
- ChatGPT 凭据：Codex OAuth 凭据在 PVC `cliproxyapi-auth`，不在 Bao（CLIProxyAPI 会自行刷新改写）。
- Gateway key：每个 key 一条 Bao `kv/k8s/ai-gateway-keys/<id>`，[ESO](external-secrets.md) 只投射
  `status=active` 的 key。key UI 代码在 `panxiao81/ai-gateway-keys` 仓库；审计见 VictoriaLogs
  （`"audit":"key.create|key.revoke"`）与 Bao 审计日志。
- 其他秘密：`kv/k8s/ai-gateway`、`kv/k8s/ai-gateway-keys-sso`、`kv/k8s/ai-gateway-keys-session`（用途见源码 README）。
- 备份恢复：尚未建立。key 在 Bao，ChatGPT 凭据丢失只需重新登录。

## 当前状态与证据

- 演进：Agent Router 前置 Anthropic
  （[828aafe](https://git.ddupan.top/panxiao81/homelab-infra/commit/828aafe5e2f3b2e3ac11caa0c55e0f6a2c23f940)）、
  CLIProxyAPI 分流（[85c9b92](https://git.ddupan.top/panxiao81/homelab-infra/commit/85c9b920780f82ce8fa45efcbcd5999333b14295)）、
  WIF（[e825e6a](https://git.ddupan.top/panxiao81/homelab-infra/commit/e825e6a0864fea6a941fd1062816ae9266a03794)）、
  key 管理界面（[d0c6074](https://git.ddupan.top/panxiao81/homelab-infra/commit/d0c6074b919e671c834c7b2951332aed801e72fc)）。
