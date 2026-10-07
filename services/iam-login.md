---
title: iam-login（sso.ddupan.top）
lifecycle: experimental
evidence: live-verified
last_reviewed: 2026-10-07
last_verified: 2026-10-07
sources:
  - https://git.ddupan.top/panxiao81/iam-login/pulls/16
  - https://git.ddupan.top/panxiao81/iam-login/pulls/17
  - https://git.ddupan.top/panxiao81/iam-login/pulls/18
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/193
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/228
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/235
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/237
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/240
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/241
  - 维护者于 2026-10-04 在 sso.ddupan.top 注册 passkey、登录 /console，并经 Gitea `sso` 登录源返回原账号
  - https://git.ddupan.top/panxiao81/iam-login/pulls/22
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/275
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/277
  - https://git.ddupan.top/panxiao81/terraform-provider-homelab
  - 维护者于 2026-10-07 确认 Pod 重启后会话保留；Terraform CD plan 以 terraform-plan 身份纳管 gitea（1 import / 0 change）
---

# iam-login（sso.ddupan.top）

独立 IAM 的人类登录与 OIDC 签发：AD 密码 + Passkey，进程内 Spring Security 授权服务器，
取代 Hydra。issuer `https://sso.ddupan.top` 为长期 issuer。Authelia（`auth.ddupan.top`）在其他
应用迁走前继续运行。设计与选型见 [独立 IAM 草案](../architecture/independent-iam-draft.md)。

## 从哪里使用

| 入口 | 用途 |
|---|---|
| `https://sso.ddupan.top/console` | OIDC 客户端管理（要求直接属于 `Domain Admins`） |
| `https://sso.ddupan.top/.well-known/openid-configuration` | discovery |
| `https://git.ddupan.top/user/oauth2/sso` | Gitea 经本服务登录 |

- 公网经 Cloudflare tunnel；LAN 与 Pod 经 split horizon 到 Envoy `https-sso`，RP 换 token 不经 WAN。
- 新接入应用：在 `/console` 登记客户端（secret 只显示一次，存 OpenBao），按应用能力决定是否关闭
  PKCE（只为做不到的应用关闭，如 Gitea 1.27）。下游按 `groups` claim 与 `aud` 授权，scope 不代表权限。

## 运行形态

- homelab-infra `apps/iam-login`：Native 镜像单副本（session 在内存，重启后需重新登录）。
- 数据库经 Ayatori 申请（`clusters/ayatori-prod/iam-login.yaml`，pg-prod `iam_login`）；本 namespace 以
  专用 SA 与 bao role `iam-login-database` 只读这一份凭据。
- `kv/k8s/iam-login`：签名私钥（不可随部署重生成）与 LDAPS truststore。
- Gitea 登录源 ID 3 `sso`（原名 `hydra`）；iam-login 以 subject 绑定沿用旧 `sub`，账号关联不变。

## 会话与客户端 IaC

- 会话存数据库（Spring Session JDBC，属性为 JSON），部署与重启不登出（2026-10-07 实测）；WebAuthn challenge
  存 `webauthn_challenge` 表，消费是一条 `DELETE ... RETURNING`。
- OIDC 客户端由 homelab-infra `apps/iam-login/terraform` 管理（Terraform CD），provider 为自研
  `terraform.lab.ddupan.top/ddupan/homelab`（静态 registry 在 SeaweedFS，release 由维护者 YubiKey 子钥
  `8A887573EFE9762D` 签名，CI 只上传构建）。provider 以调用方 JWT-SVID 认证，allowlist 为 CD 的
  plan/apply job 与笔记本开发身份；`/console` 的改动会表现为 drift。
- `gitea` 以 import 纳管，secret 仍是人工写入 `kv/k8s/gitea-sso` 的值；交给 Terraform 轮换需同时写 kv 并重启 Gitea。

## 发布

iam-login main 的 CI（runner：pve1 LXC 104，标签 `iam-build`）在 Native 浏览器测试通过后，把同一个
二进制打包推到 zot `iam/iam-login:<commit>`，身份为 runner 上 join_token SPIRE Agent 发的
`spiffe://ddupan.top/ci/panxiao81/iam-login/publish`。部署 = homelab-infra PR 修改 digest。
join_token Agent 不能重新证明：LXC 停机超过 SVID 有效期（约 1 小时）需重新发 token 并更新条目 parentID，
见 homelab-infra `platform/spire/external-agent/README.md`。

## 已知限制与教训（2026-10-04）

- Native 反射缺口只在真实数据形态出现：3 个以上组时 `List.of` 为 `ListN`，需要 `GroupMembership[]`
  的反射注册；夹具已改为 3 个组。
- 首次 passkey 注册只需近期 AD 密码，入口在公网：每个账号上线后应尽快注册。
- Gitea chart 的 init container 按**名称**匹配登录源，改名必须先在 Gitea 原地改；values ConfigMap
  的 watch 标记必须是 label（#243），否则 values 变更不触发 upgrade。

## 待办

Hydra 已下线（数据库与 `kv/k8s/hydra` 待维护者确认后删除）；MFA 自助管理；前端重做；
SPIFFE 机器登录与 MCP agent 委托设计。
