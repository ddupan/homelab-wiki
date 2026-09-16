# Homelab 知识库

人和 AI 共用的 Markdown 知识库：了解当前环境、使用服务、遵守架构约束，以及接续尚未完成的工作。

## 从这里开始

- [服务总览](services/index.md)：有什么、有什么用、在哪里、状态依据是什么。
- [待核实与文档缺口](verification.md)：互相矛盾的记录、缺少使用说明的服务、下一步核实方法。
- [架构约束](architecture/constraints.md)：修改环境前必须遵守的设计及原始依据。
- [文档维护规则](CONTRIBUTING.md)：人和 AI 如何共同维护知识。
- [服务文档模板](templates/service.md)：新服务必须同时提供使用说明。
- [AI 工作入口](AGENTS.md)：新上下文按任务查找资料。

## 当前证据边界

首轮盘点日期为 **2026-09-16**，依据 `/home/panxiao81/services` 工作区，基线 commit 为
`ebe0ec154dab557598075b5cf6d3629c3c23fe2a`。该工作区包含未提交修改和未跟踪文件。
本轮没有查询运行环境；“文档记录已部署”不等于今天已验证健康。
本库中的入口地址来自原有记录，也尚未逐一验证可达性。

基础设施源码仓库：[homelab-infra](https://git.ddupan.top/panxiao81/homelab-infra)。
服务表中的来源路径均相对于该仓库；尚未提交的来源可能只能在上述工作区找到。

## 内容归属

本库保存全局导航、跨服务设计与约束、面向使用者的指南及跨服务 runbook。
紧贴实现的部署参数与操作细节继续保存在源码仓库的 README/runbook，双方以链接关联，
不复制维护两份事实。单次变更由 commit/PR 记录，历史计划不能代替现状说明。

使用标准 Markdown、普通相对链接和 YAML frontmatter。可将仓库直接作为 Obsidian vault
打开；核心信息不依赖插件、动态查询或嵌入内容才能理解。尚未选择或部署网页展示层，
后续可接入 Backstage，文档仓库本身不依赖 Backstage 可用。
