---
title: IAM 人类登录链路交接
last_reviewed: 2026-10-01
---

# IAM 人类登录链路交接

当前要完成的是 **真实 AD + Passkey → Spring iam-login → Hydra → Gitea 原账号及原仓库权限**。
应用实现已经合并，开发实例已准备好；下一步先处理基础设施 PR #168 的回调切换，再由维护者
完成真实登录验收。不要重新进行框架选型或扩展完整 self-service。

本页是 2026-10-01 交接快照。持久服务说明以 [Hydra 服务页](../services/hydra.md)为准，
设计边界见[独立 IAM 草案](../architecture/independent-iam-draft.md)。接续时重新核对 PR、
Flux 和运行实例，不能把下面的历史验收直接当作当前状态。

## 仓库与交付状态

| 对象 | 已确认状态 | 接续入口 |
| --- | --- | --- |
| iam-login | PR #6 已合并，版本 `5f49a7c7c6f7732e9d2b39ac005c03533d30fac2` | [PR #6](https://git.ddupan.top/panxiao81/iam-login/pulls/6)、[源码](https://git.ddupan.top/panxiao81/iam-login/src/commit/5f49a7c) |
| 基础设施 | PR #168 在 2026-10-01 查询时仍 open、未合并；提交 `61674df` | [PR #168](https://git.ddupan.top/panxiao81/homelab-infra/pulls/168)、[切换及回退说明](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/61674df/apps/hydra/README.md) |
| wiki | 实现、验收和运行边界已同步 main | 本页及 Hydra 服务页 |

本机已有工作区：

- `/tmp/iam-login`：main，已同步 `5f49a7c`，本次检查无未提交修改。
- `/tmp/homelab-hydra-human-login`：`feat/iam-login-hydra-acceptance`，`61674df`，本次检查无未提交修改。
- `/tmp/iam-wiki-main-sync`：wiki 独立工作树，用于直接提交 main；提交前先同步远端。

这些 `/tmp` 路径是接续便利条件，不是永久部署或备份。路径消失时从远端恢复源码；秘密、
现有 MFA 数据和运行配置不能从测试 fixture 重建。其他工作区可能有无关修改，不要 reset。

## 已实现的边界

- Java 25 / Spring Boot 4.1.1 / Spring Security 7.1.1。Native 是交付目标，日常先验证 JVM。
- Spring Security 管理密码认证、MFA 因素、SecurityContext、session、CSRF 和本地退出。
  React 只提供页面和 WebAuthn 浏览器交互；原生表单处理密码、授权和注销确认。
- AD 仓储沿用本次用户密码 bind 连接，读取稳定主体和直接 `memberOf`；不新增只读服务账号，
  不保存密码/LDAP 连接，不展开嵌套组或修改组名。
- WebAuthn 使用官方 JDBC 仓储及 PostgreSQL。首次注册需近期密码；已有凭据后的新增注册
  需要 MFA；注册动作本身不算第二因素。
- `JdbcCredentialRegistration` 封装注册行锁与事务，锁内重新检查策略并保存凭据。
  Security 集成不直接写 SQL。数据源/连接池由 Boot 自动配置。
- `HydraGateway` 统一 Login/Consent/Logout；Boot `RestClient.Builder` 装配 HTTP client，
  连接/读取超时可配置，保持禁止跟随重定向。
- `clients/domain/ClientRepository` 是仓储契约，Hydra HTTP 实现持久化；Hydra PostgreSQL
  是 client/secret 唯一权威，不直接读取 Hydra 内部表，不公开 Admin API。
- 管理接口使用有效 MFA + 显式直接管理组 + CSRF。首轮仅 confidential authorization-code，
  scope 限 openid/profile/email/groups；没有任意 Admin 代理或完整管理 UI。
- 新客户端启用策略保存在 Hydra metadata；无标记旧 client 暂兼容配置 allowlist。
  禁用客户端不等于撤回已签发 token 或已建立的应用会话。

具体接口、参数及策略见源码 [Hydra 接入](https://git.ddupan.top/panxiao81/iam-login/src/commit/5f49a7c/docs/hydra-login.md)、
[客户端管理](https://git.ddupan.top/panxiao81/iam-login/src/commit/5f49a7c/docs/client-management.md)、
[WebAuthn](https://git.ddupan.top/panxiao81/iam-login/src/commit/5f49a7c/docs/webauthn.md)。

## 运行实例与秘密位置

| 对象 | 运行约定及最后核对 |
| --- | --- |
| 开发 UI | `https://laptop.tail7e769.ts.net:18082/signin`，Tailscale 地址 `100.102.113.57`，不绑定所有网卡 |
| 开发容器 | `iam-login-ad-jvm`，JVM；2026-09-29 更新 artifact 为 `iam-login-5c20a10d53f19aeb.jar` |
| MFA 数据库 | `iam-login-dev-postgres-1`，loopback 15432，持久卷 `iam-login-dev_postgres`；禁止清空或重建用户凭据 |
| 私有 Admin 通道 | `127.0.0.1:18445` → `hydra/hydra-admin:4445`；临时自动重连 port-forward，依赖本机进程存活 |
| Hydra issuer | `https://hydra.ad.ddupan.top`；本次切换不改变 issuer、client secret、签名密钥或 Gitea 登录源 |
| 保留路径 | Gitea 的 `authelia` 登录源与旧 Go `hydra-login` 适配器，供回退 |

2026-10-01 本次只读检查：开发 `/signin`、`/actuator/health/readiness`、Admin 转发
`/health/ready` 均为 HTTP 200。未重新执行 AD 密码/MFA，也未查询 Flux 的实际回调配置；
PR #168 仍未合并，不宣称切换已发生。

运行目录为 `/tmp/iam-login-ad-runtime`：

- `application.env`、`database.env`：受限运行配置，含秘密，禁止打印、提交或复制到文档。
- `hydra-subject.json`：2026-09-29 从目标 Gitea 账号现有 Hydra 外部关联只读取得的映射。
  同时核对了开发 Passkey 库里的 AD authority + objectGUID。不要按用户名/邮箱重新推导 sub。
- `application.pre-hydra.env`、`pre-hydra-command.json`：本次开发更新前的配置及原镜像/命令，
  用于回退；2026-10-01 确认文件存在，未输出内容。
- `browser.key`、证书、truststore：保持原 RP ID 和信任配置。不要把测试证书或测试凭据替换进去。

`/tmp/iam-deploy-mfa.py` 是此前使用的临时部署脚本：会替换开发容器并从当前构建目录复制 JAR。
**不要不经检查直接重跑它做回退**；它不是持久部署入口，也不会自动选择原版本 JAR。

Admin 转发在 Hydra Pod 重建时会断开，当前运行器会重连。接续时先检查端口和进程，失效时
才在受管终端重新运行以下命令；不重复启动多个占用相同端口的循环：

```sh
kubectl -n hydra port-forward --address 127.0.0.1 service/hydra-admin 18445:4445
```

开发配置关闭默认 Boot LDAP health indicator，因为它检查的未配置连接不对应用户 bind
AD 仓储。数据库健康仍保留；readiness 不能证明 AD 凭据有效或完整登录链路可用。

## 验证证据与尚未完成事项

已完成：

- 维护者此前验收过真实 AD 密码、直接组，以及 AD + Passkey 开发路径。
- 2026-09-29 重构后 37 项 JVM 测试、bootJar 及隔离浏览器 OIDC/注销回归通过。
- PostgreSQL 集成测试覆盖 client CRUD、Hydra 重启持久化、更新保留密钥、注册锁及事务回滚。
- 隔离浏览器验证 code/token、签名、issuer/audience/nonce/旧 sub/组、授权码重放拒绝、
  remembered login 仍需确认、注销 token 签名和 sid 关联，以及 Spring session 清除。
- 真实开发环境可读取真实 Hydra challenge，未认证请求仍被送到登录页；未绕过密码/MFA。

尚未完成：

- PR #168 合并及 Flux 应用后的真实 **Spring → Hydra → Gitea** 原账号/权限验收。
- 真实管理员 session 下的客户端 CRUD 接口验收。
- Gitea 联动注销：2026-09-29 client 没有登记 front/back-channel 或 post-logout 端点。
  必须先核对应用支持的协议，不能填入虚构地址，也不能把 Hydra 注销成功当成 Gitea 已退出。
- AD/WebAuthn/Hydra 完整 Native 验收，以及真实 MFA 数据库恢复验收。
- `processTestAot` 的夹具退出问题：处理完成后，非 daemon LDAP listener 阻止 JVM 退出。
  日常 JVM 验证已跳过测试 AOT，不能视作它已通过。依据见源码 `docs/native-validation.md`。

复现 JVM 检查（使用已有 Docker 缓存，不需要每轮编译 Native）：

```sh
IAM_DOCKER_USE_SUDO=1 IAM_GRADLE_CACHE=/tmp/iam-login-gradle \
  IAM_NPM_CACHE=/tmp/iam-login-npm scripts/gradle-in-docker \
  test bootJar -x processTestAot -x compileAotTestJava -x processAotTestResources
```

浏览器夹具命令与隔离端口见源码文档；测试只能使用临时 PostgreSQL，不得重置真实开发库。

## 接续顺序与完成条件

1. 重读 PR #168 的当前内容及维护者新反馈，核对开发容器、18445 转发、HTTPS、AD/DNS 依赖。
   2026-09-30 发生过 DC/DNS 故障，已有恢复记录，接续认证排障应先读
   [事故报告](../incidents/2026-09-30-dc-dns-openbao.md)，不要默认一切失败都在 Spring。
2. 按维护者的 PR 审查流程处理 #168，不自行合并。该配置是 Hydra 全局回调，合并后会影响
   当前经 Hydra 的登录请求，不是仅为某个浏览器开关。
3. 合并后核对 Flux 实际应用版本、Hydra 新 ConfigMap/Deployment 就绪及 Admin 转发重连。
   先检查匿名路径，再请维护者从 `https://git.ddupan.top/user/oauth2/hydra` 发起登录。
4. 由维护者完成 AD 密码、既有 Passkey、授权确认；确认回到原 Gitea 账号并保留仓库权限。
   agent 不能代替真实 MFA，也不能把隔离测试写成人类验收。
5. 验证真实 client 管理权限，并研究 Gitea 注销协议兼容性；另行安排 Native 与正式部署。
   将验收结果写回服务页，进度放相关 PR/issue。

验收失败时保留现场证据但不记录 token、code、challenge 或密码。Hydra 回调回退通过 revert
#168 配置恢复旧 Go `/login`、`/consent`，按新分支/PR 流程交付；保留直接 Authelia 登录入口。
本地应用需要回退时使用上述备份与原镜像/JAR 命令重建容器，**保留数据库及 Passkey**，
不要运行 `compose down -v`、全表清空或删除账号关联。

## 后续工作约束

代码/基础设施改动新分支开 PR，不自行合并；wiki 检查后直接推 main。中文维护文档与提交，
保留 GPG 签名，禁止为绕过 agent 故障关闭签名。PR #6 已合并，不继续向旧分支塞新代码。

正式入口目标是用 Hydra public 与 Spring UI/API 同源替换 `auth.ddupan.top`，仍独立部署，
Ayatori 只是消费者。该正式切换不在 #168 内；涉及 issuer、账号关联、cookie、可信代理与
WebAuthn RP ID/重新注册，需独立设计和验收，不把整个 `/oauth2/**` 都路由给 Hydra。

不扩展完整 self-service：AD 密码/组由 RSAT/CLI 管理，全部 MFA 遗失走核实身份后的人工
数据库恢复。machine/agent 身份、动态授权和目录迁移仍属后续范围；agent 不等同传统
service account。保留框架负责认证的边界，不重新自建认证状态机。
