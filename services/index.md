# 服务总览

审阅日期：2026-09-16。以下覆盖源码工作区 apps/、platform/、infrastructure/ 的一级组件，以及集群入口。
**除旧 VictoriaMetrics Compose 已获授权检查并清理外，其余条目未在本轮现场验证。**
状态栏区分维护者说明、文档、ticket、配置与现场证据，不提供持续的实时健康判断。
SPIFFE/SPIRE 已按维护者授权补读 #34；LAN DNS 与 Authelia 已按维护者说明更新，
独立项目按指定 README 收录。其余条目仍为初轮工作区盘点，查询前先向维护者对齐。
来源路径相对于 [homelab-infra](https://git.ddupan.top/panxiao81/homelab-infra)；包含未提交内容，见首页证据边界。

入口按已有来源记录列出，未记录的内容保持未知，不自动生成现场核实任务。
本轮状态对齐已[完成](../verification.md)；后续写作见[文档完善清单](../documentation-backlog.md)。

## 应用

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| [authelia](authelia.md) | 唯一主 OIDC broker、统一登录 | `auth.ddupan.top` | active；维护者于 2026-09-16 明确已在工作 | 维护者说明、`apps/authelia/` | 同步源码 README 中过时的 OIDC 阶段说明 |
| [blocky](lan-dns.md) | LAN 主 DNS、广告过滤、分流 | `192.168.10.127:53` | 维护者说明已作为 DHCP 主 DNS，上游为路由器 | 维护者 2026-09-16 说明、`apps/blocky/README.md` | 无需逐台确认主机；旧源码说明待同步 |
| [gitea](gitea.md) | 代码托管与 Actions | `git.ddupan.top` | 记录已部署 | `apps/gitea/README.md` | 已有登录、最小 CI 与 runner 选择指南 |
| http-echo | Flux 部署与漂移修复 canary | `集群内` | 记录已验证 | `apps/http-echo/README.md` | 已有验证步骤 |
| [litellm-gateway](litellm-gateway.md) | 模型 API 网关，实际消费者未记录 | `宿主 TCP 4000；地址未记录` | 仅发现配置 | `apps/litellm-gateway/docker-compose.yml` | 已有参数、请求示例与依赖说明 |
| [marker](marker.md) | GPU 文档转换 API | `集群内端口 8001` | 配置与部署指南；未附上线记录 | `apps/marker/README.md` | 已有转换示例；部署镜像仍为占位符 |
| netboot | PXE 与系统安装 | `192.168.10.127` | 有部署及使用记录 | `apps/netboot/README.md` | 已有客户端启动说明 |
| [netbox](netbox.md) | 网络资产与地址管理评估 | `netbox.ad.ddupan.top` | 记录已部署；评估用途 | `apps/netbox/README.md` | 已有浏览与 Git 修改入口指南 |
| [openviking](openviking.md) | 上下文检索服务 | `记录端口 1933 / 8020` | 配置与部署指南；未附上线记录 | `apps/openviking/README.md` | 已有导入、任务查询、检索与原文读取指南 |
| [ps3netsrv](ps3netsrv.md) | PS3 网络内容服务 | `宿主 TCP 38008；地址未记录` | Docker 运维文档记录运行 | `apps/ps3netsrv/docker-compose.yml` | 已有客户端与内容目录指南 |
| [seaweedfs](seaweedfs.md) | S3 对象存储 | `s3.ad.ddupan.top` | zot 文档记录已使用 | `apps/seaweedfs/README.md` | 已有客户端读写指南与备份边界说明 |
| [shared-postgresql](shared-postgresql.md) | 共享 PostgreSQL / CNPG | `shared-db namespace` | 历史迁移记录已完成 | `apps/shared-postgresql/migration.md` | 已有连接、应用接入与共享资源边界指南 |
| [smtp-relay](smtp-relay.md) | 应用经 Microsoft 365 发信 | `smtp-relay.smtp-relay.svc.cluster.local:25` | 有配置与测试指南；未附上线记录 | `apps/smtp-relay/README.md` | 已有应用参数、测试邮件与投递边界指南 |
| [tailscale](tailscale.md) | 远程网络与子网路由 | `Tailscale 网络` | 有配置；本轮未读敏感安装脚本 | `apps/tailscale/subnet-routes.sh` | 已有远程访问与路由边界指南 |
| [vlmcsd](vlmcsd.md) | KMS 兼容服务，使用范围未记录 | `宿主 TCP 1688；地址未记录` | 仅发现配置 | `apps/vlmcsd/compose.yaml` | 已有协议入口与客户端指南；未查询现场 |
| [zot](zot.md) | OCI 镜像与制品仓库 | `zot.ad.ddupan.top / zot-push.ad.ddupan.top` | 文档记录 9 月 16 日验收 | `apps/zot/README.md` | 已有拉取与发布模板；实际 publisher 授权以项目配置为准 |

## 平台

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| [cert-manager](../guides/publish-service.md) | 签发与续期 TLS 证书 | `ClusterIssuer API` | 记录已接管 Flux | `platform/cert-manager/README.md` | 已有新服务证书复用与接入指南 |
| [envoy-gateway](../guides/publish-service.md) | LAN HTTP 入口与认证集成 | `192.168.10.127:443` | 记录已接管 Flux | `platform/envoy-gateway/README.md` | 已有 DNS、路由、认证与发布路径指南 |
| [external-secrets](external-secrets.md) | OpenBao 到 Kubernetes 的秘密投射 | `Kubernetes API` | Helm 记录已接管；对象范围需区分 | `platform/external-secrets/README.md` | 已有字段投射示例与 ownership 边界 |
| gitea-runner | 旧常驻 Gitea Actions runner | 纯 `self-hosted` | 维护者说明准备退役，尚未标为已退役 | `platform/gitea-runner/README.md`、维护者说明 | 新 workflow 改用 [动态 Pod/VM](gitea-dynamic-runner.md) 的明确 labels |
| [k3s DNS](k3s-dns.md) | 集群 CoreDNS 定制 | `集群内 DNS` | 仅发现 DNS 配置 | `platform/k3s/Corefile.desired` | 已有集群 DNS 使用与配置边界说明 |
| [nats](nats.md) | 集群共享消息与 JetStream 队列 | `nats.ad.ddupan.top:4222` | 已部署；维护者说明目前唯一消费者为 Dynamic Runner | 维护者 2026-09-16 说明、`platform/nats/README.md` | runner 消息队列约定以独立项目文档为准 |
| [observability / Grafana](grafana.md) | Grafana、指标、日志和追踪 | `grafana.ad.ddupan.top` | 记录已接管 Flux；9 月 16 日变更入口 | `platform/observability/README.md` | 已有看板、指标与日志查询指南 |
| [openebs](openebs.md) | k3s 本地 ZFS 持久卷 | `localpv-zfs-ceph StorageClass` | 记录已接管 Flux | `platform/openebs/README.md` | 已有 PVC 示例、绑定与数据回收边界 |
| [spire](spire.md) | 跨基础设施的统一机器身份入口 | `Workload API / spire-oidc.ad.ddupan.top` | #34 记录基础设施与最小 OpenBao PoC 已完成；后续集成进行中 | [#34](https://git.ddupan.top/panxiao81/homelab-infra/issues/34)、[RUNBOOK](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/spire/RUNBOOK.md) | 已有接入指南；动态任务以 ticket 为准 |

## 基础设施

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| cloudflared | 公网 Tunnel 与 DNS | `Cloudflare 边缘配置` | 有现有资源接管记录 | `infrastructure/cloudflared/terraform/README.md` | 明确配置权威位置与服务发布流程 |
| [dns](lan-dns.md) | 跨视图 DNS 声明 | `records.yml` | LAN 角色已按维护者说明对齐；声明接管范围未重查 | `infrastructure/dns/README.md`、维护者说明 | 同步旧描述；补新增记录流程 |
| docker | 宿主 Docker 网络管理 | `laptop` | 记录已迁移地址池 | `infrastructure/docker/README.md` | 已有 DN42 与挂载路径约束 |
| kata-lab | Kata VM 试验环境 | `历史 VMID 147` | 记录 9 月 14 日已销毁 | `infrastructure/kata-lab/README.md` | 保留验证历史，勿当现役 VM |
| kata-lxc-lab | LXC 内 Kata worker 试验 | `pve2 / 记录地址 192.168.10.128` | 记录 PoC 验证；非正式生产服务 | `infrastructure/kata-lxc-lab/README.md` | 明确与 microVM runner 的职责 |
| microvm-runner（历史目录名） | 动态 runner 的 homelab 基础设施记录 | 当前项目接口见 [Dynamic Runner](gitea-dynamic-runner.md) | 独立项目已更名并扩展到 Pod/VM，正在积极开发 | `infrastructure/microvm-runner/README.md`、独立项目文档 | 具体启用范围和实现进度以独立项目文档为准 |
| oci | 云主机、网络与站点互联 | `OCI ap-osaka-1` | 有恢复、接管与网络实施记录 | `infrastructure/oci/README.md` | 补跨站点使用入口 |
| [openbao](openbao.md) | 秘密管理与内部 CA | `bao.ad.ddupan.top` | 有部署与接管记录 | `infrastructure/openbao/README.md` | 已有登录、取密与运维入口指南 |
| proxmox | PVE、虚拟化与主机基础设施 | `PVE 管理入口` | 已有基础设施；README 混有设计设想 | `infrastructure/proxmox/README.md` | 分离当前环境与 workload identity 设想 |
| samba-ad | AD 身份、域 DNS 与域成员管理 | `dc1 / 192.168.10.5` | 有部署记录；维护者说明 DNS 部分已完成 | `infrastructure/samba-ad/README.md`、[LAN DNS](lan-dns.md) | 补入域和日常管理入口 |

## 集群

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| homelab | k3s 的 Flux reconciliation 入口 | `flux-system namespace` | 已有部署记录；部分汇总滞后 | `clusters/homelab/README.md` | 同步 SPIRE 与新增组件状态 |

## 计划、归档与范围外

- codex-proxy：维护者于 2026-09-16 表述为“应该是退役的”，按退役方向归档；源码目录仍保留，未确认现场清理情况，不再作为新接入对象。

- [旧 VictoriaMetrics Compose](victoriametrics-legacy.md)：旧配置和三个数据卷已于 2026-09-16 按维护者要求删除；现役监控在 platform/observability。

- [e5renew、research-auto](external-consumers.md)：GitHub 上的外部消费者，不属于 homelab 基础设施；仅保留归属入口。
- [Gitea Dynamic Runner](gitea-dynamic-runner.md)：正在积极开发的动态 Pod/VM runner，原名 gitea-microvm-runner；具体启用范围、调度和队列约定以项目文档为准。
- [PostgreSQL Tenant Operator](postgresql-tenant-operator.md)：计划中的 DBaaS 中间层，管理共享实例中的数据库与账号；README 记录为 API 骨架阶段，不代表服务已上线。
- [workload-sts](../architecture/workload-sts-history.md)：已归档的早期机器身份方案；停止开发、不部署 PoC，由 SPIFFE/SPIRE 替代。
- Backstage：规划中的服务目录与文档入口；本轮未发现独立部署目录。
- Keycloak、Casdoor：`archive/` 下有明确退役记录，替代入口为 Authelia。
- Traefik：归档目录保留历史 Gateway 示例，不作为当前接入流程。
- `docs/superpowers/`：已退役工作流，记录已完成的 CNPG/ZFS 迁移。
- `docs/cicd.md`、`docs/homelab-gitops-redesign.md`：部分实施设计，不代表所有阶段都上线。
- `docs/gitea-upgrade-plan.md`：包含已完成升级记录，现状以服务 README 和现场为准。
- 仓库外服务与独立源码仓库见[已确认的归属与范围](../verification.md#已确认的归属与范围)。
