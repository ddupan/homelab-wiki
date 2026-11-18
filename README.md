# Homelab 知识库

人和 AI 共用的 Markdown 知识库：了解当前环境、使用服务、遵守架构约束，以及接续尚未完成的工作。

## 从这里开始

- [SOP 索引](sop/index.md)：出了状况或要做运维操作时，按步骤处理。
- [按任务查找文档](guides/task-index.md)：接入服务、写 CI、查日志、取秘密或接续 AI 任务。
- [服务总览](services/index.md)：组件、用途、入口和状态依据。
- [发布新服务](guides/publish-service.md)：LAN DNS、证书、HTTPRoute、认证与 GitOps。
- [架构约束](architecture/constraints.md)：修改环境前必须遵守的设计。
- [来源追溯](sources.md)：固定源码版本，以及与工作区的差异。
- [文档维护规则](CONTRIBUTING.md)、[服务模板](templates/service.md)、[SOP 模板](templates/sop.md)、[AI 工作入口](AGENTS.md)：如何共同维护知识。
- [首轮状态对齐记录](verification.md)：已完成的澄清与历史处置。
- [文档完善清单](documentation-backlog.md)：已补指南与暂缓事项。

设计历史与范围外项目见[workload-sts](architecture/workload-sts-history.md)、
[旧监控栈](services/victoriametrics-legacy.md)及[外部消费者](services/external-consumers.md)。

## 当前证据边界

首轮盘点日期为 **2026-09-16**，依据 `/home/panxiao81/services` 工作区，基线 commit 为
`ebe0ec154dab557598075b5cf6d3629c3c23fe2a`。该工作区包含未提交修改和未跟踪文件。
后续按维护者提供的线索补读了 SPIFFE/SPIRE #34 与 runbook、workload-sts 归档决策、
PostgreSQL Tenant Operator 的 README 与架构文档，以及 Gitea Dynamic Runner README。
具体来源和查阅范围见各页；后续使用指南已按对应源码和上游接口文档逐项补充。
未补充的状态仍以初轮证据为限；来源文件与已提交版本的比较见[来源追溯](sources.md)。
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
打开；核心信息不依赖插件、动态查询或嵌入内容才能理解。网页展示由 Backstage TechDocs
提供：push 到 main 后 `techdocs` workflow 生成站点并发布到共享 S3（见
[Backstage](services/backstage.md#目录与文档发布)），文档仓库本身不依赖 Backstage 可用。
