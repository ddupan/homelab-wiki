---
title: Hydra 与 OIDC 上游适配器
lifecycle: experimental
evidence: live-verified
last_reviewed: 2026-09-25
last_verified: 2026-09-25
sources:
  - https://git.ddupan.top/panxiao81/iam-login/pulls/2
  - https://git.ddupan.top/panxiao81/iam-login/commit/9cf2d235dff0cd33f98012b0a114f14a8f9bfcda
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/142
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/143
  - 2026-09-25 部署、discovery、重定向与网络隔离检查
  - 维护者于 2026-09-25 确认 Hydra 登录成功返回原 Gitea 账号且仓库权限正常
---

# Hydra 与 OIDC 上游适配器

第一轮人类登录 PoC：Hydra 负责 OIDC 签发，薄的 Login/Consent 服务通过标准 OIDC
验证上游身份。当前配置的上游是 Authelia，它继续连接 Samba AD 并执行人类 MFA。
适配器没有直接连接 LDAP，也不与 Authelia 专有认证协议绑定。

本服务独立于 Ayatori。现役 PoC 代码仍作为 homelab-infra 中的独立 Go module 保存。
下一阶段直接连接 AD 的 Java/Spring 登录服务已建立独立仓库
[iam-login](https://git.ddupan.top/panxiao81/iam-login)，已建立 Spring Native 构建验证基础，人类界面方向见
[浏览器登录设计](../architecture/independent-iam-draft.md#人类浏览器登录界面)，
尚未替换现役 Go/Authelia 链路。应用代码、测试与 Native 构建发布归新仓库，环境部署归
homelab-infra；首轮实现由 [issue #1](https://git.ddupan.top/panxiao81/iam-login/issues/1) 跟踪。
完整的多主体 IAM 仍是[草案](../architecture/independent-iam-draft.md)；
本轮不实现 SPIFFE 登录、agent 专用认证、动态授权或统一组迁移。

## 入口与首次使用

| 入口 | 用途 |
|---|---|
| <https://hydra.ad.ddupan.top> | Hydra 公共 OAuth2/OIDC API |
| <https://hydra-login.ad.ddupan.top> | Login/Consent 适配器，仅处理具体流程路径 |
| <https://git.ddupan.top/user/oauth2/hydra> | 从 Gitea 发起 Hydra 人类登录 |

Hydra 两个域名仅通过 LAN/Tailscale 可达，无公网 tunnel。请从 Gitea 的 `hydra`
登录源进入，在 Authelia 完成既有认证，然后返回 Gitea；旧 `authelia` 登录源保留。
Gitea 继续按原有账号关联、仓库权限与 gitea-admins 组映射执行授权。

```text
Gitea → Hydra → OIDC Login/Consent → Authelia → Samba AD
      ← OIDC ← 已验证的人类身份 ← OIDC callback
```

## 验证范围

2026-09-25 已现场验证：Hydra 数据库迁移成功、两个 Deployment 就绪、ESO SecretSynced、
TLS discovery 的 issuer/endpoints 正确、Flux hydra Kustomization Ready/Healthy；
HTTP 登录链路可从 Hydra 经适配器到达 Authelia 登录页。

无效 login、callback、consent 请求返回 403。Gitea Pod 能访问公共 discovery，不能
直连 Hydra admin Service；公共 HTTPS 入口的 admin API 返回 404。

Gitea 的新增登录源经 PR #143 接入，Helm revision 19 UpgradeSucceeded、Pod Ready；
登录页同时显示 hydra/authelia，从真实 Gitea 入口到达 Authelia 的整段跳转已验证。
**第一轮人类登录 PoC 已通过验收。** 维护者于 2026-09-25 实际使用 Hydra 登录入口后
确认：“已成功返回原账号，仓库权限正常”。这补齐了人类认证后的回调、原账号关联与
仓库权限验收；依据为维护者实际操作反馈，而非 agent 代为输入人类凭据。
`last_verified` 覆盖上述明确列出的检查及维护者登录反馈，不表示机器或 agent 路径已验证。

## 实现与维护

- Hydra 固定 `v26.2.0` 与镜像 digest，使用独立 hydra PostgreSQL database/role。
- 源码 `apps/hydra/login-consent`：标准 OIDC 上游适配器。校验 ID token issuer、audience、
  签名、有效期和 nonce，使用 PKCE S256 与单次、cookie 绑定的 state。
- 当前只允许 Gitea client 和 openid/profile/email/groups；按请求 scope 释放 claims，
  不签发 refresh token，不提供通用自动 consent。主体为上游 issuer/sub 的稳定哈希。
- 单副本短期登录事务保存在内存；重启使正在进行的登录失效，用户重新发起即可。
- Hydra admin 无 HTTPRoute，NetworkPolicy 仅允许适配器访问；维护时通过受控本地
  kubectl port-forward，不对外开放 admin。
- 秘密保存在 OpenBao `kv/k8s/hydra`，ESO 投射给 Hydra/适配器和 Gitea。禁止重建
  system_secret 来处理普通启动问题。
- Authelia 的新 hydra-login client 通过现有 Helm release 的增量 values 更新，保留全部
  已有客户端与 two_factor 策略；Authelia 暂未由 Flux 接管。

源码、构建、claims/client 配置和恢复说明见
[Hydra README](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/hydra/README.md)。
Hydra 部署见 [PR #142](https://git.ddupan.top/panxiao81/homelab-infra/pulls/142)，
Gitea 接入见 [PR #143](https://git.ddupan.top/panxiao81/homelab-infra/pulls/143)。

依赖共享 PostgreSQL、OpenBao/ESO、Authelia、Envoy、Samba DNS 与 zot。独立于 Ayatori
不等于已完成共享基础设施之外的灾备；恢复需保留 Hydra 数据库和秘密。
回退时先撤 Gitea 新登录源，沿用旧 Authelia 入口，不删除用户或原有认证配置。
