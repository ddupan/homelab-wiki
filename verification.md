# 首轮状态对齐记录（已完成）

**2026-09-16，维护者确认本轮待核实事项已结束；当前没有开放的状态核实任务。**

结论来自维护者说明、指定的项目文档与 ticket，以及旧监控栈的授权检查和清理。
本轮完成不等于所有服务都经过现场检查，也不等于各开发项目全部完工。
下文保留对齐结果；后续写作与源码文档同步移至[文档完善清单](documentation-backlog.md)。
动态实施进度继续由各项目文档和 ticket 维护，不另开一轮全量状态盘点。

## 已对齐的动态工作

NATS 已作为集群共享服务部署，当前唯一消费者为 Dynamic Runner，见 [NATS](services/nats.md)。
维护者明确 Dynamic Runner 正在积极开发，其启用范围、durable 名称和实现进度以
[项目文档](https://git.ddupan.top/panxiao81/gitea-dynamic-runner)为准。
维护者补充动态 Pod 已上线测试、系统总并发 4，VM 正在工作、系统总并发 1；
纯 self-hosted runner 准备退役。使用入口见 [Gitea / Actions](services/gitea.md)。
不再将旧示例的 durable 名称差异或启用范围列为独立待核实项。
NATS 原生通过 Account 隔离租户，跨 Account 的名称不构成全局冲突；
runner 的队列协调约定仅在其所属 Account 和 stream 范围内讨论。

Authelia 已按维护者于 2026-09-16 的说明标为 **active、唯一的主 OIDC broker**，
见 [Authelia](services/authelia.md)。原工作区的“OIDC 后续启用”描述待同步，
不再将其列为上线状态冲突，也不据此发起现场核实。

LAN DNS 已按维护者于 2026-09-16 提供的现状对齐：DHCP 下发主 DNS Blocky、副 DNS
路由器，Blocky 上游为路由器，Samba AD 部分已完成。详见 [LAN DNS](services/lan-dns.md)。
维护者明确无需逐台确认主机；源码 DNS README 的旧描述待同步，不再据此判定尚未启用。

SPIFFE/SPIRE 按维护者指定，以 [#34](https://git.ddupan.top/panxiao81/homelab-infra/issues/34)
记录为主要依据：基础设施与最小 OpenBao PoC 已完成，issue 保持 open 跟踪后续集成。
已合并的 runbook 也包含新 workload 接入和运维说明，不能再标记为“缺接入指南”。
原工作区集群总览的“首次上线待验证”不作为当前阶段判断。
详见 [SPIFFE/SPIRE 使用入口与阶段状态](services/spire.md)；源码工作区本轮未修改。

## 旧监控栈清理结果

初轮列出的状态差异已按维护者说明、指定资料或授权检查完成分类；不再保留自动现场核查任务。

[旧 VictoriaMetrics Compose](services/victoriametrics-legacy.md) 已于 2026-09-16 完成清理：
维护者明确要求直接删除旧配置和全部数据卷，三个无引用 Docker 卷及旧配置均已删除，
未备份或迁移数据。新 Kubernetes 栈的资源状态检查和指标清单渲染通过。
基础设施清理已通过 [PR #73](https://git.ddupan.top/panxiao81/homelab-infra/pulls/73)
合并 main（`9c64d31`）；配置交付和数据处置均已完成。

## 已确认的归属与范围

- 维护者于 2026-09-16 指定 Samba AD、OCI、Proxmox 优先 IaC、以代码为准；
  后续可直接核对仓库配置，不重复询问同一资料范围。配置声明与现场验证仍分开记录。

- 维护者于 2026-09-16 说明 codex-proxy“应该是退役的”，已从现役应用列表移至归档范围；
  未查询运行环境，也没有删除源码或数据。LiteLLM、Tailscale、ps3netsrv、vlmcsd 无需补充动态事项，
  已基于仓库配置补使用指南；这不等于新增的现场验收。

- e5renew 和 research-auto 已由维护者明确为 GitHub 上的[外部消费者](services/external-consumers.md)，
  不属于 homelab 基础设施，不再列为盘点盲区或缺失组件。
- `gitea-microvm-runner` 已更名 `gitea-dynamic-runner`，按维护者指定查阅 README，
  已收录[动态 Pod/VM runner](services/gitea-dynamic-runner.md)的接口、组件和路线；实际运行状态未查询。
- PostgreSQL Tenant Operator 已按维护者说明及项目 README/架构文档收录为
  [计划中的 DBaaS 中间层](services/postgresql-tenant-operator.md)。共享 PostgreSQL 已在使用，
  operator 仍按项目记录标为 API 骨架阶段；本轮未查询运行环境。
- workload-sts 已按维护者提供的信息查阅：仓库已归档，停止开发、不部署 PoC，
  作为[早期设计与替代决策的历史来源](architecture/workload-sts-history.md)保留，不列为待接入服务。
- Backstage 为计划中的统一入口，不作为已部署服务记录。

后续出现新的状态问题时，先向维护者对齐，再按授权范围更新对应服务文档。

## Ayatori Database 设计修订同步

2026-09-24，维护者批准 Instance → Database → Tenant 资源/申请分离，替代原 PostgreSQL
registry 与自动所有权恢复合同。源仓库设计和 wiki 已同步，Ayatori 设计与 registry 撤除
已推送到 `feat/database-registry-inspection`；本记录随 wiki 来源同步提交发布。
registry 撤除通过本地全量测试、lint 及真实 API server/PostgreSQL 集成测试；
新资源 API 与三资源运行链路未完成，不属于部署或现场验证。

源设计：[6db8a49](https://git.ddupan.top/panxiao81/ayatori/commit/6db8a495fb9f8981d336c9e6288253628ab478b6)；
代码撤除：[23a2d81](https://git.ddupan.top/panxiao81/ayatori/commit/23a2d81b5041f8589baab1c234136cd2c701bb06)；
wiki 权威摘要：[DBaaS 设计](services/postgresql-tenant-operator.md#当前资源模型2026-09-24-已确认)。
来源链接固定到实现提交；相关设计、registry 撤除与 CI 去重修复已随
[PR #9](https://git.ddupan.top/panxiao81/ayatori/pulls/9) 合并为
[347a667](https://git.ddupan.top/panxiao81/ayatori/commit/347a667c0c1737bc4e2703dec5f11358f0425e43)。
最新 head 的 CI #781 已全部通过；无日志启动失败的 test 单项重试后通过。
旧仓库固定基线及受保护工作树未修改。

2026-09-25 的单数据库、单登录 owner 与凭据生命周期边界，以及 Database 集群级作用域、
引用与管理权限边界、资源侧先写的绑定顺序与部分写入重试规则，以及无绑定名单、
删除前策略可改与 Database UID 凭据定位的决定已同步到
[DBaaS 设计](services/postgresql-tenant-operator.md#当前资源模型2026-09-24-已确认)。
依据维护者当日确认；Ayatori 已提交为 `7e9e8e828bfcbdc8d4e2fcb6bc3d13727712a82c`，
源码已通过 [Ayatori PR #10](https://git.ddupan.top/panxiao81/ayatori/pulls/10) 的三项 CI，
并于同日按维护者要求合并为
[55b269c](https://git.ddupan.top/panxiao81/ayatori/commit/55b269ce2eb40f6b44c1afe838389093efdac98e)。
wiki 按维护者要求直接合入 main，原 [wiki PR #3](https://git.ddupan.top/panxiao81/homelab-wiki/pulls/3)
保留为历史讨论入口；后续纯文档变更不另开 PR。
关联源码：[7e9e8e8](https://git.ddupan.top/panxiao81/ayatori/commit/7e9e8e828bfcbdc8d4e2fcb6bc3d13727712a82c)。
这只是第一版 API 范围确认，不表示新资源链路已实现。

上述已合并实现包含三资源 schema 与真实 API server 校验，
本地 `make test` 与远端 CI 均通过。已接入绑定
controller、目标固定、finalizer 保留与生成 RBAC，真实 API server 验证并发、补写及 watch。
尚未实现 finalizer 清理、供应与交付，不宣称完成三资源生命周期或现场验收。

同日确认原生非 superuser + CREATEDB/CREATEROLE 管理方案，已同步至
[DBaaS 职责边界](services/postgresql-tenant-operator.md#职责边界)。Instance 观测链路的实现提交
[bc227bf](https://git.ddupan.top/panxiao81/ayatori/commit/bc227bfdb4b2f5b027fe522b8dcf72db17b84d26) 本地已通过
全量测试、三轮 controller/application race、真实 PostgreSQL/API server 集成测试及普通/integration lint。
[PR #11](https://git.ddupan.top/panxiao81/ayatori/pulls/11) 的三项 CI 均通过，维护者批准后已合并为
[f4deb98](https://git.ddupan.top/panxiao81/ayatori/commit/f4deb98a7fcf61fb97ce52bbf190beb816d0141a)；
未部署或进行现场验收。

后续凭据存储切片已签名提交并推送为
[f6bb9e4](https://git.ddupan.top/panxiao81/ayatori/commit/f6bb9e4599afca49a9cdc3d40789e11d118db9c5)，
由 [PR #12](https://git.ddupan.top/panxiao81/ayatori/pulls/12) 跟踪 CI 与 review。
全量测试、真实 PostgreSQL/API server/OpenBao 集成测试及两种 lint 本地通过；源码模块文档
和 wiki 已同步实现边界与正式链接。尚未合并或接入供应流程，不把本地验证等同于远端 CI。

## 2026-09-25 sandbox 存储故障复盘的来源边界

维护者报告 VyOS 到 sandbox 的 LB 故障并授权恢复。现场确认 LB 配置未在故障当天更改，
故障来自 DRBD quorum 丢失后 sandbox1 根卷进入只读；已离线修复并恢复数据库、双 API 与 Pod。
后续按维护者给出的 PostgreSQL/Alertmanager 会话核对，发现新 HDD 数据卷初始同步重叠与
多个既有资源故障的时间关联，尚未证明具体网络或磁盘瓶颈。长期恢复方法见
[Proxmox](services/proxmox.md#sandbox-lb-与根文件系统恢复)。

事故报告与恢复手册在 wiki 统一维护，见[完整事故报告](incidents/2026-09-25-drbd-quorum-sandbox.md)。
取证引用的 etcd/shared-postgresql 源码当时尚未提交，固定版本关联待源码合并后补齐；
服务恢复不等于全部整改完成。

## 共享 etcd 与 PostgreSQL 来源同步

2026-09-25 shared etcd 三成员、新 PG 生产主从与开发实例、稳定入口、本地备份已部署，
监控 CR 已现场应用。OIDC 恢复后，专用身份与 etcd/PG 每日续签均已启用；此前 Bao 权限阻塞已解除。
真实 PG 自动切换、回切、SQL/TLS、备份恢复与配置幂等通过，边界见
[共享 PostgreSQL](services/shared-postgresql.md#k3s-外实例的实现与验收边界2026-09-25)和
[共享 etcd](services/shared-etcd.md)。

源码 `infrastructure/etcd/`、`infrastructure/shared-postgresql/`、DNS 和监控已提交至 [IaC PR #159](https://git.ddupan.top/panxiao81/homelab-infra/pulls/159)，尚未合并，
不能当作 Flux 已从 Git 接管。既有 CNPG 应用未迁移，异地备份后置；数据库细项告警仍待补齐。
Ayatori 按维护者决定继续使用独立控制面，本轮只准备接入材料，尚未验收 controller/Instance Ready。
两仓事实已同步，源码文档已直接推送 main：[文档 acd4b55](https://git.ddupan.top/panxiao81/homelab-infra/commit/acd4b55)；IaC 固定版本为
[3a2fe5f](https://git.ddupan.top/panxiao81/homelab-infra/commit/3a2fe5f)。
