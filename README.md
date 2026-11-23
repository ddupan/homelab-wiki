# Homelab 知识库

人和 AI 共用的 Markdown 知识库：了解当前环境、使用服务、遵守架构约束，以及接续尚未完成的工作。

## 从这里开始

- [SOP 索引](sop/index.md)：出了状况或要做运维操作时，按步骤处理。
- [按任务查找文档](guides/task-index.md)：接入服务、写 CI、查日志、取秘密或接续 AI 任务。
- [服务总览](services/index.md)：组件、用途、入口和状态依据。
- [发布新服务](guides/publish-service.md)：LAN DNS、证书、HTTPRoute、认证与 GitOps。
- [架构约束](architecture/constraints.md)：修改环境前必须遵守的设计。
- [文档维护规则](CONTRIBUTING.md)、[服务模板](templates/service.md)、[SOP 模板](templates/sop.md)、[AI 工作入口](AGENTS.md)：如何共同维护知识。
- [首轮状态对齐记录](verification.md)：已完成的澄清与历史处置。
- [文档完善清单](documentation-backlog.md)：已补指南与暂缓事项。

设计历史与范围外项目见[workload-sts](architecture/workload-sts-history.md)、
[旧监控栈](services/victoriametrics-legacy.md)及[外部消费者](services/external-consumers.md)。

## 以什么为准

**[homelab-infra](https://git.ddupan.top/panxiao81/homelab-infra) 的 main 就是当前环境**（维护者 2026-11-23 约定）。
本库说明怎么使用和维护它；与代码不一致时以代码为准，并回来修正对应页面。服务表中的来源路径均相对于该仓库。
页面依赖的源码路径列在 frontmatter `watch` 中，源码变化后由每周的过时检查提醒复核。

`last_verified` 是最近一次现场验证的日期，没有就为 null；代码存在不代表服务此刻健康。
历史上的盘点与状态对齐记录见[首轮状态对齐记录](verification.md)。

## 内容归属

本库保存全局导航、跨服务设计与约束、面向使用者的指南及跨服务 runbook。
[e5renew](services/e5renew.md)、[research-auto](services/research-auto.md) 由 homelab 的 Flux 部署，本库只记部署与依赖，
应用本身的文档留在各自仓库。
紧贴实现的部署参数与操作细节继续保存在源码仓库的 README/runbook，双方以链接关联，
不复制维护两份事实。单次变更由 commit/PR 记录，历史计划不能代替现状说明。

使用标准 Markdown、普通相对链接和 YAML frontmatter。可将仓库直接作为 Obsidian vault
打开；核心信息不依赖插件、动态查询或嵌入内容才能理解。网页展示由 Backstage TechDocs
提供：push 到 main 后 `techdocs` workflow 生成站点并发布到共享 S3（见
[Backstage](services/backstage.md#目录与文档发布)），文档仓库本身不依赖 Backstage 可用。
