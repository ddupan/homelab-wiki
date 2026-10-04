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

凭据存储切片及冷缓存准备修复已通过 CI #815 的 test、lint、database-integration，
维护者批准后合并 [PR #12](https://git.ddupan.top/panxiao81/ayatori/pulls/12)，合并提交
[22ab72e](https://git.ddupan.top/panxiao81/ayatori/commit/22ab72ec60dd5a0bf852e4563e107597dd56e81f)。
后续 Kubernetes 认证与短期会话续期已提交为
[f0aa86f](https://git.ddupan.top/panxiao81/ayatori/commit/f0aa86f67673fbfb5f182f3ce35679c614be968d)，
由 [PR #13](https://git.ddupan.top/panxiao81/ayatori/pulls/13) 跟踪 CI 与 review。
首版依赖投射 SA 文件的假设已按维护者意见撤除：集群外 kubeconfig 与集群内配置共用 manager
客户端，通过受限 TokenRequest 获取登录 JWT。manager 显式配置、Runnable 与 readiness 已装配；
三轮真实 API/OpenBao race、本地全量测试与两种 lint 通过，覆盖 RBAC 撤回/恢复和越权拒绝。
源码文档与 wiki 已同步边界和正式链接；后续合并及 CI 结果见下文，不把本地验证等同于远端 CI；
未部署生产 auth/RBAC，也未接入 Database 供应或 ESO 交付。

同一 PR 的公共 infra 拆分已提交为
[65c60cc](https://git.ddupan.top/panxiao81/ayatori/commit/65c60cca4528bc8bf14783fb7b59922283059c02)。
Bao client/TLS 与认证不再归 Database；Secret 凭据适配器注入 manager 的直连 reader，
领域继续维护凭据格式和写入结果语义。分层约定已同步
[控制面边界](architecture/ayatori-control-plane.md#controller-公共基础设施边界)及源码文档。
全量单元/API 测试、真实 PostgreSQL/OpenBao 集成、公共 infra race 与两种 lint 本地通过；
最终 head 为 `356e216`，包含 bootstrap 职责拆分、配置测试与真实 API 启动测试。
2026-09-27 维护者批准合并为
[6b2808c](https://git.ddupan.top/panxiao81/ayatori/commit/6b2808ce91b03215f466746a15d0c3d7442bb9d4)。
请求设置了 `merge_when_checks_succeed=true`、`force_merge=false`，但 Gitea 在
database-integration 仍运行时执行了合并，不能将自动合并参数视为全部 CI 通过的保证。
随后确认 CI #931 已结束，test、lint、database-integration 全部成功；不声称已部署。

2026-10-01 Database 链路按维护者修订的分层重构，并改为无检查点的事实驱动供应：
[PR #16](https://git.ddupan.top/panxiao81/ayatori/pulls/16)、[PR #17](https://git.ddupan.top/panxiao81/ayatori/pulls/17)、[PR #18](https://git.ddupan.top/panxiao81/ayatori/pulls/18)
在三项 CI 通过后合并为 `8dbdff0`、`915f83b`、`adce262`，未部署、未现场验证。
[控制面边界](architecture/ayatori-control-plane.md#controller-公共基础设施边界)与
[PostgreSQL Tenant Operator](services/postgresql-tenant-operator.md) 已同步。
源码 `docs/architecture/overview.md` 的“进程内依赖边界”曾滞后于新分层，已随
[PR #19](https://git.ddupan.top/panxiao81/ayatori/pulls/19)、[PR #20](https://git.ddupan.top/panxiao81/ayatori/pulls/20) 同步（合并提交 `c5424b5`、`3205186`，
CI 三项均通过）；Instance 与 Tenant 链路同时完成迁移，未部署、未现场验证。

## 2026-09-25 sandbox 存储故障复盘的来源边界

维护者报告 VyOS 到 sandbox 的 LB 故障并授权恢复。现场确认 LB 配置未在故障当天更改，
故障来自 DRBD quorum 丢失后 sandbox1 根卷进入只读；已离线修复并恢复数据库、双 API 与 Pod。
后续按维护者给出的 PostgreSQL/Alertmanager 会话核对，发现新 HDD 数据卷初始同步重叠与
多个既有资源故障的时间关联，尚未证明具体网络或磁盘瓶颈。长期恢复方法见
[Proxmox](services/proxmox.md#sandbox-lb-与根文件系统恢复)。

事故报告与恢复手册在 wiki 统一维护，见[完整事故报告](incidents/2026-09-25-drbd-quorum-sandbox.md)。
取证引用的 etcd/shared-postgresql 源码当时尚未提交，固定版本现关联 [合并提交 f6d12d6](https://git.ddupan.top/panxiao81/homelab-infra/commit/f6d12d6)；
服务恢复不等于全部整改完成。

## 共享 etcd 与 PostgreSQL 来源同步

2026-09-25 shared etcd 三成员、新 PG 生产主从与开发实例、稳定入口、本地备份已部署，
监控 CR 已现场应用。OIDC 恢复后，专用身份与 etcd/PG 每日续签均已启用；此前 Bao 权限阻塞已解除。
真实 PG 自动切换、回切、SQL/TLS、备份恢复与配置幂等通过，边界见
[共享 PostgreSQL](services/shared-postgresql.md#k3s-外实例的实现与验收边界2026-09-25)和
[共享 etcd](services/shared-etcd.md)。

源码 `infrastructure/etcd/`、`infrastructure/shared-postgresql/`、DNS 和监控已提交至 [IaC PR #159](https://git.ddupan.top/panxiao81/homelab-infra/pulls/159)，已合并。
2026-09-25 合并后现场验证：Flux observability Ready，应用版本 `f6d12d6`；
两份 VMRule 和两份 VMStaticScrape 均在 Flux inventory 中，状态 operational。
三个 etcd 和两个 Patroni 目标均 up=1，相关 11 条规则 health=ok、inactive。
监控声明已由 GitOps 接管。既有 CNPG 应用未迁移，异地备份后置；数据库细项告警仍待补齐。
Ayatori 按维护者决定继续使用独立控制面，本轮只准备接入材料，尚未验收 controller/Instance Ready。
两仓事实已同步，源码文档已直接推送 main：[文档 acd4b55](https://git.ddupan.top/panxiao81/homelab-infra/commit/acd4b55)；IaC 固定版本为
[3a2fe5f](https://git.ddupan.top/panxiao81/homelab-infra/commit/3a2fe5f)。

## laptop ARC 预算（2026-09-27）

维护者授权的 4 GiB 上限已在线应用并持久化，Ansible 复查零变更。
源码 [PR #165](https://git.ddupan.top/panxiao81/homelab-infra/pulls/165) 已获授权并合并至 main，
提交为 [06943d4](https://git.ddupan.top/panxiao81/homelab-infra/commit/06943d4c6583f1b62fea6176b56f237da54a12e7)，与已部署配置一致。
配置及验证范围见 [ARC 内存预算](guides/laptop-arc-budget.md)。本次合并未重复应用或重启主机；下一次更新负载下的效果仍待观察。


## 共享数据维护告警接管边界

2026-09-27 主机端采集、低开销 exporter 和三目标网络验证完成，6 项采集测试及 12 个新增规则场景通过。
相关 [PR #166](https://git.ddupan.top/panxiao81/homelab-infra/pulls/166) 已合并，版本
[589c34e](https://git.ddupan.top/panxiao81/homelab-infra/commit/589c34e)。现场确认 Flux observability Ready，
VMStaticScrape/PrometheusRule 已入 inventory；converter 生成的 VMRule 为 operational。
三个目标均 up=1，八条规则 health=ok、inactive，新增告警已启用。
详细事实见[维护告警](services/shared-postgresql.md#维护告警2026-09-27)。现有 PR #159 的接管验收不受影响。

## iam-login Hydra 接入的来源同步（2026-09-28）

[Hydra 服务页](services/hydra.md#独立登录服务的-hydra-接入)中的新增 Login/Consent、客户端
管理与注销实现已签名提交并推送，固定源码为
[62b6e9d](https://git.ddupan.top/panxiao81/iam-login/commit/62b6e9d)，包含在
[PR #6](https://git.ddupan.top/panxiao81/iam-login/pulls/6)。该 PR 连同仓储、网关及自动配置重构于
2026-09-29 合并，版本为 [5f49a7c](https://git.ddupan.top/panxiao81/iam-login/commit/5f49a7c)。
此前 GPG agent 阻塞已解除。
本轮 wiki 同步实现边界与隔离验收结果，不代表生产入口已切换。

以下四节写于 2026-09-25 的旧工作区，2026-10-04 补发；文中“未提交”“链接待补”均指当时状态，
相关源码之后已陆续合并（etcd/shared-postgresql 见 PR #159、Backstage 见 `apps/backstage/`）。

## zot GC 与删除授权核实

2026-09-25，维护者要求清理旧 SHA tag。现场 ConfigMap 已有 CI 发布授权，与
旧 zot README/wiki 的“没有常驻 publisher”说明不同；服务页已按现场证据纠正。
本地开发身份在两个 runner 仓库的精确规则仅有 read/create/update，
并不继承通配规则的 delete；源码 SPIRE README 的全仓库删除说明不适用于这两个例外。
详见 [zot GC 与清理](services/zot.md#gc-与-sha-tag-清理)。

权限修正经 [PR #144](https://git.ddupan.top/panxiao81/homelab-infra/pulls/144) 合并并由 Flux
应用 `185a47e2bb4877c5d4274633e366cad0e83cb2a0`；CI 检查通过，两个 HelmRelease Ready。
维护者已授权上线与清理，实际删除 controller 19 个、runner 4 个旧 SHA tag；
最新 main 额外引用的一个候选在删除前已剔除。最近两天推送以完整轮转日志复核。
保留引用的 manifest 与 blob 读取验证通过；未验证 GC 后物理空间释放，未启用自动 retention。
源码与 wiki 事实已同步并关联源码 PR；本轮 wiki 改动仍未提交。

## Backstage 首版前置条件

2026-09-25 按维护者要求准备 Backstage，见[接入与验证边界](services/backstage.md)。
源码 `apps/authelia/values.yaml` 与 `infrastructure/dns/records.yml` 已改，OIDC 与 DNS 已应用；
数据库已通过本机 SPIFFE 取密完成初始化，应用账号连接、owner 与建表权限验证通过。
旧 CLI 会话的 403 不代表 SPIFFE 权限不足。源码及 wiki 改动尚未提交，正式链接待补。
线上 Authelia 存在本地 values 未收录的 Hydra client/policy，本次通过保留线上 values 的
增量升级避免覆盖；后续全量源码部署前需先同步该差异。

## 共享 etcd 与 PostgreSQL 来源同步

2026-09-25 shared etcd 三成员、新 PG 生产主从与开发实例、稳定入口、本地备份已部署，
监控 CR 已现场应用。OIDC 恢复后，专用身份与 etcd/PG 每日续签均已启用；此前 Bao 权限阻塞已解除。
真实 PG 自动切换、回切、SQL/TLS、备份恢复与配置幂等通过，边界见
[共享 PostgreSQL](services/shared-postgresql.md#k3s-外实例的实现与验收边界2026-09-25)和
[共享 etcd](services/shared-etcd.md)。

源码 `infrastructure/etcd/`、`infrastructure/shared-postgresql/`、DNS 和监控修改仍未提交关联，
不能当作 Flux 已从 Git 接管。既有 CNPG 应用未迁移，异地备份后置；数据库细项告警仍待补齐。
Ayatori 按维护者决定继续使用独立控制面，本轮只准备接入材料，尚未验收 controller/Instance Ready。
两仓事实已同步，正式源码 commit/PR 链接待补。

## 2026-09-25 sandbox 存储故障复盘的来源边界

维护者报告 VyOS 到 sandbox 的 LB 故障并授权恢复。现场确认 LB 配置未在故障当天更改，
故障来自 DRBD quorum 丢失后 sandbox1 根卷进入只读；已离线修复并恢复数据库、双 API 与 Pod。
后续按维护者给出的 PostgreSQL/Alertmanager 会话核对，发现新 HDD 数据卷初始同步重叠与
多个既有资源故障的时间关联，尚未证明具体网络或磁盘瓶颈。长期恢复方法见
[Proxmox](services/proxmox.md#sandbox-lb-与根文件系统恢复)。

事故报告与恢复手册在 wiki 统一维护，见[完整事故报告](incidents/2026-09-25-drbd-quorum-sandbox.md)。
取证引用的 etcd/shared-postgresql 源码当时尚未提交，固定版本关联待源码合并后补齐；
服务恢复不等于全部整改完成。

## Incus 接入的跨仓库链接

2026-09-25：共享 Envoy 后端 TLS 兼容补丁已合并发布，见
[homelab-infra #164](https://git.ddupan.top/panxiao81/homelab-infra/pulls/164)。
2026-10-01：Incus/Authelia/DNS IaC 已推送至 `feat/incus-ayatori-base`，
固定源码为 [d45e0b9](https://git.ddupan.top/panxiao81/homelab-infra/commit/d45e0b94e80cb8a509df46a14cd7e89d5381b124)，尚未合并 main。
对应 wiki 随本次提交同步；
维护者已确认真实用户 MFA 登录并返回控制台成功。入口与恢复边界见 [Incus](services/incus.md)。

## Ayatori 首次部署的跨仓库关联（2026-10-04）

Ayatori：[#27](https://git.ddupan.top/panxiao81/ayatori/pulls/27)（`9936960`，部署 role 与 Release）、
[#28](https://git.ddupan.top/panxiao81/ayatori/pulls/28)（`045f535`，OpenBao audience）、
[#30](https://git.ddupan.top/panxiao81/ayatori/pulls/30)（`c0422d9`，重新开放绑定与重新拉取镜像）；
`v0.1.0` 重打于 `c0422d9`。homelab-infra：[#198](https://git.ddupan.top/panxiao81/homelab-infra/pulls/198)（`64b24cc`）、
[#202](https://git.ddupan.top/panxiao81/homelab-infra/pulls/202)（`79e9dbe`）、[#204](https://git.ddupan.top/panxiao81/homelab-infra/pulls/204)（`60de647`）、
[#208](https://git.ddupan.top/panxiao81/homelab-infra/pulls/208)（`53730fb`）、[#211](https://git.ddupan.top/panxiao81/homelab-infra/pulls/211)（`60868b7`）、
[#216](https://git.ddupan.top/panxiao81/homelab-infra/pulls/216)（`61da505`）。现场验证见 [Ayatori](services/ayatori.md#当前状态与证据)。

#208 的标题与提交信息写明 CI 身份增加 update，实际 diff 漏暂存该项，由 #211 补齐；以代码为准。

未同步：Ayatori ADR-0002/0003 与 `docs/concepts/environments.md` 仍描述 managed runtime；
homelab-infra `infrastructure/shared-postgresql/ayatori/` 旧接入材料待删除；备份未建立。
