---
title: PostgreSQL Tenant Operator（计划中的 DBaaS）
lifecycle: planned
evidence: documented
last_reviewed: 2026-09-20
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

维护者于 2026-09-20 提供的阶段状态如下：

- 已合并 Instance 的 Endpoint、凭据引用、身份/版本、定义与观测目标等值对象；
- 已合并扩展支持能力模型，以及 Instance 最小生命周期与状态 checkpoint；
- CI PR #14 已合并：lint/test 使用 Pod runner，e2e 使用 VM runner；当前没有开放 PR；
- 上述领域基础尚未接入实际运行链路，不能理解为新设计已经可用；
- 仍缺完整 Ready 判定、Kubernetes Secret 管理凭据与连接刷新、应用层/数据库 adapter/controller
  接入、CRD 与批准规格对齐及集成验证；
- Tenant 的完整创建、凭据交付和 Retain/Delete 生命周期仍未完成；
- 旧运行链路仍包含直接读取 OpenBao 管理凭据的逻辑。

本地暂停在 `feature/instance-extension-observations`，有两个未提交文件，实现 Instance 接收扩展
观测及其测试。该部分此前只通过领域包 lint，未运行本地测试、未提交、未推送；分支仍基于 #13，
未包含刚合并的 CI 改动。该工作区必须原样保留，不能作为已合并能力或迁移来源。

已批准的设计合同不等于已经实现的功能，本文不表示 DBaaS 已上线。生成的 CRD/API 与 samples
仍可能落后于批准规格，不能直接作为最终使用接口。

2026-09-20，维护者决定将该项目合并为 Ayatori 的 Database 领域模块。已批准的规格、领域模型、
状态机和测试继续作为迁移合同；不会把独立仓库的 manager、生成文件和当前工作树整仓复制。
首个迁移基线使用包含已合并 Instance 领域基础与 CI #14 的最新 main commit，再按领域层、API、
adapter 和 controller 的纵向切片进入 Ayatori；暂停中的两个未提交文件不进入首个切片。旧仓库
在迁移完成并验收前仍是现有设计与代码的来源，本决定不表示 DBaaS 已上线。

维护者同时确认目前没有可用版本，也没有 PostgreSQL 实例或 Tenant 被该 operator 托管。因此
合并不承担旧运行链路、旧 CRD/status 或数据的兼容责任：直接读取 OpenBao 管理凭据的旧路径可以
删除，未投入使用且落后于规范的 CRD/samples/实现结构不保留兼容层。

源项目已批准的系统规格、API 语义、Instance/Tenant 领域模型、状态机、ownership registry、
凭据交付、Retain/Delete、恢复和测试设计整体直接复用为 Ayatori DBaaS 合同。大胆重构针对旧运行
实现和项目装配，不表示可以静默改变这些已批准行为；合同变化仍须先修订规格并单独评审。

原 `database.ddupan.top/v1alpha1` API group 也不保留。Ayatori 中的目标 API 使用
`database.ayatori.ddupan.top/v1alpha1`，并纳入统一的 `api/database/v1alpha1` 与 Database 模块
结构；由于不存在已部署消费者，不建立 alias 或 conversion 入口。

合并边界记录在 Ayatori PR
[#3 的 ADR-0008](https://git.ddupan.top/panxiao81/ayatori/src/commit/33fb3ec9725dca8a10f2ad4bcd71cf83413932ee/docs/decisions/0008-merge-postgresql-tenant-operator.md)；
该决定已于 2026-09-21 合并 main，链接固定到合并版本；设计合并不表示 Database 实现已完成。

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

迁移前的具体实现进度仍回到[项目仓库](https://git.ddupan.top/panxiao81/postgresql-tenant-operator)
查询；迁移后的实现与发布进度转到 Ayatori。后续查询前先向维护者对齐当前工作与 ticket。
本页保留设计定位和带日期的阶段摘要。
