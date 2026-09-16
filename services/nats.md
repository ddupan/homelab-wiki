---
title: NATS
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
sources:
  - 维护者于 2026-09-16 提供的部署与消费者说明
---

# NATS

**NATS 已作为集群共享消息服务部署，目前唯一的消费者是 Dynamic Runner。**
这是维护者于 2026-09-16 提供的现状；本轮未查询运行环境。

共享服务的定位不随当前消费者数量改变。NATS 属于平台基础设施，
Dynamic Runner 使用它传递任务消息，但不独占消息服务的用途和生命周期。

## 如何接入与维护

平台部署、连接入口、TLS 和账户配置以 homelab-infra 的 `platform/nats/README.md`
及其配置为维护入口。新增消费者应使用适合自身的账户与权限，不能直接沿用 runner 的业务约定。

Dynamic Runner 的 stream、subject、durable 名称、worker 配置和具体启用范围，以
[gitea-dynamic-runner 项目文档](https://git.ddupan.top/panxiao81/gitea-dynamic-runner)
为准。项目正在积极开发，知识库不复制维护这些易变细节，也不把旧示例的 durable 名称差异
单独列为必须查询现场的冲突。

知识库只保留[Dynamic Runner 的用途与职责边界](gitea-dynamic-runner.md)。
涉及 runner 的实际配置和实现进度时，先按项目文档接续工作；需要扩大查询范围时再向维护者确认。
