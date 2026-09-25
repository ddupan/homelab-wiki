---
title: NATS
lifecycle: active
evidence: documented
last_reviewed: 2026-09-25
last_verified: null
sources:
  - 维护者于 2026-09-16 提供的部署与消费者说明
---

# NATS

**NATS 已作为集群共享消息服务部署，目前唯一的消费者是 Dynamic Runner。**
这是维护者于 2026-09-16 提供的现状；本轮未查询运行环境。

共享服务的定位不随当前消费者数量改变。NATS 属于平台基础设施，
Dynamic Runner 使用它传递任务消息，但不独占消息服务的用途和生命周期。

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

## 指标与告警

2026-09-25 已现场确认既有 :7777 prom-exporter 经 PodMonitor → VMPodScrape 接入中央采集，
job 为 `nats/nats`，target up 且 nats_* 指标有当前样本。已有采集不可用/整个 job 消失告警；
JetStream 容量、consumer 积压等业务规则仍待第二批。
转换器故障处理与验证依据见 [基础监控运维](../guides/monitoring-foundation.md#nats-转换故障经验)。
