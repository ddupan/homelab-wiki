# 架构约束索引

审阅日期：2026-11-18。以下是现有仓库明确记录的约束摘要；Ayatori 条目来自其独立项目的
已接受设计，其余来源路径相对于 homelab-infra。修改时必须读原文和对应代码，新出现的差异
先向维护者确认；[首轮状态对齐](../verification.md)已完成。

| 约束 | 原因与边界 | 来源 |
|---|---|---|
| Ayatori 公共 infra 与领域 repository 分离 | 连接、认证和官方读写客户端统一装配；领域保留对象映射和业务语义，不引入万能仓储 | [Controller 公共基础设施边界](ayatori-control-plane.md#controller-公共基础设施边界) |
| 新增监控配置优先使用 ServiceMonitor、PodMonitor、PrometheusRule | VictoriaMetrics Operator 负责转换，避免同一目标/规则维护两套声明；历史 VM 配置按需另行迁移 | 维护者 2026-09-25 明确要求；[基础监控运维](../guides/monitoring-foundation.md) |
| Ayatori 复用 Kubernetes API machinery，不复用其容器编排产品边界 | kube-apiserver/etcd 提供 API、watch、RBAC 与状态协调；领域调度、生命周期、恢复和 GC 属于 Ayatori controllers；Kubernetes workload 只是可替换 backend | [Ayatori 控制面边界](ayatori-control-plane.md) |
| Kubernetes 内置资源不绑定上游实现组件 | 可由 Ayatori Agent/controller 实现和消费 Node、Lease 等 API；使用 Node 不推导必须部署 kubelet、Pod 或 kube-scheduler | [Ayatori 控制面边界](ayatori-control-plane.md) |
| Ayatori 只为已验证的管理缺口新增北向资源 | 当前优先 Database、LoadBalancer、Bucket/Object Storage；VM 价值已确认但南向较重；Run 是内部切片，KaaS 按需，FaaS/PaaS 默认不做 | [Ayatori 控制面边界](ayatori-control-plane.md) |
| Ayatori Compute 复用 Node/Lease API，但不引入 Kubernetes workload plane | Compute Agent 实现 Node 状态；libvirt 是长期候选主路径，PVE 是 brownfield 过渡；Kata microVM 属于 Sandbox backend | [Ayatori 控制面边界](ayatori-control-plane.md) |
| Database 采用独立资源与用户申请分离 | Instance → Database → Tenant；Retain 保留资源并人工回收，显式导入，不维护 PG registry；替代旧所有权持久化合同 | [DBaaS 设计修订](../services/postgresql-tenant-operator.md#当前资源模型2026-09-24-已确认) |
| Samba AD、OCI、Proxmox 优先 IaC，以代码为准 | Ansible/Terraform 声明及任务优先于旧 README；声明不等于已验证部署 | 维护者于 2026-09-16 明确、各服务使用指南 |
| 新建 etcd 按全 homelab 共享基础设施设计，PostgreSQL 为首个消费者 | 替代 PostgreSQL 专属 DCS 定位，避免每个服务重复部署；三成员及消费者 RBAC 隔离已部署，不迁移现有 k3s datastore | [共享 etcd](../services/shared-etcd.md)，维护者于 2026-09-25 明确 |
| laptop 的 Incus 与 libvirt 并存，k8s 保持裸机 | 既有 VM 留在 libvirt，新 Linux VM/LXC 可用 Incus；已接入 Web/OIDC，并准备两个 Ayatori 基础 LXC；不引入 Incus SDN/LB，不接管既有宿主网络；etcd/PostgreSQL 由各自服务管理 | [Incus](../services/incus.md)，维护者于 2026-09-25 确认 |
| 服务独立部署，Terraform root/state 按服务隔离 | 避免认证和变更影响范围绑在一起 | `AGENTS.md`、`CLAUDE.md` |
| OpenBao 恢复不能依赖 k3s 或读取自己内部的恢复凭据 | 先恢复信任根，再恢复消费者 | `infrastructure/openbao/README.md`、`CLAUDE.md` |
| Terraform 管 API 配置，Ansible 管主机及不能安全纳管的密钥材料 | 不可读回秘密和根密钥不能靠反复重建实现收敛 | `infrastructure/openbao/README.md` |
| LAN HTTP 入口为 Envoy Gateway；新增服务核对 parentRefs、DNS 和认证 | 不直接套用 archive 中的 Gateway 示例 | `platform/envoy-gateway/README.md`、`AGENTS.md` |
| 人类认证由 iam-login 提供（AD 密码 + Passkey，组映射到 `platform-admins`）；workload 身份由 SPIRE 提供 | 旧规则（2026-09-25）：Samba AD / Authelia 为主，Hydra 为 Gitea 的实验入口。新规则：Hydra 2026-10-05、Authelia 2026-10-11 退役，全部应用为 iam-login 的 OIDC client；Gateway 没有 forward-auth，无登录的应用用 Envoy `SecurityPolicy` 对接 iam-login | [iam-login](../services/iam-login.md)、[发布新服务](../guides/publish-service.md)、[SPIRE](../services/spire.md) |
| SPIFFE 提供跨基础设施的统一机器身份入口，替代 workload-sts 统一 IAM 平台方案 | 服务信任 SPIFFE 身份、签发自己的 token 并维护自身权限；非 Kubernetes 身份不依赖 Kubernetes ServiceAccount，优先复用服务现有接入机制 | [核心设计与取舍](../services/spire.md#核心设计与取舍)，维护者于 2026-09-16 补充 |
| 已由 Flux 接管的资源通过 Git 修改；brownfield 不全局开启 prune | 防止漂移回滚与误删；未接管资源不能假定受 Flux 管理 | `clusters/homelab/README.md` |
| DNS 记录随创建它所命名对象的代码维护；只有无代码创建的主机进 `dns/terraform/hosts.tf` | 新增（2026-10-09 起）：不再集中到一份记录文件，服务名由 external-dns 从 HTTPRoute 发布到 `lab.ddupan.top` | [LAN DNS](../services/lan-dns.md)、`infrastructure/dns/README.md` |
| DNS 各视图保留权威边界；只管理明确声明的 RRset | 不清理 Samba 自动维护的域记录；LAN 现状按维护者说明对齐，旧源码文档待同步 | `infrastructure/dns/README.md`、[LAN DNS](../services/lan-dns.md) |
| 关键服务 DNS 应容忍单 DC 故障；完整 AD HA 不是前置条件 | 2026-09-30 已接受，维护者 2026-11-18 说明仍在进行中；备用需独立提供受保护记录并跨宿主故障域，保留 AD 动态记录所有权；冷启动和缓存过期也须通过验收 | [LAN DNS](../services/lan-dns.md)、[事故报告](../incidents/2026-09-30-dc-dns-openbao.md) |
| DHCP 下发主 DNS Blocky、副 DNS 路由器；Blocky 上游为路由器 | 路由器同时承担上游与客户端备用角色；Samba AD 保留域 DNS 职责，不能把所有条件转发合并成一条普通上游 | [LAN DNS](../services/lan-dns.md)，维护者于 2026-09-16 说明 |
| vyos-rtr 的 CLI 配置只有一个写入方 `vyos_router`，受管路径以 `match: enforce` 整体收敛 | 新规则（2026-11-18）：原先两个项目四个 play 各自追加 `set` 行，删不掉旧值，各自维护的归属范围一旦重叠就会互删；合并后模板即受管路径的全部事实。不得新增第二个写入方；不得把机器自生成的内容（wg42 私钥、login、hw-id）纳入受管路径 | [VyOS 路由器](../services/vyos-router.md)、homelab-infra #830 |
| Docker 地址池不得与 DN42 的 172.20.0.0/14 重叠 | 本地直连路由会干扰 DN42；已有网络不自动改地址 | `infrastructure/docker/README.md` |
| 地址规划只在 Git（`infrastructure/network/ipam.yml`），已用地址以 DNS 为准；不引入 UI 权威数据 | 旧规则：NetBox 为评估、拓扑由 Git 管理。新规则：NetBox 2026-10-04 下线，原因是它只是无人阅读的派生镜像且对单节点过重 | [NetBox（已退役）](../services/netbox.md)、homelab-infra `CLAUDE.md` |
| 实例级 runner 只运行可信 workflow | 旧规则针对 privileged DinD 常驻 runner，它已于 2026-09-21 删除；动态 runner 池同样是实例级共享，仍不能视为不可信任务的隔离边界 | [Dynamic Runner](../services/gitea-dynamic-runner.md) |
| 每个动态 Pod/VM 应能独立取得自身 SPIFFE 身份；runner 只提供执行环境 | 登录目标、audience、token 交换及业务凭据生命周期由 workflow 决定；服务自行维护权限 | [Dynamic Runner 设计原则](../services/gitea-dynamic-runner.md)，维护者于 2026-09-16 明确 |
| NATS 是集群共享消息服务，原生以 Account 隔离租户；2026-10-05 起缩容为 0、当前无消费者（Dynamic Runner 已移除 NATS 依赖），恢复启用时沿用此约束 | 不把跨 Account 的名称当作全局冲突；runner 所属 Account 内的 durable 等业务约定由其项目文档维护 | [NATS](../services/nats.md)，维护者于 2026-09-16 说明 |
| zot 匿名入口只读；鉴权入口必须按具体身份授权 | 能认证不代表可以推送；不得给整个 trust domain 写权限 | `apps/zot/README.md` |

通用变更约束：先做适用的 plan/check/diff，再操作现场；不将凭据和 Terraform state
写入知识库；不更新 homelab-infra 的冻结 `CHANGELOG.md`。

## 待评估草案

[十万日元以内混合存储草案](hybrid-storage-draft.md)（2026-09-27，draft）评估单机
Ceph SSD/HDD 分池、千兆起步与二手 PC。预算与方向来自维护者讨论，尚未形成已验证的
采购清单，未部署或替代现有存储；备份与恢复优先于跨主机高可用。

[独立 IAM 与 agent 身份草案](independent-iam-draft.md)（2026-09-25，draft）提出以 Hydra
解耦认证与签发，通过 OIDC 接入人类、machine 和 agent，并作为 Ayatori 的独立外部依赖。
完整方案仍为草案。2026-09-25 已按维护者要求先实施人类登录 PoC，上表显式记录其有限
变更；SPIFFE、agent 动态授权、组模型及 DNS 迁移未随之实施。
