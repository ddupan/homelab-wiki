---
title: 旧 VictoriaMetrics Compose 栈（已清理）
lifecycle: retired
evidence: live-verified
last_reviewed: 2026-09-16
last_verified: 2026-09-16
sources:
  - 维护者于 2026-09-16 明确要求直接删除旧配置和全部旧数据卷
  - 2026-09-16 Docker 卷删除前后检查及 Kubernetes monitoring 状态检查
---

# 旧 VictoriaMetrics Compose 栈（已清理）

**旧配置与三个 Docker 数据卷已于 2026-09-16 删除，未备份、未迁移旧数据。**
维护者在了解保留数据情况后明确选择直接删除。新 Kubernetes 可观测性栈未做部署修改。

## 清理范围与结果

删除前，旧 Compose 栈已经没有容器；再次确认三个旧卷没有任何容器引用后，
按完整卷名逐个删除，并检查卷列表确认它们均不存在：

| 已删除卷 | 删除前内容 |
|---|---|
| `victoriametrics_vmdata` | 约 131 MiB，包含历史指标数据与索引 |
| `victoriametrics_vmagentdata` | 空目录，占用约 4 KiB |
| `victoriametrics_grafanadata` | 约 45 MiB，包含旧 grafana.db 和插件等 |

源码仓库 `apps/victoriametrics/` 下的 13 个受管文件已删除，平台文档和告警规则注释
中的旧路径引用已修正。旧配置可以从 Git 历史找回；不能通过 Git 恢复已删除的数据卷内容。
本次未创建任何数据备份。

基础设施清理已通过 [PR #73](https://git.ddupan.top/panxiao81/homelab-infra/pulls/73)
于 2026-09-16 16:05:33 UTC 合并到 main，合并提交为
[`9c64d31`](https://git.ddupan.top/panxiao81/homelab-infra/commit/9c64d31d3dea2ac2663170ca8125f03ac95cf0dd)。
PR 仅包含此次清理；源码工作区原有的其他修改未纳入。

## 清理后的检查

- Docker 中三个指定卷均不存在，旧配置目录已不存在。
- 新栈 VMSingle/main、VMAgent/main 仍为 operational。
- Grafana、VMSingle、VLSingle、VTSingle 的四个 PVC 均为 Bound。
- `platform/observability/metrics` 的 Kustomize 渲染通过。

这些检查确认清理范围及新栈资源状态，不宣称新旧历史数据完成迁移。
现役监控的维护入口为 homelab-infra `platform/observability/README.md`。
