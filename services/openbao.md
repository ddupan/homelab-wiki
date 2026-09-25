---
title: OpenBao 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-25
last_verified: null
---

# OpenBao

OpenBao 提供秘密管理与内部 CA，部署在 Kubernetes 之外的独立主机上。
日常使用是以自己的身份登录，按已有 policy 读取秘密或申请短期凭据。

本页依据 homelab-infra 工作区 `infrastructure/openbao/README.md` 整理，
CLI 语法参考下列官方文档。本轮未登录服务、读取秘密或验证现场。

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
| laptop 本地 AI agent | 独立客户端证书，cert auth role 为 `local-agent` |
| SPIFFE workload | 按 [SPIRE 接入说明](spire.md) 与对应 OpenBao role 配置换取 token |

源码记录的本地 agent 证书与私钥由 Ansible 安装在 `/etc/homelab-agent/openbao/`，
不要复制到仓库或 workflow。其 token TTL 为 15 分钟、最长 1 小时；权限包括受限的 SSH 签名、
自身证书续期及 `kv/agents/local/*`，明确不包含 `kv/k8s/*`。
证书注册、登录与续期按源码 README 操作，不能从 SPIFFE 的整体设计推断该路径已迁移。

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

2026-09-25 只读核对：匿名 `/v1/sys/metrics?format=prometheus` 返回 403，仓库服务模板未声明
Prometheus telemetry。中央监控尚未接入 OpenBao 自身指标；ESO store 状态只提供依赖侧间接检测。
维护者要求先安排维护窗口，时间、时区和解封负责人待确认。本轮未修改或重启 OpenBao。

窗口建议预留 30 分钟，执行顺序为：

1. 核对现有 seal 类型、服务配置与 IaC 差异；确定人工解封负责人，密钥只由负责人自行使用。
2. 准备 telemetry 配置差异、仅 sys/metrics 读取权限的采集身份及其续期方式；不为方便采集开放匿名管理指标。
3. 核验最近快照及独立恢复凭据可用，保存可回滚配置；这些检查不能依赖重启后的 OpenBao 才能取到材料。
4. 宣告窗口并为明确受影响告警设置有截止时间的静默；变更、重启、解封由同一窗口协调。
5. 验证 TLS、健康状态、受鉴权 metrics、ESO 同步和现有认证链路，再接入 Prometheus 兼容监控 CR。
6. 异常时恢复原配置；回滚后的重启也可能需要再次解封。清理维护静默，记录验证结果。

以上为待执行步骤，不代表采集身份、快照恢复或 telemetry 已完成验收。
当前 Ansible 写配置会触发 restart；若采用 Shamir，必须预期重启后重新 sealed。
