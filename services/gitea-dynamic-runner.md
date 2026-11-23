---
title: Gitea Dynamic Runner
lifecycle: experimental
evidence: documented
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/gitea-dynamic-runner/src/branch/main/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/dynamic-runner/README.md
  - https://git.ddupan.top/panxiao81/ci-actions/src/tag/v1
  - homelab-infra platform/dynamic-runner、platform/sandbox-dynamic-runner、platform/sandbox-ci-runners、platform/sandbox-kata 的 README
  - homelab-infra infrastructure/gcp-ci/terraform/README.md
  - gitea-dynamic-runner README（2026-09-16 查阅，历史架构部分）
watch:
  - homelab-infra:platform/dynamic-runner/
  - homelab-infra:platform/sandbox-dynamic-runner/
  - homelab-infra:platform/sandbox-ci-runners/
  - homelab-infra:platform/sandbox-kata/
  - homelab-infra:infrastructure/gcp-ci/terraform/
---

# Gitea Dynamic Runner

原名 `gitea-microvm-runner`，现为
[gitea-dynamic-runner](https://git.ddupan.top/panxiao81/gitea-dynamic-runner)。
它为 Gitea Actions 按需创建一次性执行环境（Kubernetes Pod、OpenSandbox/Kata VM、GKE Autopilot Pod）；
每个环境只执行一个 job，结束后销毁环境及本地状态。

**项目正在积极开发，具体启用范围和实现进度以该项目文档为准。**

## workflow 如何选择执行环境

每个池只声明一个 label，job 的 `runs-on` 也只写这一个。

| `runs-on` | 池 / 成员 | 执行方式与部署位置 | 容量 |
|---|---|---|---|
| `[self-hosted]` | `pod-sandbox`（迁移期间另带别名 `pod`） | sandbox 集群的 Kubernetes Pod，`platform/sandbox-dynamic-runner` | 见该目录配置 |
| `[self-hosted-large]` | `pod-laptop` | laptop k3s 的 Kubernetes Pod，`platform/dynamic-runner` | `POD_CAPACITY=4` |
| `[self-hosted-vm]` | `vm` | OpenSandbox `ci-vm` Pool 的 Kata VM（`kata-clh-runtime-rs`），`platform/sandbox-ci-runners`、`platform/sandbox-kata` | `VM_CAPACITY=1` |
| `[cloud]` / `[cloud-small]` | `cloud-scheduler` | GKE Autopilot 一次性 Pod（`infrastructure/gcp-ci/terraform`），每个 job 一个 ephemeral runner | 默认 2 vCPU / 4 GiB；`cloud-small` 0.5 vCPU / 1 GiB；实际上限为试用账号 GCE 配额 |

容量是池的总容量，不按仓库或 workflow 分配。满载时 worker 不领取，task 在 Gitea 显示等待，由池内其他成员领取。
旧写法 `[self-hosted, pod]`、`[self-hosted, vm]` 已不是当前接口；`pod` 别名只在迁移期间保留。
各池接口不能仅凭“环境一次性”就认定具有相同的隔离边界，接入前结合项目设计约束确认任务的信任范围。

### Docker 可用性约定更新

维护者于 2026-09-21 明确：CI 后端正在修复，后续由 runner 保证 dockerd 默认可用。
这取代旧说明中要求业务 workflow 自行启动 Docker daemon 的部分；不能据此推断 BuildKit、
kind 等其他工具也默认就绪。数据库集成测试不因使用 Docker 而要求 VM。
消费方 workflow 应检查 Docker 是否可用，而不重复启动 daemon、强制 storage driver 或
覆盖 runner 提供的 endpoint。[Ayatori #6](https://git.ddupan.top/panxiao81/ayatori/pulls/6)
按此约定调整。

## 组件如何协作

单副本 Go controller 在同一进程运行原生 Kubernetes worker、
OpenSandbox worker 和 SPIFFE mTLS facade。每个 worker 各自是一个 Gitea runner 池成员（`TASK_SOURCE=gitea`），
持有自己的 registration，只在本地容量池有空位时 `FetchTask`，由 Gitea 在池内分发。sandbox 集群另有一个只运行
`kubernetes-worker` 的实例（`pod-sandbox`）。原先的 scheduler、NATS 队列与 Lease 已于 2026-10-05 移除
（gitea-dynamic-runner `docs/runner-registration-migration.md`）。云端池由 `cloud-scheduler` 为每个排队 job
注册 ephemeral runner，Pod 直连 Gitea。

registration 位于 Bao `kv/k8s/dynamic-runner-pod-laptop`、`kv/k8s/dynamic-runner-vm` 等路径，只挂载给 controller，
不进入 executor。Deployment 为 `replicas: 1` + `Recreate`，同一 registration 与 facade 不能由两个实例同时持有。

### 历史：webhook + NATS 架构（2026-10-05 前）

2026-09-16 查阅的项目 README 描述的 bootstrap 路径为：

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

[NATS](nats.md) 作为集群共享服务部署；当时只有 Dynamic Runner 消费它，2026-10-05 后已无消费者。

webhook → NATS 是尽快验证 Pod/VM 生命周期的 bootstrap 实现。当时的长期目标“controller 兼容
Gitea Runner 协议，直接注册、声明 labels、领取 task”已由上文的 runner 池成员架构取代。
当时的 VM 后端是 Cloud Hypervisor microVM（`microvm-runner-launch`），现行 VM 池为 OpenSandbox/Kata；
旧 homelab-infra 文档中的 `kind-microvm` 是更早的记录。

当时维护者提供的阶段（2026-09-16）：动态 `[self-hosted, pod]` 上线测试（并发 4），`[self-hosted, vm]` 正在工作（并发 1），
纯 `self-hosted` 旧常驻 runner 准备退役（已于 2026-09-21 删除，见下文）。

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

## 基础设施归属与运行凭据

- `jwt-broker` 是早期共享 Kubernetes runner 的过渡实验；目标架构不部署它。
- runner registration、facade capability key 等凭据用于执行平台本身运作（现行路径见上文），
  与 workflow 自行请求的下游业务 token 分开管理，不复制进知识库。旧架构的 NATS 密码与 webhook secret 已随之不再使用。
- registration token 不写入 seed image；worker 通过单次 nonce endpoint 交给 guest。
- base image 不携带 runner identity、registration token、SSH 密码或 host key。
- runner 软件保存在本项目；Kubernetes、OpenBao、LXC、bridge 和容量配置保留在 homelab-infra。
- homelab-infra 的 `platform/gitea-runner/` 是此前的常驻 runner，已于 2026-09-21 删除
  （[bb24c76](https://git.ddupan.top/panxiao81/homelab-infra/commit/bb24c76704a018df967bfe007539fde9c9b2a46e)）。

## 继续阅读

- [项目 README](https://git.ddupan.top/panxiao81/gitea-dynamic-runner/src/branch/main/README.md)：接口、组件、开发命令与安全边界。
- [设计原则](https://git.ddupan.top/panxiao81/gitea-dynamic-runner/src/branch/main/docs/design-principles.md)：README 指向的完整设计约束。
- [Runner 协议路线](https://git.ddupan.top/panxiao81/gitea-dynamic-runner/src/branch/main/docs/runner-protocol-roadmap.md)：README 指向的长期调度路线与迁移边界。
- [SPIFFE/SPIRE](spire.md)：统一机器身份的设计定位与阶段依据。
- [`ci-actions@v1`](https://git.ddupan.top/panxiao81/ci-actions/src/tag/v1)：workflow 可复用的 SPIFFE/OpenBao 登录与 Nexus 配置 Action。

实际启用范围、workflow 验收、排障及消息队列约定在项目文档中维护。
开发中的变化直接以项目文档为准，知识库不另列“启用范围待核实”任务。
