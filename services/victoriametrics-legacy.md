---
title: 旧 VictoriaMetrics Compose 栈
lifecycle: retired
evidence: live-verified
last_reviewed: 2026-09-16
last_verified: 2026-09-16
sources:
  - 维护者提供的 Kubernetes 完整可观测性栈替代目标
  - 2026-09-16 本机 Docker 容器、卷及文件元数据只读检查
  - 2026-09-16 monitoring namespace 的资源状态只读检查
---

# 旧 VictoriaMetrics Compose 栈

**旧运行栈已停用，历史数据卷仍保留。数据是否已迁移、是否需要长期保留尚未确认。**
这里的 retired 只描述旧 Compose 运行栈，不代表旧数据已获准删除。

维护者最初的目标是以 Kubernetes 内的完整可观测性栈替代它，以便集成其他服务。
2026-09-16 经维护者授权进行了有限只读检查，没有启动、停止、迁移或删除任何服务或数据。

## 检查结果

- `docker ps -a` 按 Compose project `victoriametrics` 筛选，没有容器；
  按 VictoriaMetrics、vmagent、vmalert、Grafana、Alertmanager 名称及镜像筛选也没有旧栈容器。
- 三个 Docker 卷仍存在，按卷筛选所有容器，没有发现引用它们的容器。
- Kubernetes `monitoring` 中 VMSingle/main 和 VMAgent/main 状态为 operational；
  Grafana、指标、日志、追踪及相关采集组件的 Pod 处于 Running。
- 新栈的 Grafana、VMSingle、VLSingle、VTSingle PVC 均为 Bound。
  这些资源状态不等于已经验证新旧数据一致或完成全部端到端采集验收。

| 旧 Docker 卷 | 磁盘占用（du -sh） | 保留内容 |
|---|---|---|
| `victoriametrics_vmdata` | 131 MiB | data、indexdb、metadata、cache 等；data/small 和 data/big 下有 `2026_02`、`2026_03` 目录 |
| `victoriametrics_vmagentdata` | 4 KiB | 本次查看目录为空 |
| `victoriametrics_grafanadata` | 45 MiB | `grafana.db`（1,536,000 字节）及 plugins、dashboards 等目录 |

元数据统计确认 `data/` 下有 247 个文件，逻辑大小合计 118,467,976 字节；
`indexdb/` 下有 173 个文件，逻辑大小合计 11,864,570 字节。

本机卷路径为 `/var/lib/docker/volumes/<卷名>/_data`。
旧 `grafana.db` 文件修改时间为 2026-03-09 08:30:18 UTC。
目录名和文件修改时间仅是文件系统证据，不能据此断言样本的准确时间范围、完整性或可查询性。

## 如何理解当前状态

旧卷确有保留内容，不能按“只剩 Compose 配置”处理。
本机没有运行中的旧栈容器，本轮也没有可直接查询的旧实例；未为检查数据而启动旧实例。
没有读取 Grafana 数据库内容或凭据，也没有执行历史样本查询。

下一步若需要保留、恢复或迁移历史数据，应先与维护者确定目标，再安排独立工作。
在此之前保留三个卷，不运行 `docker compose down -v` 或将它们纳入未使用卷清理。
旧数据当前没有容器引用，不能因此视为可安全删除。

## 文档与代码归属

- 旧 Compose 配置：homelab-infra `apps/victoriametrics/compose.yaml`。
- 新可观测性栈：homelab-infra `platform/observability/README.md`。
- 本次只同步知识库，未改动源码中的历史配置或执行退役清理。
