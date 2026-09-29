---
title: Ayatori 控制面边界
last_reviewed: 2026-09-29
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

## Controller 公共基础设施边界

2026-09-25 维护者确认：OpenBao 认证、客户端及 Kubernetes 读写访问是整个 controller 的
infra 能力，不属于第一个使用它们的 Database 领域。启动入口统一装配和注入；公共层不反向
依赖产品领域，也不为复用而增加全局注册中心或统一包装所有后端的 reader/writer。
优先使用官方 SDK 和 manager 已提供的接口；不同身份与权限范围仍须显式隔离。

领域维护业务值对象与规则，application 按消费方需要定义 repository 接口，adapter 负责
对象映射与后端访问。例如 Database 七键凭据、位置约束及冲突恢复不是通用 KV 规则，
也不应因接入 Bao 而把这些业务规则归入 adapter。此次修订纠正原实现把 Bao 认证放在
Database adapter 的归属，认证方式与部署位置约定不变。源码拆分由
[PR #13](https://git.ddupan.top/panxiao81/ayatori/pulls/13) 跟踪，2026-09-27 经维护者批准合并；
实现与详细约定见
[6b2808c 的总体架构](https://git.ddupan.top/panxiao81/ayatori/src/commit/6b2808ce91b03215f466746a15d0c3d7442bb9d4/docs/architecture/overview.md#进程内依赖边界)。

2026-09-27 维护者进一步确认采用 Wire 风格的显式构造器注入：当前规模由 bootstrap
集中手写装配，不引入运行时 IoC 容器或代码生成依赖。controller 接收装配完的用例，
不在 Reconcile 或注册过程中创建 adapter/use case。application 保留 I/O 编排、消费方
接口及并发快照；凭据值对象、准备资格和恢复规则归领域，Kubernetes Conditions 映射归
adapter。此约定用于纠正业务规则混入 application 及装配分散的问题，不要求把所有接口
和临时数据结构搬进领域。实现已随
[PR #15](https://git.ddupan.top/panxiao81/ayatori/pulls/15) 合并（`d71285a`），PR 三项 CI 均通过；具体边界与测试见
[7834cab 的总体架构](https://git.ddupan.top/panxiao81/ayatori/src/commit/7834cab/docs/architecture/overview.md#进程内依赖边界)；
不改变现有 API 或凭据协议，尚未部署。

## CI 验证约定

2026-09-24 维护者决定：全量验证自动在 PR 执行，main push 不再重复运行；保留手动入口。
直接推送 main 不会自动验证，常规变更仍应经 PR；基线有实质变化时需更新分支并重验，
不能把分支 head 的成功当成任何合并结果的成功。测试项目未减少，不修改分支保护设置。
配置与边界见 Ayatori
[f347ee5 的环境文档](https://git.ddupan.top/panxiao81/ayatori/src/commit/f347ee5292ecf39ac0ecbb21e162ee406d8ce382/docs/concepts/environments.md)，
已随 [PR #9](https://git.ddupan.top/panxiao81/ayatori/pulls/9) 合并 main；合并后未触发重复全量验证。
这不是整个 homelab 的统一 CI 策略。
