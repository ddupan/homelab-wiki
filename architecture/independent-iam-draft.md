---
title: 独立 IAM 草案：人类、机器与 AI Agent 的统一应用接入
status: draft
last_reviewed: 2026-09-25
last_verified: null
sources:
  - 维护者于 2026-09-25 的架构讨论与草案记录要求
---

# 独立 IAM 草案：人类、机器与 AI Agent 的统一应用接入

本页记录完整 IAM 的设计意图，状态仍为 **draft**。2026-09-25 维护者随后选择先实施
[Hydra 人类登录 PoC](../services/hydra.md)：通用 OIDC 上游适配器暂用 Authelia，Gitea
新增 Hydra 登录源；维护者已确认成功返回原账号且仓库权限正常，第一轮人类 PoC
验收通过。这不表示完整方案已采纳或开始全面迁移。
长期名称、资源模型及 agent 接口尚未确定。

## 动机与首要目标

首要目标是降低下游应用集成成本。原生接入 SPIFFE 的应用覆盖有限，OIDC/OAuth 则已有
广泛的应用与 CLI 生态。通过独立 IAM 集中处理身份验证，让应用沿用标准登录和授权流程，
即可接入人类、传统机器账户和 AI agent，无需每个应用自行验证 SVID 或集成 SPIRE。

维护者认为，现有方案缺少好用的、真正区分 AI agent 与传统 service account 的身份及
授权模型，这是考虑自行建设的主要原因。拟自建的是主体语义、认证编排与授权能力，
OAuth2/OIDC 协议和 token 签发优先交给 Hydra。

Hydra 的核心价值是把“如何验证身份”与“如何完成标准授权流程并签发 token”解耦。
统一 token 格式不是主要目标，也不要求所有应用 API 直接接受 Hydra token。

## 独立服务边界

IAM 应当能够独立部署、运行和恢复，不依赖 Ayatori 的 API、CRD、controller 或领域资源。
Ayatori 是其消费者，依赖关系类似 OpenStack 其他服务对 Keystone 的依赖；这一类比
不意味着复刻 Keystone 的全部 API 或功能。即使未来命名为 Ayatori IAM，也不改变边界。

| 部分 | 拟承担的职责 |
|---|---|
| 人类认证后端 | 人类登录、MFA、账号生命周期；可选 ZITADEL，过渡期保留 Samba AD |
| SPIRE | workload 身份证明与 SVID 签发，可辅助 machine 或 agent 认证 |
| Login / Consent 与身份授权服务 | 验证不同主体的证明，映射稳定身份，处理登录、授权、组和必要的动态审批 |
| Hydra | OAuth2/OIDC 流程、client 与 token 签发 |
| 下游应用 | 关联本地账号，执行应用自身权限，按原有机制签发或使用应用凭据 |

```text
人类：交互登录 / 上游 IdP ──────┐
机器：SPIFFE 等预配置身份 ─────┼→ 独立身份验证与授权 → Hydra → OIDC/OAuth 消费者
Agent：人类授权 / SPIFFE /     │                                  ├→ Gitea 等应用
       后续专门认证方式 ──────┘                                  └→ Ayatori API server
```

Ayatori 使用裁剪的 kube-apiserver，目标是让它信任 Hydra 签发的 token 来验证身份，
再由自身 RBAC 执行资源授权。具体 token 类型、claims、audience 与 JWT authenticator
兼容性需要验证；不能预先把任意 Hydra access token 都视为 API server 可用凭据。

## 主体类型与认证方式分离

人类、machine、agent 是不同的主体类型，不能按所用认证协议决定分类。
Agent 可以使用 SPIFFE 辅助证明执行环境，而仍然是 agent 主体，不必冒充传统机器账户。
Agent 的负责人、委托人及当前执行实例也不应与 agent 自身身份混为一谈。

| 维度 | 传统机器账户 / CI | AI agent |
|---|---|---|
| 任务特征 | 预定义流程与资源范围 | 能理解任务、作出决策，可能跨应用并在执行中改变操作路径 |
| 权限需求 | 通常可以预先配置 | 潜在范围更广，可能执行中动态申请 |
| 授权方式 | 审核配置后按固定规则授予 | 基础权限与任务、会话或限时授权组合，由策略或人类批准 |
| 交互能力 | 固定程序处理约定流程 | 可使用 CLI、MCP 和 skills，自主组织请求并在需要时请求批准 |
| 审计语义 | 哪个 workload 执行了操作 | 哪个 agent、哪次执行、代表谁、依据哪次授权执行 |

更广的潜在权限不等于常驻全权。动态批准应转化为服务端认可的授权和适当凭据，
不能由 agent 自报身份或声明 scope 就自动生效。申请、批准、期限、撤销以及下游已有
会话和 token 的失效语义需要明确设计，不能假设 Hydra 自动提供完整实现。

认证入口保持可扩展：

- Remote MCP 的 OAuth 可提供人类参与的授权入口。设计上允许人类在流程中确认或选择
  agent 身份、委托关系与权限，再由服务端绑定凭据。普通 MCP OAuth 并不自动定义
  agent 主体语义；具体绑定属于本方案要实现的能力。
- SPIFFE 路径以经人类审核的 workload/身份绑定规则为信任来源，运行时验证证明是否
  满足规则。交互批准和预配置批准都是可用的信任建立方式。
- MCP 和 skills 是 agent 参与流程的工具及操作约定，本身不替代可验证凭据。
  后续可以增加专门的 agent 认证方式，不必现在锁定一个唯一协议。

Agent 可以独立使用自身权限，也可以接受人类委托。人类授权 agent 不等于 agent
变成人类账号；需要时保留“agent A，经用户 B 授权”的关系与审计信息。

## 无浏览器的标准登录与 Gitea 示例

Authorization code flow 不要求必须使用图形浏览器。对于可通过 HTTP 完成的流程，
agent 可以用 curl/CLI 保存 cookies、跟随重定向、提交表单和身份证明，并到达 callback。
必须保留 state、nonce、PKCE 等协议绑定；以 HTTP 客户端执行不意味着跳过这些校验。
专用登录 helper 可以作为便利工具，但不是架构前提。

关键是 Login 服务支持 machine/agent 的身份证明，而不强迫它们完成人类密码、
交互 MFA 等认证。Consent 按已有授权策略处理，必要时请求人类批准。

Gitea 的目标路径包含内外两层授权：

```text
官方 tea CLI 发起 Gitea OAuth 授权
  → Gitea 经 OIDC 请求 Hydra 登录
  → Login 服务验证 agent 或 machine 的身份
  → 接受 login challenge，按策略完成 Hydra consent
  → Hydra 回调 Gitea，Gitea 关联对应 bot 账号
  → 完成 Gitea 自身对 tea 的授权确认
  → Gitea 回调 tea，由 tea 完成 code 交换并取得 Gitea token
  → tea 按 bot 的 Gitea 权限调用 API
```

这里 Hydra token 用于 Gitea 的身份登录，Gitea token 用于 CLI 调用应用 API。
因此不要求 Gitea API 直接接受 Hydra bearer token，也不以自建 PAT 分发 broker 为前提。
Bot 是下游账号映射，不代表所有 agent 共享一个万能 bot。

该路径尚未端到端验证。需要验证官方 CLI 的授权 URL/callback 交接、Gitea 本地会话与
首次授权确认、账号关联和 scope，以及刷新与重新登录。其他应用可复用相同思路，
但支持 OIDC 不等于所有应用的无交互授权路径均已兼容，须按具体流程验收。

## 统一组与下游授权

集中维护较统一的粗粒度用户组，避免每个应用都独立维护一套 admins 成员关系。
应用仍保留自身角色、team 和资源权限，由明确映射决定中央组在应用内的权限。
统一组不等于一个全局 admins 自动拥有所有服务的管理权。

Agent 的动态授权需要落到应用可识别的 scope、角色、账号权限或其他已有授权机制上。
仅在 Hydra token 中增加一个 claim，不意味着下游会自动执行或撤销相应权限。
具体组名、角色模型及同步方式尚未确定。

## 人类后端、Samba AD 与 DNS 演进

### 人类认证后端的接口边界

2026-09-25 维护者明确：考虑 ZITADEL 是为了复用认证会话与登录状态机，而不是把它作为
另一个 OIDC 上游。下一阶段目标是由人类认证后端处理认证因素与会话，适配层验证结果、
映射稳定主体并接受 Hydra login challenge；面向下游的 OAuth2/OIDC 仍由 Hydra 提供。
第一轮通过 Authelia OIDC 的 PoC 保留为已验收基线，尚未部署此替代路径。

同日的上游接口与源码评估形成两个候选，尚未决定切换：

| 候选 | 可复用能力 | 尚需承担的接入工作 |
|---|---|---|
| ZITADEL Session API + Login V2 | 逐步验证认证因素、会话、账号管理；Login V2 有登录编排与 UI | 将登录事务绑定到 Hydra challenge，服务端验证认证结果并接回 Hydra；按选定版本验证 LDAP、MFA 与完整恢复流程 |
| Ory Kratos + self-service UI | 登录、MFA、恢复与会话流程；上游已有 Hydra login challenge 集成 | 部署和维护独立 UI，保留主体映射与 consent；Samba AD 不能假设存在开箱即用的 LDAP 认证接入 |

Kratos 在认证与签发的职责分离上更直接，是值得优先验证的替代候选；但若必须继续使用
Samba AD 密码登录，LDAP 过渡成本可能使 ZITADEL 更合适。Kratos 本身是 headless 服务，
现成参考 UI 不等于无需维护的内置管理门户，亦不能把 Ory Network 的功能直接视为自托管
开源版能力。此判断是方案评估，不是新的部署决定。

ZITADEL Session API 返回会话不等于已完成全部认证；需要确认已验证因素、有效期、用户
状态和所需 MFA。官方 Login V2 的流程编排包含这些判断。无 OIDC 上下文登录及默认完成
跳转可用，但普通跳转不是传给 Hydra 的认证证明，也不自动绑定原始 login challenge。

查阅时上游文档与开发分支存在差异：Hosted Login 文档仍列出 LDAP 限制，而
[Login V2 固定源码](https://github.com/zitadel/zitadel/blob/5ca0b54ca311c4be535589e7c375f9bea50e3ec2/apps/login/src/lib/server/idp.ts)
已有 LDAP 认证实现；不能据此宣称某个发布版本已经验收。部署前需锁定发行版本再验证。

参考：[ZITADEL Session API](https://zitadel.com/docs/reference/api/session/zitadel.session.v2.SessionService.CreateSession)、
[Login App](https://zitadel.com/docs/guides/integrate/login-ui/login-app)、
[Hosted Login 限制](https://zitadel.com/docs/guides/integrate/login/hosted-login)、
[Kratos Hydra 集成源码](https://github.com/ory/kratos/blob/master/selfservice/flow/login/handler.go)、
[Kratos self-service UI](https://github.com/ory/kratos-selfservice-ui-node)、
[LDAP 功能请求](https://github.com/ory/kratos/issues/274)。

### 目录与 DNS 迁移

人类同样使用这套独立 IAM。过渡期可以保留 Samba AD，通过 ZITADEL 连接 LDAP；
后续可以把人类账号迁出 Samba。ZITADEL 是候选后端，不是本草案已经确定的依赖。
更换认证后端时应保持稳定主体与下游账号关联，避免按可变邮箱或用户名重新识别账号。

维护者认为 Samba AD 使用率较低，长期希望完全删除它。退役需处理 LDAP、Kerberos、
SMB 域身份、域成员和域 DNS 等实际依赖，不能用网页登录迁移成功代替全部退出条件。

DNS 可独立评估迁往 PowerDNS Authoritative，主要考虑其 API 与资源成本。可从简单后端
开始评估，不预先要求完整 Recursor/UI/数据库集群。实际资源占用尚未测量。
AD 存续期间保留其域记录权威与动态更新边界；普通记录的迁移、Blocky/路由器解析链和
最终域退役应分别设计。PowerDNS 不是 IAM 的必需组件。

## 与现役约束的关系

现役记录仍以 [架构约束](constraints.md)、[Authelia](../services/authelia.md) 和
[SPIFFE/SPIRE](../services/spire.md) 为准。当前文档中的 Authelia 主 OIDC 入口、
服务直接验证 SPIFFE 后签发自身 token 的规则，仍是现役基础。第一轮人类 PoC 对
Gitea 增加实验性 Hydra 签发入口的有限变更已在约束索引中单独记录。

本草案提出的变化是：增加独立的多主体 IAM，通过 Hydra 解耦认证与签发，让尚不支持
SPIFFE 的下游复用 OIDC；并为 agent 增加区别于传统 service account 的身份授权语义。
若采纳，应显式更新现役约束和相关服务文档。已能直接使用 SPIFFE 的服务无需强制改道。
这也不构成恢复已归档 [workload-sts](workload-sts-history.md) 项目的决定。

## 后续验证问题

以下是草案的验证范围，不是已启动的实施任务或第二份动态进度表：

1. 一个 SPIFFE 主体，通过官方 tea 的 OAuth 入口，用 CLI/HTTP 完成无浏览器登录，
   以指定 bot 成功调用 Gitea API，同时验证错误身份不能取得该账号。
2. 人类和 agent 使用不同认证方式后，下游仍能通过同一 OIDC 接口识别正确身份与组。
3. Ayatori 的 kube-apiserver 验证 Hydra token，并正确映射主体、组与 RBAC。
4. Agent 动态申请权限，经过策略或人类批准后生效；到期与撤销行为覆盖下游凭据。
5. 明确稳定 agent、执行实例、委托者的绑定方式，以及可供 agent 使用的 MCP/CLI 接口。
6. 独立评估 Samba 退出条件、PowerDNS 资源成本与 DNS 迁移边界。

## 上游依据

以下文档用于说明协议与产品能力，不代表本方案已验证或已选定具体版本：

- [Hydra Login / Consent 流程](https://www.ory.com/docs/oauth2-oidc/custom-login-consent/flow)
- [Gitea OAuth2 provider 与 tea 内置客户端](https://docs.gitea.com/development/oauth2-provider/)
- [tea 登录命令定义](https://pkg.go.dev/code.gitea.io/tea/cmd/login)
- [Kubernetes 身份验证](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
- [ZITADEL LDAP 上游](https://zitadel.com/docs/guides/integrate/identity-providers/ldap)
- [PowerDNS Authoritative HTTP API](https://doc.powerdns.com/authoritative/http-api/index.html)
