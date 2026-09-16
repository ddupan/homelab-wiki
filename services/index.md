# 服务总览

审阅日期：2026-09-16。以下覆盖源码工作区 apps/、platform/、infrastructure/ 的一级组件，以及集群入口。
**所有条目本轮均未现场验证。** 状态栏表示文档、ticket 或配置证据，不表示实时健康状态。
SPIFFE/SPIRE 已按维护者授权补读 #34；其他条目仍为初轮工作区盘点，查询前先向维护者对齐。
来源路径相对于 [homelab-infra](https://git.ddupan.top/panxiao81/homelab-infra)；包含未提交内容，见首页证据边界。

入口按来源记录列出，访问范围和可达性仍需验证。缺口详情见[待核实清单](../verification.md)。

## 应用

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| authelia | 统一登录与 OIDC | `auth.ddupan.top` | 记录已部署；旧 README 冲突 | `apps/authelia/README.md` | 补当前登录与接入指南 |
| [blocky](lan-dns.md) | LAN 主 DNS、广告过滤、分流 | `192.168.10.127:53` | 维护者说明已作为 DHCP 主 DNS，上游为路由器 | 维护者 2026-09-16 说明、`apps/blocky/README.md` | 无需逐台确认主机；旧源码说明待同步 |
| codex-proxy | 代理服务，具体接口待确认 | `待核实` | 仅发现配置 | `apps/codex-proxy/docker-compose.yml` | 缺 README 与使用说明 |
| gitea | 代码托管与 Actions | `git.ddupan.top` | 记录已部署 | `apps/gitea/README.md` | 补首次使用与 runner 选择 |
| http-echo | Flux 部署与漂移修复 canary | `集群内` | 记录已验证 | `apps/http-echo/README.md` | 已有验证步骤 |
| litellm-gateway | 模型 API 网关，实际消费者待确认 | `待核实` | 仅发现配置 | `apps/litellm-gateway/docker-compose.yml` | 缺 README 与接入说明 |
| marker | GPU 文档转换 API | `集群内端口 8001` | 配置与部署指南；上线待核实 | `apps/marker/README.md` | 缺 API 使用例子 |
| netboot | PXE 与系统安装 | `192.168.10.127` | 有部署及使用记录 | `apps/netboot/README.md` | 已有客户端启动说明 |
| netbox | 网络资产与地址管理评估 | `netbox.ad.ddupan.top` | 记录已部署；评估用途 | `apps/netbox/README.md` | 补面向浏览者的使用路径 |
| openviking | 上下文检索服务 | `记录端口 1933 / 8020` | 配置与部署指南；上线待核实 | `apps/openviking/README.md` | 缺导入、查询的完整例子 |
| ps3netsrv | PS3 网络内容服务 | `待核实` | Docker 运维文档记录运行 | `apps/ps3netsrv/docker-compose.yml` | 缺客户端使用与挂载说明 |
| seaweedfs | S3 对象存储 | `s3.ad.ddupan.top` | zot 文档记录已使用 | `apps/seaweedfs/README.md` | 补客户端接入、备份与恢复 |
| shared-postgresql | 共享 PostgreSQL / CNPG | `shared-db namespace` | 历史迁移记录已完成 | `apps/shared-postgresql/migration.md` | 缺服务首页、租户接入说明 |
| smtp-relay | 应用经 Microsoft 365 发信 | `smtp-relay.smtp-relay.svc.cluster.local:25` | 有配置与测试指南；上线待核实 | `apps/smtp-relay/README.md` | 核实发信链路与消费者 |
| tailscale | 远程网络与子网路由 | `Tailscale 网络` | 有配置；本轮未读敏感安装脚本 | `apps/tailscale/subnet-routes.sh` | 缺 README、路由与客户端说明 |
| victoriametrics | 旧 Compose 监控栈 | `待核实` | 文档称被平台栈替代；残留待查 | `apps/victoriametrics/compose.yaml` | 明确退役或现存职责 |
| vlmcsd | KMS 兼容服务，使用范围待确认 | `待核实` | 仅发现配置 | `apps/vlmcsd/compose.yaml` | 缺 README 与状态说明 |
| zot | OCI 镜像与制品仓库 | `zot.ad.ddupan.top / zot-push.ad.ddupan.top` | 文档记录 9 月 16 日验收 | `apps/zot/README.md` | 已有拉取示例；长期 CI 发布仍待接入 |

## 平台

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| cert-manager | 签发与续期 TLS 证书 | `ClusterIssuer API` | 记录已接管 Flux | `platform/cert-manager/README.md` | 已有签发和验证说明 |
| envoy-gateway | LAN HTTP 入口与认证集成 | `192.168.10.127:443` | 记录已接管 Flux | `platform/envoy-gateway/README.md` | 已有服务接入说明 |
| external-secrets | OpenBao 到 Kubernetes 的秘密投射 | `Kubernetes API` | Helm 记录已接管；对象范围需区分 | `platform/external-secrets/README.md` | 补新增秘密引用的使用流程 |
| gitea-runner | 可信 Gitea Actions 任务执行 | `Gitea Actions` | 记录已接管 Flux | `platform/gitea-runner/README.md` | 补 workflow label 与使用限制 |
| k3s | 集群 CoreDNS 定制 | `集群内 DNS` | 仅发现 DNS 配置 | `platform/k3s/Corefile.desired` | 缺组件 README |
| nats | 共享消息与 JetStream 队列 | `nats.ad.ddupan.top:4222` | 有配置与拓扑记录；现场待核实 | `platform/nats/README.md` | 补生产/消费示例与队列检查 |
| observability | Grafana、指标、日志和追踪 | `grafana.ad.ddupan.top` | 记录已接管 Flux；9 月 16 日变更入口 | `platform/observability/README.md` | 补看板和查询使用指南 |
| openebs | k3s 本地 ZFS 持久卷 | `localpv-zfs-ceph StorageClass` | 记录已接管 Flux | `platform/openebs/README.md` | 已有运维检查；补 PVC 使用边界 |
| [spire](spire.md) | 跨基础设施的统一机器身份入口 | `Workload API / spire-oidc.ad.ddupan.top` | #34 记录基础设施与最小 OpenBao PoC 已完成；后续集成进行中 | [#34](https://git.ddupan.top/panxiao81/homelab-infra/issues/34)、[RUNBOOK](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/spire/RUNBOOK.md) | 已有接入指南；动态任务以 ticket 为准 |

## 基础设施

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| cloudflared | 公网 Tunnel 与 DNS | `Cloudflare 边缘配置` | 有现有资源接管记录 | `infrastructure/cloudflared/terraform/README.md` | 明确配置权威位置与服务发布流程 |
| [dns](lan-dns.md) | 跨视图 DNS 声明 | `records.yml` | LAN 角色已按维护者说明对齐；声明接管范围未重查 | `infrastructure/dns/README.md`、维护者说明 | 同步旧描述；补新增记录流程 |
| docker | 宿主 Docker 网络管理 | `laptop` | 记录已迁移地址池 | `infrastructure/docker/README.md` | 已有 DN42 与挂载路径约束 |
| kata-lab | Kata VM 试验环境 | `历史 VMID 147` | 记录 9 月 14 日已销毁 | `infrastructure/kata-lab/README.md` | 保留验证历史，勿当现役 VM |
| kata-lxc-lab | LXC 内 Kata worker 试验 | `pve2 / 记录地址 192.168.10.128` | 记录 PoC 验证；非正式生产服务 | `infrastructure/kata-lxc-lab/README.md` | 明确与 microVM runner 的职责 |
| microvm-runner（历史目录名） | 动态 runner 的 homelab 基础设施记录 | 当前项目接口见 [Dynamic Runner](gitea-dynamic-runner.md) | 旧工作区记录 PoC；独立项目已更名并扩展到 Pod/VM，实际启用范围未查询 | `infrastructure/microvm-runner/README.md`、独立项目 README | 软件与基础设施职责已明确；旧 kind-microvm label 不作为当前接口 |
| oci | 云主机、网络与站点互联 | `OCI ap-osaka-1` | 有恢复、接管与网络实施记录 | `infrastructure/oci/README.md` | 补跨站点使用入口 |
| openbao | 秘密管理与内部 CA | `bao.ad.ddupan.top` | 有部署与接管记录 | `infrastructure/openbao/README.md` | 补日常使用和恢复入口 |
| proxmox | PVE、虚拟化与主机基础设施 | `PVE 管理入口` | 已有基础设施；README 混有设计设想 | `infrastructure/proxmox/README.md` | 分离当前环境与 workload identity 设想 |
| samba-ad | AD 身份、域 DNS 与域成员管理 | `dc1 / 192.168.10.5` | 有部署记录；维护者说明 DNS 部分已完成 | `infrastructure/samba-ad/README.md`、[LAN DNS](lan-dns.md) | 补入域和日常管理入口 |

## 集群

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| homelab | k3s 的 Flux reconciliation 入口 | `flux-system namespace` | 已有部署记录；部分汇总滞后 | `clusters/homelab/README.md` | 同步 SPIRE 与新增组件状态 |

## 计划、归档与范围外

- [Gitea Dynamic Runner](gitea-dynamic-runner.md)：独立开发的动态 Pod/VM runner，原名 gitea-microvm-runner；README 描述 bootstrap 实现与长期调度路线，部署范围尚未查询。
- [PostgreSQL Tenant Operator](postgresql-tenant-operator.md)：计划中的 DBaaS 中间层，管理共享实例中的数据库与账号；README 记录为 API 骨架阶段，不代表服务已上线。
- [workload-sts](../architecture/workload-sts-history.md)：已归档的早期机器身份方案；停止开发、不部署 PoC，由 SPIFFE/SPIRE 替代。
- Backstage：规划中的服务目录与文档入口；本轮未发现独立部署目录。
- Keycloak、Casdoor：`archive/` 下有明确退役记录，替代入口为 Authelia。
- Traefik：归档目录保留历史 Gateway 示例，不作为当前接入流程。
- `docs/superpowers/`：已退役工作流，记录已完成的 CNPG/ZFS 迁移。
- `docs/cicd.md`、`docs/homelab-gitops-redesign.md`：部分实施设计，不代表所有阶段都上线。
- `docs/gitea-upgrade-plan.md`：包含已完成升级记录，现状以服务 README 和现场为准。
- 仓库外服务与独立源码仓库见[盘点盲区](../verification.md#盘点盲区)。
