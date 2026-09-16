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
