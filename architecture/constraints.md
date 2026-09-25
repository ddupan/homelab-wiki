# 架构约束索引

审阅日期：2026-09-25。以下是现有仓库明确记录的约束摘要；Ayatori 条目来自其独立项目的
已接受设计，其余来源路径相对于 homelab-infra。修改时必须读原文和对应代码，新出现的差异
先向维护者确认；[首轮状态对齐](../verification.md)已完成。

| 约束 | 原因与边界 | 来源 |
|---|---|---|
| Ayatori 复用 Kubernetes API machinery，不复用其容器编排产品边界 | kube-apiserver/etcd 提供 API、watch、RBAC 与状态协调；领域调度、生命周期、恢复和 GC 属于 Ayatori controllers；Kubernetes workload 只是可替换 backend | [Ayatori 控制面边界](ayatori-control-plane.md) |
| Kubernetes 内置资源不绑定上游实现组件 | 可由 Ayatori Agent/controller 实现和消费 Node、Lease 等 API；使用 Node 不推导必须部署 kubelet、Pod 或 kube-scheduler | [Ayatori 控制面边界](ayatori-control-plane.md) |
| Ayatori 只为已验证的管理缺口新增北向资源 | 当前优先 Database、LoadBalancer、Bucket/Object Storage；VM 价值已确认但南向较重；Run 是内部切片，KaaS 按需，FaaS/PaaS 默认不做 | [Ayatori 控制面边界](ayatori-control-plane.md) |
| Ayatori Compute 复用 Node/Lease API，但不引入 Kubernetes workload plane | Compute Agent 实现 Node 状态；libvirt 是长期候选主路径，PVE 是 brownfield 过渡；Kata microVM 属于 Sandbox backend | [Ayatori 控制面边界](ayatori-control-plane.md) |
| Database 采用独立资源与用户申请分离 | Instance → Database → Tenant；Retain 保留资源并人工回收，显式导入，不维护 PG registry；替代旧所有权持久化合同 | [DBaaS 设计修订](../services/postgresql-tenant-operator.md#当前资源模型2026-09-24-已确认) |
| Samba AD、OCI、Proxmox 优先 IaC，以代码为准 | Ansible/Terraform 声明及任务优先于旧 README；声明不等于已验证部署 | 维护者于 2026-09-16 明确、各服务使用指南 |
| 服务独立部署，Terraform root/state 按服务隔离 | 避免认证和变更影响范围绑在一起 | `AGENTS.md`、`CLAUDE.md` |
| OpenBao 恢复不能依赖 k3s 或读取自己内部的恢复凭据 | 先恢复信任根，再恢复消费者 | `infrastructure/openbao/README.md`、`CLAUDE.md` |
| Terraform 管 API 配置，Ansible 管主机及不能安全纳管的密钥材料 | 不可读回秘密和根密钥不能靠反复重建实现收敛 | `infrastructure/openbao/README.md` |
| LAN HTTP 入口为 Envoy Gateway；新增服务核对 parentRefs、DNS 和认证 | 不直接套用 archive 中的 Gateway 示例 | `platform/envoy-gateway/README.md`、`AGENTS.md` |
| 人类认证仍由 Samba AD / Authelia 提供；Hydra 作为 Gitea 的实验性签发入口，通过 OIDC 复用 Authelia；workload 身份由 SPIRE 提供 | 2026-09-25 第一轮人类 PoC 扩展了原单 broker 接入边界，未迁移主入口、机器身份或应用权限 | [Authelia](../services/authelia.md)、[Hydra PoC](../services/hydra.md)、[SPIRE](../services/spire.md) |
| SPIFFE 提供跨基础设施的统一机器身份入口，替代 workload-sts 统一 IAM 平台方案 | 服务信任 SPIFFE 身份、签发自己的 token 并维护自身权限；非 Kubernetes 身份不依赖 Kubernetes ServiceAccount，优先复用服务现有接入机制 | [核心设计与取舍](../services/spire.md#核心设计与取舍)，维护者于 2026-09-16 补充 |
| 已由 Flux 接管的资源通过 Git 修改；brownfield 不全局开启 prune | 防止漂移回滚与误删；未接管资源不能假定受 Flux 管理 | `clusters/homelab/README.md` |
| DNS 各视图保留权威边界；只管理明确声明的 RRset | 不清理 Samba 自动维护的域记录；LAN 现状按维护者说明对齐，旧源码文档待同步 | `infrastructure/dns/README.md`、[LAN DNS](../services/lan-dns.md) |
| DHCP 下发主 DNS Blocky、副 DNS 路由器；Blocky 上游为路由器 | 路由器同时承担上游与客户端备用角色；Samba AD 保留域 DNS 职责，不能把所有条件转发合并成一条普通上游 | [LAN DNS](../services/lan-dns.md)，维护者于 2026-09-16 说明 |
| Docker 地址池不得与 DN42 的 172.20.0.0/14 重叠 | 本地直连路由会干扰 DN42；已有网络不自动改地址 | `infrastructure/docker/README.md` |
| NetBox 目前是评估，拓扑由 Git 管理 | 不把网页编辑结果当作新的权威数据 | `apps/netbox/README.md`、`CLAUDE.md` |
| 现有 privileged DinD runner 只运行可信 workflow | 实例级 runner 不能视为不可信任务隔离边界 | `platform/gitea-runner/README.md` |
| 每个动态 Pod/VM 应能独立取得自身 SPIFFE 身份；runner 只提供执行环境 | 登录目标、audience、token 交换及业务凭据生命周期由 workflow 决定；服务自行维护权限 | [Dynamic Runner 设计原则](../services/gitea-dynamic-runner.md)，维护者于 2026-09-16 明确 |
| NATS 是集群共享消息服务，原生以 Account 隔离租户，目前仅 Dynamic Runner 消费 | 不把跨 Account 的名称当作全局冲突；runner 所属 Account 内的 durable 等业务约定由其项目文档维护 | [NATS](../services/nats.md)，维护者于 2026-09-16 说明 |
| zot 匿名入口只读；鉴权入口必须按具体身份授权 | 能认证不代表可以推送；不得给整个 trust domain 写权限 | `apps/zot/README.md` |

通用变更约束：先做适用的 plan/check/diff，再操作现场；不将凭据和 Terraform state
写入知识库；不更新 homelab-infra 的冻结 `CHANGELOG.md`。

## 待评估草案

[独立 IAM 与 agent 身份草案](independent-iam-draft.md)（2026-09-25，draft）提出以 Hydra
解耦认证与签发，通过 OIDC 接入人类、machine 和 agent，并作为 Ayatori 的独立外部依赖。
完整方案仍为草案。2026-09-25 已按维护者要求先实施人类登录 PoC，上表显式记录其有限
变更；SPIFFE、agent 动态授权、组模型及 DNS 迁移未随之实施。
