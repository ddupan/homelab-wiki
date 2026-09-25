---
title: CNPG、NATS 与 SeaweedFS 监控
last_reviewed: 2026-09-25
---

# CNPG、NATS 与 SeaweedFS 监控

本批仅增加指标采集与 14 条 PrometheusRule 告警，数据库范围按维护者要求限于 CNPG。
共享 Patroni PostgreSQL 与 etcd 的变更由对应任务管理。

## 采集与规则

| 服务 | 采集与范围 | 告警 |
|---|---|---|
| CNPG shared-db/shared-postgresql | PodMonitor 抓取已有实例 :9187，job=cnpg | exporter/目标不可用 5m critical；PostgreSQL down 2m critical；SQL 采集错误 5m；连接使用率 >80% 10m；非 idle 事务超过 300s 持续 5m |
| NATS | 沿用 job=nats/nats | JetStream 服务端文件或内存容量 >80% 10m；10m 内慢消费者计数增加并持续 5m |
| SeaweedFS | ServiceMonitor 仅选择 master/filer/volume 三个服务的 :9327 | 各组件采集不可用 5m critical；volume 可用磁盘 <10% 10m；因磁盘不足限制写入 5m critical；5m 内写失败增加持续 2m |

CNPG 使用内置 exporter，不新增数据库账号、不改数据库实例配置、不执行业务写入。
连接数按 Pod 汇总数据库与用户，再除以同实例 max_connections；长事务排除普通 idle 连接。
当前单实例没有复制冗余，不添加必然无法满足的副本告警。本批没有建立或验证备份流程。

NATS 本批是服务端容量，不能代替 Account、stream 限额与 consumer pending/redelivery 监控。
当前 exporter 未输出这些 consumer 维度，后续需明确 exporter 开关与业务阈值再补。
慢消费者使用增量，历史累计值不持续触发。

SeaweedFS 排除 filer-client 的重复发现，组件分别使用 seaweedfs-master/filer/volume job。
只把 isDiskSpaceLow 视为这条只读故障，避免满卷轮转或主动只读造成误报。
这些指标不证明 S3 请求端到端成功，也不证明副本和异机备份可恢复。

## 使用与故障定位

在 [Grafana Explore](https://grafana.ad.ddupan.top/explore) 选择 VictoriaMetrics，可查询：

```promql
cnpg_collector_up{job="cnpg"}
```

预期 CNPG 实例值为 1。告警中的 pod/namespace 对应数据库实例；先看 CNPG Cluster conditions、
Pod 日志及 PVC，再查连接池和事务。禁止仅为消除告警盲目提高连接上限或终止业务事务。
NATS 先查服务端配额、保留策略和消费者处理能力；不同 Account 的队列必须分别解释。
SeaweedFS 先查 volume 文件系统/ZFS 与日志，不能直接删除底层卷文件。
通知和临时静默见 [Grafana](../services/grafana.md#从告警进入-grafana)。

实现：[PR #160](https://git.ddupan.top/panxiao81/homelab-infra/pulls/160)。
2026-09-25 现场确认新增 CNPG 与 SeaweedFS 共 4 个 target up，CNPG collector_up=1，
SeaweedFS 容量指标有当前样本；NATS 沿用已验证采集。新增规则无评估错误。
测试覆盖连接数聚合、磁盘指标 type 标签匹配及慢消费者历史值；未制造生产数据库/磁盘故障。
