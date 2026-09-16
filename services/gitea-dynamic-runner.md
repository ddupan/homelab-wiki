---
title: Gitea Dynamic Runner
lifecycle: experimental
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/gitea-dynamic-runner/src/branch/main/README.md
---

# Gitea Dynamic Runner

原名 `gitea-microvm-runner`，现为
[gitea-dynamic-runner](https://git.ddupan.top/panxiao81/gitea-dynamic-runner)。
它为 Gitea Actions 按需创建一次性执行环境，支持 Kubernetes Pod 和 Cloud Hypervisor
microVM；每个环境只执行一个 job，结束后销毁环境及本地状态。

更名由维护者提供；以下内容依据 2026-09-16 查阅的项目 README。
README 描述了 bootstrap 实现与后续路线，没有明确记录当前部署范围或端到端上线验收。
本页因此按试验阶段记录，不表示现场 runner 已注册或下面的 labels 已可调度；本轮未查询现场。

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
| `pod` | 动态 Kubernetes privileged Pod；workflow 使用 host executor | Docker、BuildKit、kind 等工具由 pipeline 按需 setup；这里的 host executor 指 Pod 内执行环境 |
| `vm` | 动态 Cloud Hypervisor microVM | 每个任务创建独立 COW disk、seed 和 TAP，guest runner 执行一个 job 后关机并清理 |

两种接口不能仅凭“环境一次性”就认定具有相同的隔离边界。
接入前需要结合项目设计约束和实际部署确认任务的信任范围。
旧 homelab-infra 文档中的 `kind-microvm` 是早期记录，不作为本项目当前 workflow 接口。

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
同一 runner label 的 worker 共享同一个 durable consumer，通过增加 worker 或 capacity 扩容。

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

后续需补充实际启用范围、workflow 验收示例和失败任务排障入口；查询前先向维护者对齐动态工作。
