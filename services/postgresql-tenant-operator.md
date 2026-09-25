---
title: PostgreSQL Tenant Operator（计划中的 DBaaS）
lifecycle: planned
evidence: documented
last_reviewed: 2026-09-25
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

2026-09-20 的迁移决定原要求整体沿用源设计。2026-09-24，维护者明确批准下述资源/申请
分离修订，替代 registry、自动所有权恢复与原 Retain 合同；管理凭据、TLS、OpenBao/ESO 和
其他适用安全边界继续保留。这是显式设计修订，不是已完成运行验证。

原 `database.ddupan.top/v1alpha1` API group 也不保留。Ayatori 中的目标 API 使用
`database.ayatori.ddupan.top/v1alpha1`，并纳入统一的 `api/database/v1alpha1` 与 Database 模块
结构；由于不存在已部署消费者，不建立 alias 或 conversion 入口。

合并边界记录在 Ayatori PR
[#3 的 ADR-0008](https://git.ddupan.top/panxiao81/ayatori/src/commit/33fb3ec9725dca8a10f2ad4bcd71cf83413932ee/docs/decisions/0008-merge-postgresql-tenant-operator.md)；
该决定已于 2026-09-21 合并 main，链接固定到合并版本；设计合并不表示 Database 实现已完成。

## 当前资源模型（2026-09-24 已确认）

参考 [Kubernetes 官方 PV/PVC](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) 的
资源/申请分离：Instance 是资源来源与管理入口；独立 Database 类似 PV；Tenant 是类似 PVC
的用户申请。Instance 一对多 Database，每个 Database 同时最多绑定一个 Tenant。

Database 自带 instanceRef，手工登记不依赖 Tenant；动态申请由 Tenant 选择 Instance，
引用已有 Database 时从资源获取 Instance，不重复声明另一份来源。

Retain 在申请删除后保留 Database 对象和外部数据，进入 Released，等待管理员处理数据、
旧访问权限和凭据后显式授权重新绑定。已有数据库可由管理员显式登记导入，初始验证不改密、
不改 owner；发现未知同名资源仍报 Conflict。回收策略位于资源侧，Database 不随 Tenant GC。

撤销 PostgreSQL ownership registry 和任意 status 丢失自动重建所有权的要求。CR 记录持久
身份、绑定和进度；普通失败幂等重试，无法确认外部创建结果时报告足够人工诊断的冲突。
不引入 CSI 协议、存储调度或通用 Claim。绑定字段和凭据重新交付协议仍需细化。

2026-09-25，维护者确认第一版 Database 的生命周期边界包含一个数据库、一个兼任 owner
的登录账号及其应用凭据；Tenant 负责申请与交付。不预留多账号字段或新增 Role/Credential
CRD；一库多账号若有实际需求，再通过后续 API 版本演进。此决定不扩大导入管理授权。
同日确认 Instance 与 Database 为 cluster-scoped，Tenant 为 namespaced。Database 由平台
管理员管理，不属于应用 namespace，也不需要资源专用 namespace。Tenant 按名称引用
Database，资源侧绑定记录包含 Tenant namespace/name/UID；普通申请者不能自行修改回收
策略或将 Released 资源重新开放。具体字段与 RBAC 规则仍待细化。

绑定采用资源侧先写：动态 Database 名称由 Tenant UID 确定；先写 Database 的 Tenant
namespace/name/UID，再写 Tenant status 的 Database name/UID，双向一致后才供应或交付。
API 版本冲突重新读取判断，已被其他 Tenant 占用则报冲突；资源侧成功、申请侧失败由
reconcile 核对身份后补齐，不回滚资源侧绑定。绑定不等于 Ready；外部数据库创建结果
不确定仍交给人工处理，不增加事务队列或 registry。该顺序由维护者于同日确认。

同日进一步明确：不增加允许绑定名单或逐 Tenant 审批，有权创建 Tenant 的申请者可显式
申请未绑定且可用的 Database；Released 仍需管理员处理旧访问后重新开放。
回收策略默认 Retain，资源管理者可在删除流程开始前修改；进入删除流程后固定，指定
Delete 即为删除授权，不加第二次审批。动态凭据路径按 Database UID 确定，导入显式关联
已有凭据位置；Released 不自动改密，重新开放前由管理员处理旧访问。
对应 Ayatori `docs/database/specification.md`、`domain-model.md` 与 `api-reference.md`
已推送为 [7e9e8e8](https://git.ddupan.top/panxiao81/ayatori/commit/7e9e8e828bfcbdc8d4e2fcb6bc3d13727712a82c)，
已随 [Ayatori PR #10](https://git.ddupan.top/panxiao81/ayatori/pulls/10) 通过三项 CI 并合并 main，
合并版本为 [55b269c](https://git.ddupan.top/panxiao81/ayatori/commit/55b269ce2eb40f6b44c1afe838389093efdac98e)。

Ayatori main 已加入三资源 Go 类型、生成 CRD、Scheme 注册与 YAML 示例，尚未部署为业务服务。
`make test` 使用真实 API server 验证作用域、默认值、声明
校验、status 隔离、绑定写入版本冲突与示例。绑定 controller 已接入 manager：动态资源按
Tenant UID 命名，先写资源侧绑定，再回读补齐 Tenant status；进入 Binding 后固定申请目标，
拒绝 Released、旧 UID 和陈旧 Ready 观察。真实 API server 覆盖部分写入故障后新 reconciler
补齐、双 Tenant 竞争及实际 manager 在生成 RBAC 角色下的 watch；绑定角色不能读取 Secret。
Bound 仍为 Ready=False，尚无供应或凭据投射。已有 finalizer 保护，但删除清理未实现：
Tenant 删除保持 DeletionPending，资源和申请的 finalizer 不自动移除，不能视为可用的
Retain/Delete 生命周期或部署为业务 DBaaS。具体字段和未完成边界见
源码 [API 合同](https://git.ddupan.top/panxiao81/ayatori/src/commit/7e9e8e828bfcbdc8d4e2fcb6bc3d13727712a82c/docs/database/api-reference.md)
的“当前 API 切片”。

绑定代码按维护者要求分层：领域层负责纯规则，application service 协调绑定步骤和回读，
Kubernetes adapter 负责 CR 映射、版本保护及 Conditions/status/finalizer 呈现，controller
只连接事件、用例与重试。service 和领域层不依赖 Kubernetes 类型，不新增通用事务或
Repository 框架；该重构不扩展上述运行能力。对应源码 `docs/database/domain-model.md`
已随上述提交保存，见 [领域模型](https://git.ddupan.top/panxiao81/ayatori/src/commit/7e9e8e828bfcbdc8d4e2fcb6bc3d13727712a82c/docs/database/domain-model.md)。

本轮依据为维护者设计讨论和 Ayatori 已推送的
[ADR-0009](https://git.ddupan.top/panxiao81/ayatori/src/commit/6db8a495fb9f8981d336c9e6288253628ab478b6/docs/decisions/0009-database-resource-and-claim.md)、
[系统规格](https://git.ddupan.top/panxiao81/ayatori/src/commit/6db8a495fb9f8981d336c9e6288253628ab478b6/docs/database/specification.md)。
registry 实现、迁移与 Instance 初始化依赖已在
[23a2d81](https://git.ddupan.top/panxiao81/ayatori/commit/23a2d81b5041f8589baab1c234136cd2c701bb06)
撤除；本地测试与真实 PostgreSQL/API server 集成验证通过，但新三资源链路尚未完成。
上述设计与撤除已随 [PR #9](https://git.ddupan.top/panxiao81/ayatori/pulls/9) 合并 main，
合并版本为 `347a667`；不表示三资源链路已实现或部署。见 [同步记录](../verification.md#ayatori-database-设计修订同步)。

## 计划中的使用方式

1. 平台管理员通过 `PostgreSQLInstance` 注册已有 PostgreSQL 实例及管理连接。
2. 下游以 namespaced `PostgreSQLTenant` 申请数据库，或显式引用管理员登记的 Database。
3. controller 建立独立 Database 记录与排他绑定，供应或验证资源；未知同名及不确定创建报冲突。
4. 应用凭据以 OpenBao KV 为事实来源，由 ESO 投射为 Kubernetes Secret。
   非 Kubernetes 消费者使用提供的 OpenBao API URL，并通过自身授权获取凭据。
5. ESO 投射成功且应用凭据实际登录成功后，Tenant 才能进入 Ready。

GitOps、Terraform、kubectl 和未来 Backstage 计划共用这套 Kubernetes API。
当前没有可供日常申请数据库的已验证服务入口；接口和具体行为以项目规范为准。

## 职责边界

2026-09-25 维护者确认第一版 PostgreSQL 管理账号使用原生非 superuser 方案，具有
CREATEDB/CREATEROLE，不引入 SECURITY DEFINER 接口。扩展安装按实际权限逐请求验证，
可用列表不等于任意扩展均可安装；基础管理能力不授予导入或接管他人资源的权限。
这项决定沿用原安全文档的非 superuser 原则，并明确了此前未选定的实施方式。
Instance 观测、Secret watch 与删除引用保护的后续实现目前位于 Ayatori
`feat/database-instance-observation` 分支，已本地签名提交为
`bc227bfdb4b2f5b027fe522b8dcf72db17b84d26`，尚未推送/合并；权限矩阵、启用方式和测试边界
以该提交的 `docs/database/README.md`、`security.md` 为准，不能把 main 的旧实现当成已具备该能力。

- operator 管理实例内的租户资源，不运行 PostgreSQL/OpenBao，也不管理 VM、存储、备份或 OpenBao PKI。
- 应用密码写入 OpenBao，不进入 CR、Event 或日志；ESO 负责向 Kubernetes 消费者投射。
- Database 默认 Retain；删除 Tenant 保留资源对象与数据，Released 不自动重新分配。
- 资源侧 Delete 需明确授权、finalizer 与实际管理范围检查，导入不隐含删除或改密授权。
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
