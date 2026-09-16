# Homelab 知识库

人和 AI 共用的 Markdown 知识库：了解当前环境、使用服务、遵守架构约束，以及接续尚未完成的工作。

## 从这里开始

- [发布新服务](guides/publish-service.md)：串联 LAN DNS、证书、HTTPRoute、认证与 GitOps。
- [服务总览](services/index.md)：有什么、有什么用、在哪里、状态依据是什么。
- [Gitea / Actions 入门](services/gitea.md)：登录、创建仓库、运行第一个 CI 与选择 runner。
- [Grafana 使用指南](services/grafana.md)：内存看板、指标查询和日志搜索。
- [zot 使用指南](services/zot.md)：匿名拉取、SPIFFE 发布身份与仓库授权。
- [SeaweedFS 使用指南](services/seaweedfs.md)：S3 客户端接入、对象读写与存储边界。
- [OpenBao 使用指南](services/openbao.md)：日常登录、按权限取密与机器身份边界。
- [NetBox 使用指南](services/netbox.md)：浏览设备和 IPAM，按 Git 来源维护资产镜像。
- [SPIFFE/SPIRE](services/spire.md)：按 #34 整理的阶段状态、使用与 runbook 入口。
- [LiteLLM 网关](services/litellm-gateway.md)：模型 API 接入参数与请求示例。
- [Tailscale](services/tailscale.md)：远程客户端、子网路由与 Service 入口。
- [ps3netsrv](services/ps3netsrv.md) / [vlmcsd](services/vlmcsd.md)：客户端接入与故障入口。
- [Marker](services/marker.md) / [OpenViking](services/openviking.md)：文档转换与上下文检索。
- [SMTP relay](services/smtp-relay.md)：应用发信参数、测试与投递排障。
- [External Secrets](services/external-secrets.md)：应用秘密投射与更新流程。
- [OpenEBS](services/openebs.md)：PVC 申请、绑定和数据回收边界。
- [k3s DNS](services/k3s-dns.md)：Pod 解析、内部域分流与缓存规则。
- [共享 PostgreSQL 使用指南](services/shared-postgresql.md)：应用接入、连接示例与共享实例维护边界。
- [PostgreSQL Tenant Operator](services/postgresql-tenant-operator.md)：计划在共享 PostgreSQL 上提供的 DBaaS 中间层。
- [Gitea Dynamic Runner](services/gitea-dynamic-runner.md)：原 microVM runner，现支持 Pod/VM 两种一次性执行环境。
- [NATS](services/nats.md)：已部署的集群共享消息服务，目前仅 Dynamic Runner 消费。
- [旧 VictoriaMetrics 栈](services/victoriametrics-legacy.md)：旧运行栈、配置及数据卷已清理。
- [LAN DNS](services/lan-dns.md)：Blocky 主 DNS、路由器上游与备用、Samba AD 域 DNS 的现状。
- [Authelia](services/authelia.md)：active 的唯一主 OIDC broker 与登录入口。
- [首轮状态对齐记录](verification.md)：本轮已完成，没有开放的状态核实任务。
- [文档完善清单](documentation-backlog.md)：后续补充使用说明、同步旧文档和完善来源链接。
- [架构约束](architecture/constraints.md)：修改环境前必须遵守的设计及原始依据。
- [workload-sts 设计历史](architecture/workload-sts-history.md)：已归档的早期身份方案及 SPIRE 替代决策。
- [文档维护规则](CONTRIBUTING.md)：人和 AI 如何共同维护知识。
- [服务文档模板](templates/service.md)：新服务必须同时提供使用说明。
- [AI 工作入口](AGENTS.md)：新上下文按任务查找资料。

## 当前证据边界

首轮盘点日期为 **2026-09-16**，依据 `/home/panxiao81/services` 工作区，基线 commit 为
`ebe0ec154dab557598075b5cf6d3629c3c23fe2a`。该工作区包含未提交修改和未跟踪文件。
后续按维护者提供的线索补读了 SPIFFE/SPIRE #34 与 runbook、workload-sts 归档决策、
PostgreSQL Tenant Operator 的 README 与架构文档，以及 Gitea Dynamic Runner README。
具体来源和查阅范围见各页；其余条目仍以初轮工作区证据为限。
LAN DNS 已按维护者于 2026-09-16 提供的现状更新，未查询现场。
Authelia 同日由维护者明确为 active、唯一的主 OIDC broker，已同步到服务总览。
后续状态查询先向维护者确认动态工作与资料来源，授权范围内不重复询问。
初轮没有查询运行环境；后续对旧 VictoriaMetrics 栈做了维护者明确授权的有限只读检查，
随后按明确要求删除旧配置和数据卷，
检查范围和结果见对应页面。“文档记录已部署”不等于今天已验证健康。
本库中的入口地址来自原有记录，也尚未逐一验证可达性。

基础设施源码仓库：[homelab-infra](https://git.ddupan.top/panxiao81/homelab-infra)。
服务表中的来源路径均相对于该仓库；尚未提交的来源可能只能在上述工作区找到。

## 内容归属

本库保存全局导航、跨服务设计与约束、面向使用者的指南及跨服务 runbook。
e5renew、research-auto 是 GitHub 上的[外部消费者](services/external-consumers.md)，不属于
homelab 基础设施；本库不接管其应用文档或运行状态。
紧贴实现的部署参数与操作细节继续保存在源码仓库的 README/runbook，双方以链接关联，
不复制维护两份事实。单次变更由 commit/PR 记录，历史计划不能代替现状说明。

使用标准 Markdown、普通相对链接和 YAML frontmatter。可将仓库直接作为 Obsidian vault
打开；核心信息不依赖插件、动态查询或嵌入内容才能理解。尚未选择或部署网页展示层，
后续可接入 Backstage，文档仓库本身不依赖 Backstage 可用。
