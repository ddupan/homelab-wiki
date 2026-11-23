---
title: OpenBao 使用指南
lifecycle: active
evidence: live-verified
last_reviewed: 2026-11-23
last_verified: 2026-09-25
sources:
  - homelab-infra infrastructure/openbao/README.md、ansible/roles/openbao_bootstrap/
  - 维护者 2026-11-23 说明：local-agent 证书路径已不存在，机器路径为 ai-agent
watch:
  - homelab-infra:infrastructure/openbao/
  - homelab-infra:platform/spire/README.md
---

# OpenBao

OpenBao 提供秘密管理与内部 CA，部署在 Kubernetes 之外的独立主机上。
日常使用是以自己的身份登录，按已有 policy 读取秘密或申请短期凭据。

CLI 语法参考下列官方文档。

## 人的登录入口

前提是客户端能解析并访问内部域名 `bao.lab.ddupan.top`（仅 LAN/Tailscale），已安装 `bao` CLI，
且账号属于 AD 组 `platform-admins`。

```bash
export BAO_ADDR=https://bao.lab.ddupan.top:8200
bao login -method=oidc -path=oidc-sso -no-print
```

按提示通过浏览器进入 [iam-login](iam-login.md)（`sso.ddupan.top`）登录。人的登录挂载是 `auth/oidc-sso`，
默认 role `admin` 要求 `groups` claim 含 `platform-admins`；挂载与 client 在 homelab-infra
`apps/iam-login/terraform/clients.tf` 声明。原 Authelia 挂载 `auth/oidc` 已随 Authelia 退役。
客户端使用 `bao.lab.ddupan.top`（[f42b1a4](https://git.ddupan.top/panxiao81/homelab-infra/commit/f42b1a4)）；
`bao.ad.ddupan.top` 只为已签发证书中的 AIA/CRL URL 与 ACME 账户长期保留，不作为客户端地址
（`infrastructure/openbao/README.md`）。
使用域名进行 TLS 校验，不用 IP 地址代替，也不关闭证书校验：Let's Encrypt 证书只有 DNS SAN。
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
| 人 | iam-login OIDC，`auth/oidc-sso` |
| laptop 本地开发进程（UID 1000） | SPIFFE `spiffe://ddupan.top/dev/panxiao81`，JWT role 为 `local-development` |
| 集群内 AI agent（namespace `agents`、SA `ai-agent`） | kubernetes auth role `ai-agent`，policy `ai-agent-ssh`：只能签 `ssh-client-signer/sign/ai-agent` 的 SSH 短证书（证书 5 分钟、最长 15 分钟；token 10 分钟） |
| SPIFFE workload | 按 [SPIRE 接入说明](spire.md) 与对应 OpenBao role 配置换取 token |
| Ayatori Dev/Prod 的 manager 与 ESO | kubernetes auth `kubernetes-ayatori-<env>`（k0s SA，登录 JWT 兼作 TokenReview 凭据），见 [Ayatori](ayatori.md) |

**laptop 上的 agent 与开发进程应首先使用这条 SPIFFE 路径**取得 homelab 秘密，只有被拒绝时才请维护者做人类 OIDC 登录
（homelab-infra `CLAUDE.md`、`platform/spire/README.md`）。身份只按 UID 1000 匹配，`sudo` 下不生效。
本机开发 SPIFFE 路径：通过
`/run/spire/agent-sockets/spire-agent.sock` 获取 `aud=openbao` 的 JWT-SVID，
再调用 `auth/jwt-spire/login`、指定 `role=local-development`。
该角色授予 `kv/k8s/*` 与 `kv/infra/*` 的读写及对应 metadata 列表、签发 `ai-agent` SSH 短证书、
查询与撤销自身 token，不允许删除/销毁 KV 数据或管理 auth；token TTL 为 5 分钟（`platform/spire/README.md`）。
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
`infrastructure/openbao/README.md`。服务依赖主机持久存储及 Raft 数据，人的登录还依赖 iam-login 与 Samba AD。
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

2026-09-25 时维护者用 working PC 的 YubiKey 解密加密 unseal share，重启后人工解封。
本次服务配置变更、采集上线与恢复验收已完成，详细操作与证据见
[OpenBao 监控接入维护 runbook](../guides/openbao-monitoring-maintenance.md)。

## 自动解封（TPM pkcs11 seal）

**自 2026-11-05 起 bao1 从 TPM 自动解封**（OpenBao 2.7.2，`pkcs11` KMS 插件经 tpm2-pkcs11；
[PR #603](https://git.ddupan.top/panxiao81/homelab-infra/pulls/603)、[PR #607](https://git.ddupan.top/panxiao81/homelab-infra/pulls/607)；
`group_vars/all/vars.yml` 中 `openbao_pkcs11_seal: true`）。服务、VM 或 laptop 重启不再需要人在场解封。
上述人工解封流程只在 TPM 被更换/清空、或节点仍为 Shamir 时使用（`infrastructure/openbao/unseal.sh`）。

- 原 Shamir key 现在是 **recovery key**，不能再解密任何数据；seal 密钥以 YubiKey 加密的
  `tpm-seal-key.gpg` 托管在仓库，TPM 与该托管同时丢失即丢失数据。
- TPM 更换或新节点的恢复、回滚到 Shamir 的步骤见 `infrastructure/openbao/README.md`「TPM seal」。
