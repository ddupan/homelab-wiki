---
title: Gitea Dynamic Runner
lifecycle: experimental
evidence: documented
last_reviewed: 2026-09-21
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/gitea-dynamic-runner/src/branch/main/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/dynamic-runner/README.md
  - https://git.ddupan.top/panxiao81/ci-actions/src/tag/v1
---

# Gitea Dynamic Runner

原名 `gitea-microvm-runner`，现为
[gitea-dynamic-runner](https://git.ddupan.top/panxiao81/gitea-dynamic-runner)。
它为 Gitea Actions 按需创建一次性执行环境，支持 Kubernetes Pod 和 Cloud Hypervisor
microVM；每个环境只执行一个 job，结束后销毁环境及本地状态。

更名由维护者提供；以下组件与接口说明依据 2026-09-16 查阅的项目 README。
维护者进一步明确：**项目正在积极开发，具体启用范围和实现进度以该项目文档为准。**
本页保留用途、设计原则和该次 README 的摘要，仅补充维护者明确提供的阶段与容量，不复制维护完整部署范围或消息队列参数清单。
本轮未查询现场，不将设计接口视为已完成的上线验收。

## 当前开发与启用阶段

维护者于 2026-09-16 补充：开发接近完成，动态 `pod` 已上线测试，`vm` 正在工作；
纯 `self-hosted` 的旧常驻 runner 准备退役。

| 执行环境 | workflow labels | 系统总并发量 | 阶段 |
|---|---|---:|---|
| Pod | `[self-hosted, pod]` | 4 | 已上线测试 |
| VM | `[self-hosted, vm]` | 1 | 正在工作，具体进度以项目文档为准 |

并发量是对应环境在系统中的总容量，不按仓库或 workflow 分别分配一份额度。
本页记录维护者提供的阶段与容量，不将“上线测试”写成完整正式验收；
旧常驻 runner 也尚未标记为已退役。后续变化继续以项目文档为准。

## workflow 如何选择执行环境

README 定义两种稳定接口，在 workflow 的 job 中选择：

```yaml
runs-on: [self-hosted, pod]
```

```yaml
runs-on: [self-hosted, vm]
```

| 接口 | 执行方式 | 使用时需要理解的边界 |
|---|---|---|
| `pod` | 动态 Kubernetes privileged Pod；workflow 使用 host executor | 旧 README 要求 pipeline 按需 setup Docker；Docker 的新约定见下文。host executor 指 Pod 内执行环境 |
| `vm` | 动态 Cloud Hypervisor microVM | 每个任务创建独立 COW disk、seed 和 TAP，guest runner 执行一个 job 后关机并清理 |

两种接口不能仅凭“环境一次性”就认定具有相同的隔离边界。
接入前需要结合项目设计约束和实际部署确认任务的信任范围。
旧 homelab-infra 文档中的 `kind-microvm` 是早期记录，不作为本项目当前 workflow 接口。

### Docker 可用性约定更新

维护者于 2026-09-21 明确：CI 后端正在修复，后续由 runner 保证 dockerd 默认可用。
这取代旧说明中要求业务 workflow 自行启动 Docker daemon 的部分；不能据此推断 BuildKit、
kind 等其他工具也默认就绪。数据库集成测试不因使用 Docker 而要求 VM。
消费方 workflow 应检查 Docker 是否可用，而不重复启动 daemon、强制 storage driver 或
覆盖 runner 提供的 endpoint。[Ayatori #6](https://git.ddupan.top/panxiao81/ayatori/pulls/6)
正在按此约定调整。此处依据维护者说明，不表示后端修复已经部署或远端集成已经通过，
`last_verified` 保持不变。

## 组件如何协作

当前 README 描述的 bootstrap 路径为：

```text
Gitea workflow_job webhook
  → controller 筛选 queued job / label
  → NATS JetStream WorkQueue
  → worker 领取任务并限制并发
  → Pod 或 microVM backend 创建一次性执行环境
  → 执行一个 job，随后清理环境
```

`microvm-runner-launch` 管理 VM 的临时磁盘、网络及清理，`guest-runner` 领取一次性
注册凭据并以 ephemeral 模式注册。`pod-worker` 创建 Kubernetes 执行 Pod。
该次 README 描述同一 runner label 的 worker 共享同一个 durable consumer，通过增加 worker
或 capacity 扩容。这是 runner 所属 Account 和 stream 内的协调约定，不是跨 NATS Account
的全局命名要求。具体 durable 名称和后续调度改动以项目文档为准。

[NATS](nats.md) 作为集群共享服务部署；维护者说明当前只有 Dynamic Runner 消费它，
不因此将 NATS 视为 runner 私有组件。

webhook → NATS 是尽快验证 Pod/VM 生命周期的 bootstrap 实现。
长期目标是 controller 兼容 Gitea Runner 协议，直接注册、声明 labels、领取 task，
再交给 Pod/VM executor；不能把该目标描述为已经实现。

## 设计原则：runner 提供环境，workflow 消费身份

**每个动态 Pod/VM 都应具备独立获取自身 SPIFFE 身份的能力。** 这是执行环境的设计原则，
由维护者于 2026-09-16 明确；不以是否接入某个特定下游服务作为 runner 的职责定义。

runner 负责创建、运行和清理环境，并提供该环境获取自身 SPIFFE 身份的能力。
workflow 决定如何消费身份：登录哪个服务、请求哪个 audience、交换什么 token、
何时刷新或撤销凭据，以及执行哪些业务操作。下游服务继续自行验证身份并维护权限。

例如，向 OpenBao 登录并交换 Bao token 是需要访问 OpenBao 的 workflow 的工作，
不属于 runner 内置的业务流程。向其他服务请求 token 也遵循同一边界；
runner 不应替 workflow 选择下游 role/policy，或统一代理其业务凭据交换。

通用实现已发布为 [`panxiao81/ci-actions@v1`](https://git.ddupan.top/panxiao81/ci-actions/src/tag/v1)：
`spiffe-openbao-login` 负责获取 JWT-SVID、交换 Bao token 和退出吊销，`setup-nexus`
负责匿名配置 Ansible Galaxy、Go module proxy 与 OCI endpoint。后者读取 Nexus public
repository 时不需要 Bao 登录；发布制品应另建 repository service account 和最小权限
policy。

这些 Action 不扩大 runner 权限。runner 只提供 Node.js 20、`spire-agent` 与 Workload
API socket，workflow 明确声明 role、audience 和用途，目标服务 policy 做最终授权。
由于短期 token 会进入 Actions job 临时文件，只能在一次性 Pod/VM executor 使用。

因此，身份相关的环境验收应关注 Pod/VM 能否取得各自身份和是否保持隔离；
具体服务的登录与 token 使用由对应 workflow 验收。
本段记录设计职责，不表示获取身份的能力已经在所有 backend 完成实现或现场验证。

## 基础设施归属与运行凭据

- `jwt-broker` 是早期共享 Kubernetes runner 的过渡实验；目标架构不部署它。
- 以下 NATS、webhook 与 runner registration 凭据用于执行平台本身运作，
  与 workflow 自行请求的下游业务 token 分开管理。
- NATS 密码、webhook secret 和 registration token 从文件读取，不复制进知识库。
- registration token 不写入 seed image；worker 通过单次 nonce endpoint 交给 guest。
- base image 不携带 runner identity、registration token、SSH 密码或 host key。
- runner 软件保存在本项目；Kubernetes、OpenBao、LXC、bridge 和容量配置保留在 homelab-infra。
- homelab-infra 的 `platform/gitea-runner/` 是此前的常驻 runner；本 README 不能证明它已被替换或退役。

## 继续阅读

- [项目 README](https://git.ddupan.top/panxiao81/gitea-dynamic-runner/src/branch/main/README.md)：接口、组件、开发命令与安全边界，本轮已查阅。
- [设计原则](https://git.ddupan.top/panxiao81/gitea-dynamic-runner/src/branch/main/docs/design-principles.md)：README 指向的完整设计约束，本轮未逐篇复核。
- [Runner 协议路线](https://git.ddupan.top/panxiao81/gitea-dynamic-runner/src/branch/main/docs/runner-protocol-roadmap.md)：README 指向的长期调度路线与迁移边界，本轮未逐篇复核。
- [SPIFFE/SPIRE](spire.md)：统一机器身份的设计定位与阶段依据。
- [`ci-actions@v1`](https://git.ddupan.top/panxiao81/ci-actions/src/tag/v1)：workflow 可复用的 SPIFFE/OpenBao 登录与 Nexus 配置 Action。

实际启用范围、workflow 验收、排障及消息队列约定在项目文档中维护。
开发中的变化直接以项目文档为准，知识库不另列“启用范围待核实”任务。
