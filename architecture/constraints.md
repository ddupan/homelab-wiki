# 架构约束索引

审阅日期：2026-09-16。以下是现有仓库明确记录的约束摘要，不是本轮新增的架构决策。
来源路径相对于 homelab-infra；修改时必须读原文和对应代码，新出现的差异先向维护者确认；[首轮状态对齐](../verification.md)已完成。

| 约束 | 原因与边界 | 来源 |
|---|---|---|
| 服务独立部署，Terraform root/state 按服务隔离 | 避免认证和变更影响范围绑在一起 | `AGENTS.md`、`CLAUDE.md` |
| OpenBao 恢复不能依赖 k3s 或读取自己内部的恢复凭据 | 先恢复信任根，再恢复消费者 | `infrastructure/openbao/README.md`、`CLAUDE.md` |
| Terraform 管 API 配置，Ansible 管主机及不能安全纳管的密钥材料 | 不可读回秘密和根密钥不能靠反复重建实现收敛 | `infrastructure/openbao/README.md` |
| LAN HTTP 入口为 Envoy Gateway；新增服务核对 parentRefs、DNS 和认证 | 不直接套用 archive 中的 Gateway 示例 | `platform/envoy-gateway/README.md`、`AGENTS.md` |
| 人类身份由 Samba AD / Authelia 提供，Authelia 是 active 的唯一主 OIDC broker；workload 身份由 SPIRE 提供 | 身份签发不等于资源授权；SPIRE 基础设施与最小 PoC 已完成，后续集成以 #34 为准 | [Authelia](../services/authelia.md)、[SPIRE 状态与依据](../services/spire.md) |
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
