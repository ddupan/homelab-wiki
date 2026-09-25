---
title: 基础监控与告警运维
last_reviewed: 2026-09-25
---

# 基础监控与告警运维

第一批补齐 Kubernetes 状态、主机/ZFS 和通知链路；业务数据库、备份、外部探测等
后续范围见 [覆盖计划](monitoring-coverage.md)。本页的规则检查不等于所有服务健康。

## 声明与归属

维护者于 2026-09-25 明确：新增监控配置优先使用 Prometheus Operator 的
`ServiceMonitor`、`PodMonitor`、`PrometheusRule`。VictoriaMetrics Operator 负责转换为
VMServiceScrape、VMPodScrape、VMRule，vmagent/vmalert 继续负责采集与规则执行。
不要再为同一个新目标/规则手工维护一份 VM 对象；已有历史 VM 配置按需求单独迁移。

- kube-state-metrics：Flux HelmRelease，chart `8.5.0` / app `2.20.0`，适配本集群 Kubernetes 1.36。
- KSM 的 ServiceMonitor 使用 `honorLabels: true`，保留被观测对象的 namespace/pod 等标签。
  :8080 提供对象指标，:8081 提供 exporter 自身指标；job 均为 `kube-state-metrics`。
- collector/RBAC 限于本批需要的 nodes、pods、deployments、statefulsets、daemonsets、
  PVC/PV、jobs/cronjobs、namespaces，只读 list/watch，没有启用 secrets collector。
- NATS 沿用其 Helm 管理的 PodMonitor，转换后的 `nats/nats` VMPodScrape 抓取 :7777，job 为 `nats/nats`。
- Operator HelmRelease 依赖 `prometheus-operator-crds`；KSM 同时依赖两者。
  先确保 CRD Ready，再启动依赖 CRD 的转换器和消费者。
- 源码：[基础补齐 PR #149](https://git.ddupan.top/panxiao81/homelab-infra/pulls/149)。
  三份新增规则位于 `platform/observability/metrics/rules/{kubernetes-health,host-health,monitoring-delivery}.yaml`。
  PrometheusRule 声明切换见 [PR #151](https://git.ddupan.top/panxiao81/homelab-infra/pulls/151)，
  Flux 已应用 `e8e7bd4b203def4123658a4d02a1d92a854005fc`。

## 21 条规则的范围

| 组 | 规则与持续时间 | 严重性 |
|---|---|---|
| Kubernetes（11） | NodeNotReady 5m；Memory/Disk/PID Pressure 5m | 节点未就绪 critical，压力 warning |
| Kubernetes（续） | CrashLoop 10m；15 分钟内重启 >3 次持续 5m；近期 OOM 重启 1m；Pod Pending 15m | warning |
| Kubernetes（续） | Deployment/StatefulSet/DaemonSet 可用副本不足 10m；PVC Pending 15m；Job Failed condition 5m | warning |
| 主机（5） | 可用内存 <10% 持续 10m；磁盘可用空间/inode <10% 持续 15m | warning |
| 主机（续） | 文件系统只读 5m；ZFS 池非 online 的状态值为 1 持续 5m | critical |
| 采集（3） | KSM、node-exporter、NATS target down 或整个 job 消失持续 5m | 前两项 critical，NATS warning |
| 通知（2） | Telegram 失败计数最近 5 分钟增加并持续 1m；Alertmanager 配置加载失败 5m | critical |

主机规则只用 `job="node-exporter"`，避免旧 docker-hosts 重复样本。
磁盘规则排除 tmpfs/devtmpfs/overlay/squashfs/nsfs/fuse 和临时挂载路径；inode 总数为零不报警。
OOM 同时要求近期 restart counter 增加，避免历史终止原因持续报警。
Deployment 以声明副本为准，缩容到零不触发。

本批没有增加主机 CPU/Swap/IO 告警、NATS JetStream 业务规则、数据库/备份或外部探测。
job 完全消失使用 absent(up) 检查，但未建立每个预期主机/成员的独立清单，不能保证发现
同一个 job 中少了一个成员；此类预期拓扑检测后续再补。

## 通知、静默与抑制

warning/critical 及恢复消息沿用 [Telegram 路由](../services/grafana.md#telegram-告警接入)。
新规则 annotations 中包含本 runbook 链接。
告警 Source 的指标查询入口与 Grafana 中的 Alertmanager 静默管理入口见
[从告警进入 Grafana](../services/grafana.md#从告警进入-grafana)。
同一 namespace/pod/container 的 `KubePodCrashLooping` 只抑制 `KubePodFrequentRestarts`，
不抑制 OOM，也不静默整个 namespace。工作负载副本不足仍独立可见。

维护时在 Alertmanager 为明确标签创建有截止时间和原因的 silence；不要把维护中的
etcd、SPIRE 或 Backstage 直接写成永久排除规则。结束维护后核对 silence 到期和目标健康。

Telegram 完全不可达时，发送失败告警也无法依靠同一渠道送达。该规则有助于留存和
恢复后通知，不能替代集群外心跳或第二渠道。发送失败时直接检查 Alertmanager/Grafana。

## 接入或升级后如何验收

1. 确认 Flux HelmRelease Ready，原生 ServiceMonitor/PodMonitor/PrometheusRule 存在。
2. 确认转换出的 VM 对象存在、内容同步；不要仅凭原生 CR 已创建判定成功。
3. 在 vmagent `/api/v1/targets` 确认 up、最近采集时间和样本数；VictoriaMetrics 即时查询
   验证 `up{job="kube-state-metrics"}`、`up{job="nats/nats"}` 和所需指标当前有值。
4. 在 vmalert `/api/v1/rules` 核对规则数量、lastError 和依赖样本。
   没有失败 Job 或 OOM 时条件指标可能不存在，不能把这种空结果直接当作采集失败。
5. 变更规则时从源码运行 `bash platform/observability/metrics/tests/check-rules.sh`；
   依赖 Python 3、PyYAML、promtool（本次验证版本 3.5.0）。该脚本直接读取三份规则的 spec.groups，
   生成临时文件校验，不维护第二份规则。8 组测试覆盖阈值持续时间、缺失目标和常见噪声边界。
6. 经维护者授权发送临时 canary，验证触发与恢复后删除测试规则，恢复正式规则总数。
   不通过制造真实 OOM、磁盘满或破坏 Telegram token 来做验收。

## NATS 转换故障经验

NATS 已有 exporter 和 PodMonitor，但 Operator 自 7 月启动，PodMonitor CRD 到 9 月才安装。
本次滚动重启 Operator 后，日志记录启动 PodMonitor controller 并创建 `VMPodScrape=nats/nats`，
之后 target up 且 nats_* 指标入库。NATS 本身没有重启。

遇到同类问题先检查原生 CR、转换对象、转换器日志、watch/RBAC 和 CRD 安装时间；
不能直接另建同目标 VM scrape 来掩盖转换链路问题。必要重启只针对 Operator，
先确认当前无升级/恢复操作，重启后验证对象生成和采集。

## 本次验证边界

2026-09-25，KSM 两个端点及 NATS 均 up，KSM 约 5,300 条对象样本和 75 条自身样本，
可读到 27 个 workload namespace 的容器重启指标。NATS 有约 187 条采集样本。
正式规则从 47 增为 68，当前规则评估无错误；8 组离线测试、Helm/Kustomize 渲染和服务端 dry-run 通过。
canary 触发已由维护者确认收到；规则恢复后 Telegram 发送计数从 11 增至 12，
失败计数仍为 0，Alertmanager 无残留 canary，测试 VMRule 已删除。恢复消息未单独取得收件端确认。
三份 PrometheusRule 的转换内容一致（仅 VMRule 补默认空 record 字段），vmalert 最终仅有 68 条正式规则，未重复评估。
这些数量是验收快照，不是容量承诺或持续健康结论。正在调整的 etcd 不在本批修复范围。
