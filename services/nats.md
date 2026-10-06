---
title: NATS
lifecycle: retired
evidence: live-verified
last_reviewed: 2026-10-06
last_verified: 2026-10-06
sources:
  - 维护者于 2026-09-16 提供的部署与消费者说明
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/278
---

# NATS

**NATS 已停用并缩容到零，配置、PVC 与 Service 保留供恢复。**
2026-10-05 的源码 README 记录 Dynamic Runner 已移除 JetStream 依赖；
2026-10-06 排障现场确认 nats namespace 无 Pod，残留采集造成空抓取池告警。
本次通过 [PR #278](https://git.ddupan.top/panxiao81/homelab-infra/pulls/278)
停用 PodMonitor，现场清理残留 VMPodScrape；验收范围为无 Pod、无采集对象、
Helm v13 和 Flux Ready，未验证停用前的消息业务。恢复时同时将 replicas 改回 1、启用
`promExporter.podMonitor.enabled`，并从 Git 历史恢复 NATS 专用告警。
以下 Account 与接入说明仅供恢复时参考，不代表入口当前可用。

## 多租户边界

NATS 原生通过 **Account** 提供多租户隔离。不同 Account 拥有各自的 subject 命名空间
和 JetStream 资源范围，多个消费者可以使用同一套 NATS 服务。
不同 Account 下的 stream、subject 或 durable 名称不会仅因重名而互相冲突。

因此，讨论队列与 consumer 必须同时明确所属 Account、stream 和消费者约定，
不能把不同租户的名称当作集群全局冲突。跨 Account 通信需要显式配置，
同一 Account 内的 worker 协调则遵循所属项目的约定。
这一共享服务的隔离定位由维护者于 2026-09-16 补充。

## 如何接入与维护

平台部署、连接入口、TLS 和账户配置以 homelab-infra 的 `platform/nats/README.md`
及其配置为维护入口。新租户通过独立 Account 及对应权限接入；属于同一租户的消费者
按该 Account 的业务约定使用资源，不能把 runner 的约定推广为整个集群的统一命名要求。

Dynamic Runner 的 stream、subject、durable 名称、worker 配置和具体启用范围，以
[gitea-dynamic-runner 项目文档](https://git.ddupan.top/panxiao81/gitea-dynamic-runner)
为准。项目正在积极开发，知识库不复制维护这些易变细节，也不把旧示例的 durable 名称差异
单独列为必须查询现场的冲突。

知识库只保留[Dynamic Runner 的用途与职责边界](gitea-dynamic-runner.md)。
涉及 runner 的实际配置和实现进度时，先按项目文档接续工作；需要扩大查询范围时再向维护者确认。

## 历史指标与告警

2026-09-25 已现场确认既有 :7777 prom-exporter 经 PodMonitor → VMPodScrape 接入中央采集，
job 为 `nats/nats`，target up 且 nats_* 指标有当前样本。当时配置了采集不可用/整个 job 消失告警；
已增加 JetStream 服务端容量与慢消费者规则；consumer 积压仍待后续。
范围和阈值见 [数据服务监控](../guides/monitoring-data-services.md)。
转换器故障处理与验证依据见 [基础监控运维](../guides/monitoring-foundation.md#nats-转换故障经验)。
