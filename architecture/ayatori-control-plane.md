---
title: Ayatori 控制面边界
last_reviewed: 2026-09-24
---

# Ayatori 控制面边界

Ayatori 是规划和早期实现中的 homelab 基础设施控制平面。它使用 kube-apiserver、etcd、CRD
和 Kubernetes API machinery 作为版本化 API 与状态协调平面，主要复用对象并发控制、
list/watch、informer、RBAC、admission、审计和 API 版本机制，而不是复用 Kubernetes 的容器
编排产品边界。

Ayatori controller-manager 负责领域资源的调度、生命周期、故障恢复、垃圾回收和后端收敛。
这部分职责近似 Kubernetes 的 controller-manager，但面向 VM、LB、数据库、对象存储、任务、
托管 Kubernetes 和人工操作等 Ayatori 领域。

Kubernetes workload 集群只是与 OpenSandbox、Proxmox 等并列的 backend/executor，可能位于
远端，也可能在某个部署 profile 中不存在。除 Flux、Ayatori controllers 等管理组件的部署外，
领域 API 不得默认依赖同集群 Pod、Job、Service、NetworkPolicy、namespace 共置或 owner
reference；跨后端能力必须由领域 API 和 adapter 契约明确表达。

Kubernetes 内置资源也只是可选择复用的 API contract，不绑定其传统实现组件。例如 Ayatori
可以让 Compute Agent 更新 `core/v1 Node` 和 Lease，并由自有 controller 调度 VM，而不部署
kubelet、Pod、CRI 或 kube-scheduler。每个复用资源都必须单独明确 producer、consumer、
ownership、采用字段和有意舍弃的上游语义。

当前选择继续使用 kube-apiserver + CRD。generic-apiserver 或聚合 API Server 不会替代领域
controller，只会让项目额外接管资源服务端、watch、RBAC、API 兼容和存储迁移责任。只有 CRD
或 kube-apiserver 的限制形成经过验证的阻碍时，才重新评估自建 API Server。

Ayatori 不按传统私有云产品目录建设。当前已确认的首要管理缺口是 Database、LoadBalancer 与
Bucket/Object Storage；VirtualMachine 同样具有明确价值，但需要组合 Proxmox API、节点受限
Agent/CLI 和人工任务。当前 Job controller 是控制循环与 adapter 的验证切片，长期只可能收敛为
内部 Run 能力，不构成 FaaS、Cloud Run 或应用托管承诺。KaaS 只有出现实际需求时才评估，不是
产品路线的必达终点。

Compute 方向已被记录但延后实施：选择性复用 `core/v1 Node` 与 Lease，由 Ayatori Compute Agent
实现节点状态并由自有 controller 调度，不引入 kubelet、Pod 或 kube-scheduler。长期 VM 主路径
可以是普通 Linux 节点上的 libvirt/QEMU；Proxmox 用于 brownfield adopt 和过渡。OpenSandbox/Kata
microVM 属于 Run/Sandbox 的隔离实现，不因此成为 VirtualMachine 资源。

Database 资源模型于 2026-09-24 明确采用官方 PV/PVC 的资源/申请分离模式：Instance 提供
管理入口，独立 Database 表示实际资源，Tenant 表示用户申请。Retain 保留资源对象，支持
人工导入和明确授权后的重新绑定；不维护 PostgreSQL ownership registry，不为创建结果不确定
提供自动认领保证。详见 [DBaaS 设计](../services/postgresql-tenant-operator.md#当前资源模型2026-09-24-已确认)。

新增 Kubernetes 资源生命周期前须核对官方设计方式，记录采用与偏离的语义；参考模式不意味着
部署对应上游组件，也不意味着复制全部字段与抽象。

详细设计以 Ayatori 仓库的
[ADR-0001](https://git.ddupan.top/panxiao81/ayatori/src/branch/main/docs/decisions/0001-kubernetes-api-machinery.md)
、[ADR-0006](https://git.ddupan.top/panxiao81/ayatori/src/branch/main/docs/decisions/0006-demand-driven-resource-scope.md)
和[总体架构](https://git.ddupan.top/panxiao81/ayatori/src/branch/main/docs/architecture/overview.md)为准。
本页记录跨 homelab 的稳定边界，不表示 Ayatori 已部署或达到生产可用状态。
