---
title: PostgreSQL Tenant Operator（计划中的 DBaaS）
lifecycle: planned
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/postgresql-tenant-operator
  - https://git.ddupan.top/panxiao81/postgresql-tenant-operator/src/branch/main/docs/architecture.md
---

# PostgreSQL Tenant Operator

计划中的 homelab DBaaS 中间层：在已有 PostgreSQL 实例上，为下游服务声明式创建和管理
database、login role、权限、扩展及连接凭据。

## 为什么需要它

homelab 资源有限，为每个应用维护一套数据库会浪费资源。绝大多数服务使用 PostgreSQL，
因此集群内目前已经共用一套 PostgreSQL 实例，但数据库、账号、权限和凭据仍不容易维护。
计划自行实现这个中间层，让下游通过统一接口申请可消费的数据库，降低共享实例的管理成本。

这段现状和设计动机由维护者于 2026-09-16 提供；本轮没有查询数据库或集群。
现有实例的日常接入见[共享 PostgreSQL 使用指南](shared-postgresql.md)。
现有实例的源码入口为 homelab-infra 的 `apps/shared-postgresql/`。

## 当前进度

2026-09-16 查阅[项目 README](https://git.ddupan.top/panxiao81/postgresql-tenant-operator/src/branch/main/README.md)
与架构文档时，项目记录为 **API 骨架阶段，尚未对 PostgreSQL 或 OpenBao 执行写操作**。
已批准的设计合同不等于已经实现的功能，本文不表示 DBaaS 已上线。
项目首页还注明 `config/samples` 保留旧 API 骨架，不能将其直接当作最终使用接口。

## 计划中的使用方式

1. 平台管理员通过 `PostgreSQLInstance` 注册已有 PostgreSQL 实例及管理连接。
2. 下游以 namespaced `PostgreSQLTenant` 声明所需 database、login owner 和扩展。
3. controller 校验所有权与冲突，幂等创建凭据、role、database 和授权等资源。
4. 应用凭据以 OpenBao KV 为事实来源，由 ESO 投射为 Kubernetes Secret。
   非 Kubernetes 消费者使用提供的 OpenBao API URL，并通过自身授权获取凭据。
5. ESO 投射成功且应用凭据实际登录成功后，Tenant 才能进入 Ready。

GitOps、Terraform、kubectl 和未来 Backstage 计划共用这套 Kubernetes API。
当前没有可供日常申请数据库的已验证服务入口；接口和具体行为以项目规范为准。

## 职责边界

- operator 管理实例内的租户资源，不运行 PostgreSQL/OpenBao，也不管理 VM、存储、备份或 OpenBao PKI。
- 应用密码写入 OpenBao，不进入 CR、Event 或日志；ESO 负责向 Kubernetes 消费者投射。
- 默认删除策略为 `Retain`，删除声明不会默认删除业务数据；显式 `Delete` 需重新校验所有权。
- 遇到未知 database/role 等资源报告 Conflict，不能自动接管、覆盖或删除；现有数据库迁移需遵循迁移合同。
- namespace 是 Kubernetes 身份与 RBAC 边界；database/role 名称在一个 PostgreSQL Instance 内仍全局唯一。

这些是项目已记录的设计合同，不是本轮验证过的运行行为。

## 设计与操作文档入口

已查阅[系统架构](https://git.ddupan.top/panxiao81/postgresql-tenant-operator/src/branch/main/docs/architecture.md)，
其中说明组件、所有权、协调流程及凭据边界。其他文档按 README 收录，未在本轮逐篇复核：

- [规范与验收标准](https://git.ddupan.top/panxiao81/postgresql-tenant-operator/src/branch/main/docs/specification.md)：规范性行为；与架构视图冲突时以规范为准。
- [API 合同](https://git.ddupan.top/panxiao81/postgresql-tenant-operator/src/branch/main/docs/api-reference.md)：资源字段和 Condition。
- [部署](https://git.ddupan.top/panxiao81/postgresql-tenant-operator/src/branch/main/docs/deployment.md)与[安全](https://git.ddupan.top/panxiao81/postgresql-tenant-operator/src/branch/main/docs/security.md)：依赖和权限。
- [迁移](https://git.ddupan.top/panxiao81/postgresql-tenant-operator/src/branch/main/docs/migration.md)与[运维](https://git.ddupan.top/panxiao81/postgresql-tenant-operator/src/branch/main/docs/operations.md)：现有数据库、删除和恢复合同。

具体实现进度回到[项目仓库](https://git.ddupan.top/panxiao81/postgresql-tenant-operator)查询，
后续查询前先向维护者对齐当前工作与 ticket。本页保留设计定位和带日期的阶段摘要。
