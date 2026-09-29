---
title: Hydra 与 OIDC 上游适配器
lifecycle: experimental
evidence: live-verified
last_reviewed: 2026-09-27
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

### 独立登录服务的 AD 接入

`iam-login` 的人类界面沿用内联上下文与原生表单，新增 AD 第一因素验收入口；
以用户身份 LDAPS bind，读取 objectGUID 和直接 `memberOf`，组名保持原样。
当前不展开嵌套组或主组，不能视为已完成与 Authelia 的有效组集合等价验证。
密码成功仅代表第一因素通过；Gitea 仍使用上面已验收的 Go/Authelia 路径。
按 2026-09-27 明确的实现边界，React 只替换 Spring Security 默认 UI，密码 POST、
因素状态和认证会话交由框架管理。待 MFA 页面要求近期密码因素，尚未实现的应用入口拒绝访问。监控 Basic 认证与人类登录会话隔离。

本轮开发验证通过 JVM 测试，并从 JVM 通过 CA/域名验证读取真实 AD RootDSE。
2026-09-25 维护者已在 HTTPS 开发入口完成真实密码验证，成功进入待 MFA 页面，
并反馈目录标识、邮箱及六个直接所属组的查询结果。此人类验收只覆盖 AD 第一因素与
属性读取，不包括 MFA 或 Hydra 登录。新增路径尚未跑 Native；日常迭代不要求每轮原生编译。开发入口使用受限 Tailscale HTTPS，属于临时验收实例，不是生产入口。
AD 接入与 Spring Security 重构统一见 [iam-login PR #4](https://git.ddupan.top/panxiao81/iam-login/pulls/4)；
2026-09-27 通过 18 项 JVM 测试和 1 项浏览器回归，后续真实人类验证反馈见下方 WebAuthn 开发验证。
配置、边界与使用方式见
[iam-login AD 接入文档](https://git.ddupan.top/panxiao81/iam-login/src/branch/main/docs/ad-login.md)。

### WebAuthn 开发验证

2026-09-27 的 [iam-login PR #6](https://git.ddupan.top/panxiao81/iam-login/pulls/6) 将第二因素接入
Spring Security 官方 WebAuthn 流程，并以官方 JDBC 仓储和本地 PostgreSQL 持久卷保存凭据。
该实现仍在开发 PR，生产 Go/Authelia 链路未切换。

开发入口仍为 `https://laptop.tail7e769.ts.net:18082/signin`，限 Tailscale 可达。
先验证 AD 密码，首次使用注册 passkey，再实际验证 passkey；注册成功本身不通过 MFA。
已有凭据后的新增注册要求现有 MFA；本轮 UI 不开放凭据管理、删除或自助恢复。
当前真实 AD 开发实例的 `/signin/complete` 显示双因素结果，尚未配置 Hydra 授权接入；
新增 Login/Consent 的代码与隔离验证见下文。

2026-09-28 维护者明确首轮自用边界：AD 用户、密码和组继续使用 RSAT/命令行管理；
丢失全部 MFA 时由管理员核实身份后人工操作目标主体的数据库凭据恢复。
不开发目录管理、自动恢复或完整 self-service UI，也不将其作为核心人类链路验收前提。

22 项 JVM 测试与 Chromium 虚拟认证器流程通过，覆盖再次登录、注册限制、会话轮换、
challenge 过期/消费、断言重放及跨主体凭据拒绝。真实开发 HTTPS 页面的证书与表单回归
已检查。维护者随后在该开发入口完成验收，反馈“我验收完了，看样子能工作”；
据此记录 AD + passkey 人类浏览器路径已获维护者确认。此反馈不构成 Native、数据库
重启恢复或 Hydra/Gitea 新链路验收，也未限定认证器型号与跨设备兼容范围。
数据库开发操作、数据卷保留与失败边界见
[WebAuthn 文档（开发分支）](https://git.ddupan.top/panxiao81/iam-login/src/branch/feat/webauthn-mfa/docs/webauthn.md)。

### 独立登录服务的 Hydra 接入

双因素后的 Login/Consent、客户端管理与统一注销已提交至
[同一 iam-login PR #6](https://git.ddupan.top/panxiao81/iam-login/pulls/6)，源码版本为
[62b6e9d](https://git.ddupan.top/panxiao81/iam-login/commit/62b6e9d)，尚未合并或切换生产入口。
2026-09-28 已通过 36 项 JVM 测试与隔离 Hydra v26.2.0 的浏览器授权码及注销流程：
模拟 AD → WebAuthn → 原生表单确认 → Hydra code → 客户端兑换并验签 ID token。
验证覆盖 issuer、audience、nonce、显式配置的旧 subject、直接组 claims 与授权码重放拒绝；
独立 MFA 路径此前也通过浏览器回归。本轮另验证客户端 CRUD、Hydra 重启后的 PostgreSQL
持久化、更新保留密钥、管理权限/CSRF 拒绝、再次授权确认、注销通知签名与 sid 关联，以及
Spring 本地会话失效。这些是测试夹具结果，不是生产 Gitea 验收。

生产主体按 AD authority + objectGUID 显式绑定现役 Hydra sub，未绑定账号拒绝授权；
不靠邮箱、用户名或自动新建账号迁移。生产映射值尚未取得并核实，现役入口未切换，
AD/WebAuthn/Hydra 的 Native 完整链路也仍待验收。配置与迁移条件见
[Login/Consent 文档（开发分支）](https://git.ddupan.top/panxiao81/iam-login/src/branch/feat/webauthn-mfa/docs/hydra-login.md)。

Hydra 持有客户端注册表并提供 CRUD Admin API；新增客户端不依赖修改服务器配置文件。
管理能力由 iam-login 的 `clients` 领域模块包装：Spring session、有效 MFA 与显式直接管理组
控制访问，写操作保留 CSRF；不公开 Hydra admin 或任意代理。本地实现中的客户端与密钥只存
Hydra PostgreSQL，启用标记写入 client metadata 并在授权时重新读取。旧配置 allowlist
只作无标记客户端的过渡兼容，不是第二份注册表。暂不建设完整自助管理 UI。

统一注销计划沿用 Hydra 登记的 front/back-channel 协议；登录服务通过 Spring 清除当前
本地会话。Hydra 必须保留登录会话以关联注销；仅凭 issuer 的 remembered-login 标记不能
绕过本地 MFA。下游不支持注销协议、通知失败或 issuer 会话已过期时，不能声称所有应用均
已退出；不等同撤销全部 token 或其他设备会话。

正式入口目标是替换现役 `auth.ddupan.top`，Hydra public 与 iam-login UI/API 按路径共用
origin，仍保持独立部署。不能把整个 `/oauth2/**` 都路由给 Hydra，也不发布 admin 路径。
上线前需审查 issuer 与现有账号关联、cookie/TLS 转发、WebAuthn RP ID 与凭据重新注册、
回退路由；这是部署计划，现有 Go/Authelia 生产链路未改变。

### 登录服务的数据源与框架边界

应用运行需要 PostgreSQL，通过 Boot 的 `spring.datasource.*` 与 `spring.datasource.hikari.*`
配置连接及连接池；不以关闭 WebAuthn 为由排除数据源自动配置。WebAuthn 继续使用官方 JDBC
仓储，注册行锁及事务封装在持久化实现，策略复查与凭据保存处于同一事务。
客户端使用领域层 `ClientRepository`，Hydra HTTP 实现仓储；Login/Consent/Logout 共用
`HydraGateway`。HTTP client 由 Boot builder 装配，连接和读取超时通过
`iam.hydra.http.connect-timeout` / `read-timeout` 配置（默认 3s / 5s），保持禁止重定向。
该重构见 [fdf2e49](https://git.ddupan.top/panxiao81/iam-login/commit/fdf2e49)，随 PR #6 交付。
2026-09-29 的 37 项 JVM 测试与隔离浏览器登录/注销回归通过，不表示开发实例或生产入口已更新。
测试 AOT 夹具退出问题与 Native 验收仍待处理，详见源码 `docs/native-validation.md`。
