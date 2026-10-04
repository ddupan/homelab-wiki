---
title: OpenBao 使用指南
lifecycle: active
evidence: live-verified
last_reviewed: 2026-09-25
last_verified: 2026-09-25
---

# OpenBao

OpenBao 提供秘密管理与内部 CA，部署在 Kubernetes 之外的独立主机上。
日常使用是以自己的身份登录，按已有 policy 读取秘密或申请短期凭据。

本页依据 homelab-infra 工作区 `infrastructure/openbao/README.md` 整理，
CLI 语法参考下列官方文档。登录和取密指南仍以文档为据；2026-09-25 已现场验证
服务解封、中央指标、ESO 秘密刷新及本地快照监控，范围见本文末节。

## 人的登录入口

前提是客户端能解析并访问内部域名，已安装 `bao` CLI，且账号具备相应 OIDC 授权。

```bash
export BAO_ADDR=https://bao.ad.ddupan.top:8200
bao login -method=oidc -no-print
```

按提示通过浏览器进入 Authelia，完成登录和二次认证。
使用域名进行 TLS 校验，不用 IP 地址代替，也不关闭证书校验。
`-no-print` 避免显示 token，但成功登录后仍会把它存入本机 token helper，供后续命令使用。
因此应在自己的受控会话中登录。参见 [OpenBao login](https://openbao.org/docs/commands/login/)。

登录成功后，只查看当前会话的权限与有效期：

```bash
bao token lookup -field=policies
bao token lookup -field=ttl
```

这两个命令不打印完整 token；字段选项见
[token lookup](https://openbao.org/docs/commands/token/lookup/)。能登录不代表能读取任意秘密。

## 按授权路径读取一个字段

先由服务所有者提供准确的 mount、秘密路径和字段名。
下例 `YOUR_AUTHORIZED_PATH` 是占位符，须替换为 `kv` mount 下已授权且存在的路径；
`password` 也应替换为实际字段名。命令仅适合已获相应权限的会话。

```bash
set +x
APP_PASSWORD="$(bao kv get -mount=kv -field=password YOUR_AUTHORIZED_PATH)"
# 在当前会话中交给实际消费者；不要 echo，也不要放入命令行参数或日志。
unset APP_PASSWORD
```

示例只演示接收字段后清除变量，不会配置任何应用；接入脚本还应检查命令失败并停止后续操作。
`kv get` 会处理 KV 引擎的 API 路径，CLI 的相对路径无需自行插入 `data/`。
参见 [OpenBao kv get](https://openbao.org/docs/commands/kv/get/)。

Kubernetes 应用通常消费 ESO 投射的 Secret。修改秘密应通过其受管来源及对应服务的轮换流程，
不能只编辑 ESO 生成的副本。不要把完整秘密内容粘贴到 AI 上下文、issue 或 wiki。

## 机器身份的使用边界

| 调用者 | 本库已记录的认证路径 |
|---|---|
| 人 | Authelia OIDC 登录 |
| laptop 本地开发进程（UID 1000） | SPIFFE `spiffe://ddupan.top/dev/panxiao81`，JWT role 为 `local-development` |
| 本地 agent 旧证书路径 | 独立客户端证书，cert auth role 为 `local-agent` |
| SPIFFE workload | 按 [SPIRE 接入说明](spire.md) 与对应 OpenBao role 配置换取 token |
| Ayatori Dev/Prod 的 manager 与 ESO | kubernetes auth `kubernetes-ayatori-<env>`（k0s SA，登录 JWT 兼作 TokenReview 凭据），见 [Ayatori](ayatori.md) |

源码记录的本地 agent 证书与私钥由 Ansible 安装在 `/etc/homelab-agent/openbao/`，
不要复制到仓库或 workflow。其 token TTL 为 15 分钟、最长 1 小时；权限包括受限的 SSH 签名、
自身证书续期及 `kv/agents/local/*`，明确不包含 `kv/k8s/*`。
证书注册、登录与续期按源码 README 操作，不能从 SPIFFE 的整体设计推断该路径已迁移。

本机开发 SPIFFE 路径与上述旧证书路径不同：通过
`/run/spire/agent-sockets/spire-agent.sock` 获取 `aud=openbao` 的 JWT-SVID，
再调用 `auth/jwt-spire/login`、指定 `role=local-development`。
该角色授予 `kv/data/k8s/*` 与 `kv/data/infra/*` 的 create/read/update，token TTL 为 5 分钟。
2026-09-25 已实际用该身份读取 Backstage 数据库密码并完成[数据库接入](backstage.md)，
无须更改策略或改用人类 OIDC。token/JWT 仅在进程内存中传递，不输出或写入文档。
依据为 homelab-infra `platform/spire/README.md`、
`infrastructure/openbao/terraform/auth-spire.tf` 与 `policies/local-development.hcl`。
现有 CLI 会话返回 403 时，应先核对身份和有效期；不能据此判断 SPIFFE 缺少 KV 权限。

SPIFFE 验证机器身份，OpenBao 自己签发 token 并维护 policy。
Dynamic Runner 提供执行环境和 workload 身份，具体向 OpenBao 请求什么 token 由 workflow 决定。

## 权限申请与故障入口

申请权限时提供调用者身份、准确路径、所需动作、有效期及用途，由维护者调整受管 role/policy。
遇到拒绝访问先核对上述信息及会话有效期，不用管理员 token 代替应用身份。
连接失败时先区分内部 DNS、网络、TLS 与认证问题；OIDC 回调问题需结合客户端浏览器所在位置排查。

部署、PKI、SSH 签名、本地 agent 身份和恢复细节见 homelab-infra
`infrastructure/openbao/README.md`。服务依赖主机持久存储及 Raft 数据，人的登录还依赖 Authelia。
根密钥与恢复身份不应依赖 Kubernetes 或只能由 OpenBao 自身解密的秘密；
日常登录成功不等于已完成备份或灾难恢复验收。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#openbao)。

## 监控接入与维护窗口

2026-09-25 已启用受鉴权 Prometheus telemetry，ServiceMonitor 通过现有 vmagent 采集，
job 为 `openbao`。同 Pod 的 Bao Agent 使用 Kubernetes SA 登录 metrics role，自动续期，
token 仅保存于内存卷；指标身份不能读取业务秘密，匿名 metrics 仍被拒绝。
已有目标 down/消失持续 3 分钟的 critical 告警，通知沿用 Telegram。
内部健康规则另检查当前单节点的 active、unsealed、Raft autopilot node healthy，
并单独告警健康 gauge 缺失。以后改为多节点时必须调整 active 判定；尚未覆盖全部 Raft 或 PKI 风险。

维护中已修复快照 token 失效及脚本缺少续期的问题，生成新快照并核对 VM 外副本。
快照 timer 已启用；独立的 VM node_exporter 通过 textfile 上报最近结果、完成时间和最后成功时间，
不依赖 Bao 解封或 API token。快照失败持续 5 分钟为 warning，超过 36 小时无成功快照
或无成功记录持续 15 分钟为 critical；采集失联/损坏也有专用告警。
标准主机指标复用现有主机规则。异地副本与恢复演练仍需独立验收。

维护者用 working PC 的 YubiKey 解密 VM 上保存的加密 unseal share，重启后人工解封。
本次服务配置变更、采集上线与恢复验收已完成，详细操作与证据见
[OpenBao 监控接入维护 runbook](../guides/openbao-monitoring-maintenance.md)。
后续重启仍需同样的人在场解封流程；不能因本次恢复成功假定已经自动解封。
