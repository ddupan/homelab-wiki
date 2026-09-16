# 待核实与文档缺口

审阅日期：2026-09-16；初版依据工作区，SPIFFE/SPIRE 已按维护者指定补读 #34 与 runbook，未查询现场。
下面的检查方法只是候选步骤，执行前先问维护者当前进度及查询范围。
以下路径相对于 homelab-infra。优先修复影响恢复、认证、DNS 和首次使用的问题。

## 已对齐的动态工作

LAN DNS 已按维护者于 2026-09-16 提供的现状对齐：DHCP 下发主 DNS Blocky、副 DNS
路由器，Blocky 上游为路由器，Samba AD 部分已完成。详见 [LAN DNS](services/lan-dns.md)。
维护者明确无需逐台确认主机；源码 DNS README 的旧描述待同步，不再据此判定尚未启用。

SPIFFE/SPIRE 按维护者指定，以 [#34](https://git.ddupan.top/panxiao81/homelab-infra/issues/34)
记录为主要依据：基础设施与最小 OpenBao PoC 已完成，issue 保持 open 跟踪后续集成。
已合并的 runbook 也包含新 workload 接入和运维说明，不能再标记为“缺接入指南”。
原工作区集群总览的“首次上线待验证”不作为当前阶段判断。
详见 [SPIFFE/SPIRE 使用入口与阶段状态](services/spire.md)；源码工作区本轮未修改。

## 待向维护者确认的记录差异

| 项目 | 两边的记录 | 核实与收敛方式 |
|---|---|---|
| Authelia | README 仍描述 OIDC 为后续阶段、旧 Contour/Traefik 路径；退役记录和 Envoy 文档已描述 Authelia 替代旧 IdP | 核对 OIDC discovery、登录及 forward-auth，重写过时段落；迁移旧文档前检查其中的敏感示例 |
| Dynamic Runner 的启用范围 | 新仓库 README 定义 Pod/VM 两种接口；旧工作区仍记录 kind-microvm PoC | 软件与基础设施归属已由 README 明确；实际启用范围先问维护者，再按指定 ticket 或验证记录补充，不将旧 PoC 当作新接口已上线的依据 |
| NATS durable 名称 | NATS 文档示例为 `kind-microvm-pve2`；microVM 文档配置为 `kind-microvm`，要求同类 worker 共享 durable | 查运行配置和 consumer；统一文档，避免多 worker 队列语义不一致 |
| 旧 VictoriaMetrics Compose | `platform/observability/README.md` 说已替代；`apps/victoriametrics/` 仍留配置 | 只读检查 Docker 与采集目标，确认是否仍承担职责，再标记退役或迁移 |

## 优先补充的使用说明

1. Gitea / Actions：登录、创建仓库、选择 runner，以及可信任务限制。
2. Grafana：登录、找到内存与 Swap 看板、查询指标和日志的一个完整例子。
3. zot / SeaweedFS：拉取、发布授权、S3 客户端接入，以及数据备份边界。
4. OpenBao：日常登录、按权限取用秘密、申请权限；与灾难恢复分开说明。
5. NetBox：查看拓扑与 IPAM 的路径，强调目前是评估镜像，改动入口在 Git。
6. codex-proxy、LiteLLM gateway、shared PostgreSQL、Tailscale、ps3netsrv、vlmcsd、k3s：补用途和当前状态；这些目录缺少根 README。

## 盘点盲区

- `docs/cicd.md` 提及 `e5renew`、`rustfs`，但无独立组件目录；需要确认现状与归属。
- `infrastructure/docker/README.md` 提及仓库外 `research-auto`，不能在本轮算作已盘点服务。
- `gitea-microvm-runner` 已更名 `gitea-dynamic-runner`，按维护者指定查阅 README，
  已收录[动态 Pod/VM runner](services/gitea-dynamic-runner.md)的接口、组件和路线；实际运行状态未查询。
- PostgreSQL Tenant Operator 已按维护者说明及项目 README/架构文档收录为
  [计划中的 DBaaS 中间层](services/postgresql-tenant-operator.md)。共享 PostgreSQL 已在使用，
  operator 仍按项目记录标为 API 骨架阶段；本轮未查询运行环境。
- workload-sts 已按维护者提供的信息查阅：仓库已归档，停止开发、不部署 PoC，
  作为[早期设计与替代决策的历史来源](architecture/workload-sts-history.md)保留，不列为待接入服务。
- 新增 NATS、zot、microVM 等来源含未提交文件；合并后补可访问的 commit/PR 链接。
- Backstage 仍作为计划入口记录；本轮没有证明已有部署。

完成核实后，将结果写回对应权威文档，并更新服务总览的证据等级和验证日期。
