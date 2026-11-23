# 服务总览

审阅日期：2026-11-23。以 homelab-infra main 为准；“状态依据”一栏写明事实来自配置、维护者说明还是现场验证。
来源路径相对于 [homelab-infra](https://git.ddupan.top/panxiao81/homelab-infra)。后续写作见[文档完善清单](../documentation-backlog.md)。

## 应用

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| [iam-login](iam-login.md) | 人类登录（AD 密码 + Passkey）与 OIDC 签发，所有应用的唯一 IdP | `sso.ddupan.top` | 2026-10-11 起全部 RP 已切换（Gitea、Grafana、Backstage、OpenBao、Incus、artifact-keeper、Ayatori）；Authelia、Hydra 已退役 | homelab-infra `apps/iam-login/`、iam-login 仓库 | 无发布周期，main 即当前版本；源码 README 的管理组仍写 Domain Admins（实为 `platform-admins`） |
| [backstage](backstage.md) | 服务目录与文档门户（TechDocs） | `backstage.lab.ddupan.top` | 配置：iam-login 登录，数据库为 pg-prod 租户 | `apps/backstage/README.md` | 登录与目录内容未现场验收 |
| [blocky](lan-dns.md) | LAN 主 DNS、广告过滤、分流 | `192.168.10.127:53` | 维护者说明已作为 DHCP 主 DNS，上游为路由器 | 维护者 2026-09-16 说明、`apps/blocky/README.md` | 无需逐台确认主机；旧源码说明待同步 |
| [gitea](gitea.md) | 代码托管与 Actions | `git.ddupan.top`（OCI，Cloudflare 代理） | 2026-11-05 迁到 OCI A1（Compose + SQLite）；k3s 副本 2026-11-11 删除 | `infrastructure/oci/ansible`（role `gitea`） | 备份：OCI 2 天 → Google Drive 30 天；GitHub `ddupan` 镜像 |
| http-echo | Flux 部署与漂移修复 canary | `集群内` | 记录已验证 | `apps/http-echo/README.md` | 已有验证步骤 |
| [marker](marker.md) | GPU 文档转换 API | `集群内端口 8001` | 配置与部署指南；未附上线记录 | `apps/marker/README.md` | 已有转换示例；部署镜像仍为占位符 |
| netboot | PXE 与系统安装 | `192.168.10.127` | 有部署及使用记录 | `apps/netboot/README.md` | 已有客户端启动说明 |
| [nexus](nexus.md) | 制品仓库；少量尚未迁移的 CI 依赖 | `nexus.lab.ddupan.top` | 正式使用；AD LDAPS 登录；维护者 2026-11-18 说明多数 CI 依赖已改走 artifact-keeper | `apps/nexus/README.md` | 列出并迁走剩余 CI 消费者；外部 PostgreSQL 与备份恢复测试 |
| [openviking](openviking.md) | 上下文检索服务 | `记录端口 1933 / 8020` | 配置与部署指南；未附上线记录 | `apps/openviking/README.md` | 已有导入、任务查询、检索与原文读取指南 |
| [ps3netsrv](ps3netsrv.md) | PS3 网络内容服务 | `宿主 TCP 38008；地址未记录` | Docker 运维文档记录运行 | `apps/ps3netsrv/docker-compose.yml` | 已有客户端与内容目录指南 |
| [seaweedfs](seaweedfs.md) | S3 对象存储 | `s3.lab.ddupan.top` | zot、Terraform state、artifact-keeper 使用 | `apps/seaweedfs/README.md` | 源码 README 仍写旧名 `s3.ad` |
| [shared-etcd](shared-etcd.md) | homelab 共享协调与选主存储 | etcd-pve1/2/3，mTLS，见服务页 | 三成员均在 PVE（etcd-pve3 取代 laptop，#570），由 Cinc 管理；消费者 Patroni pg-prod、pg-sandbox | `infrastructure/etcd/README.md` | 原生指标、续签与维护告警已接入 |
| [shared-postgresql](shared-postgresql.md) | k3s 外共享 PostgreSQL（Patroni） | `pg-prod.lab.ddupan.top`（Ayatori LB）/ `pg-dev` | 生产主从运行；租户经 Ayatori 申请；CNPG 2026-10-13 退役、应用已全部迁移 | `infrastructure/shared-postgresql/README.md`、`clusters/ayatori-*/` | 源码仍有 VyOS 旧入口遗留（README、探测、`pg-prod.ad` 记录） |
| [smtp-relay](smtp-relay.md) | 应用发信中继（boky/postfix → OCI Email Delivery） | `smtp-relay.smtp-relay.svc.cluster.local:25`；PVE 节点经 `192.168.10.127:25` | 2026-11-12 起改走 OCI Email Delivery（#735）；发件人仅 `noreply@ddupan.top` | `apps/smtp-relay/README.md` | 来源网段是唯一门禁 |
| [tailscale](tailscale.md) | 远程网络与子网路由 | `Tailscale 网络` | 有配置 | `apps/tailscale/subnet-routes.sh` | 已有远程访问与路由边界指南 |
| [vlmcsd](vlmcsd.md) | KMS 兼容服务，使用范围未记录 | `宿主 TCP 1688；地址未记录` | 仅发现配置 | `apps/vlmcsd/compose.yaml` | 已有协议入口与客户端指南；未查询现场 |
| [ai-gateway](ai-gateway.md) | LLM 统一入口，按客户端发 key（Anthropic 经 SPIRE WIF、ChatGPT Plus 经 CLIProxyAPI） | `ai.lab.ddupan.top`；key 管理 `ai-keys.lab.ddupan.top` | 配置；2026-11-03 起为模型 API 入口 | `apps/ai-gateway/README.md` | 未现场验证 |
| [artifact-keeper](artifact-keeper.md) | CI 依赖下载的主要 pull-through 缓存（PyPI/npm/Go/Galaxy/Terraform/Docker Hub 等） | `artifacts.lab.ddupan.top` | 配置；维护者 2026-11-18 说明多数 CI 流量已迁入 | `apps/artifact-keeper/values.yaml`（无 README） | 剩余 Nexus 消费者未列出 |
| [homepage](homepage.md) | 所有应用的起始页 | `home.lab.ddupan.top` | 配置；2026-11-03 上线 | `apps/homepage/README.md` | 未现场验证 |
| [e5renew](e5renew.md) | 外部项目 e5renew 的 homelab 部署（仅部署与依赖） | `e5renew.ddupan.top`（Cloudflare Tunnel） | 配置：Flux + pg-prod 租户 | `apps/e5renew/README.md` | Entra secret 到期时间未核对 |
| [research-auto](research-auto.md) | 外部项目 research-auto 的 homelab 部署（仅部署与依赖） | Tailscale LoadBalancer（主机名未记录） | 配置：Flux + pg-prod 租户 | `apps/research-auto/README.md` | 入口主机名、PVC/S3 备份未记录 |
| [zot](zot.md) | OCI 镜像与制品仓库 | `zot.lab.ddupan.top / zot-push.lab.ddupan.top`（ad 名称过渡保留） | 配置；issuer `spire-oidc.ddupan.top` | `apps/zot/README.md` | publisher 全部切到 lab 后退役 ad 名称 |

## 平台

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| [cert-manager](../guides/publish-service.md) | 签发与续期 TLS 证书 | `ClusterIssuer API` | 记录已接管 Flux | `platform/cert-manager/README.md` | 已有新服务证书复用与接入指南 |
| [envoy-gateway](../guides/publish-service.md) | LAN HTTP 入口与认证集成 | `192.168.10.127:443` | 记录已接管 Flux | `platform/envoy-gateway/README.md` | 已有 DNS、路由、认证与发布路径指南 |
| [external-secrets](external-secrets.md) | OpenBao 到 Kubernetes 的秘密投射 | `Kubernetes API` | Helm 记录已接管；对象范围需区分 | `platform/external-secrets/README.md` | 已有字段投射示例与 ownership 边界 |
| [k3s DNS](k3s-dns.md) | 集群 CoreDNS 定制 | `集群内 DNS` | 仅发现 DNS 配置 | `platform/k3s/Corefile.desired` | 已有集群 DNS 使用与配置边界说明 |
| [nats](nats.md) | 集群共享消息与 JetStream 队列 | `nats.ad.ddupan.top:4222` | 2026-10-05 已缩容停用，保留配置与 PVC；runner 已移除队列依赖 | `platform/nats/README.md`、2026-10-06 现场排障 | 恢复时同步启用 PodMonitor 与专用告警 |
| [observability / Grafana](grafana.md) | Grafana、指标、日志和追踪 | `grafana.lab.ddupan.top` | 配置：iam-login 登录，Tailscale ingress 已停用 | `platform/observability/README.md` | 已有看板、指标与日志查询指南 |
| [openebs](openebs.md) | k3s 本地 ZFS 持久卷 | `localpv-zfs-ceph StorageClass` | 记录已接管 Flux | `platform/openebs/README.md` | 已有 PVC 示例、绑定与数据回收边界 |
| [spire](spire.md) | 跨基础设施的统一机器身份入口 | `Workload API / spire-oidc.ddupan.top` | 配置：issuer 已迁到 `spire-oidc.ddupan.top`（2026-11） | `platform/spire/README.md`、[#34](https://git.ddupan.top/panxiao81/homelab-infra/issues/34) | 已有接入指南 |
| [sandbox cluster](sandbox-cluster.md) | OpenSandbox、CI 与 agent 用的双节点 k3s | `sandbox-k8s.lab.ddupan.top:6443` / `:8080`（Ayatori LB） | 配置；入口 2026-11-03 迁到 Ayatori LB | `infrastructure/sandbox-cluster/README.md`、`clusters/sandbox/` | kubeconfig 获取与 datastore 备份未记录 |

## 基础设施

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| cloudflared | 公网 Tunnel 与 DNS | `Cloudflare 边缘配置` | 有现有资源接管记录 | `infrastructure/cloudflared/terraform/README.md` | 明确配置权威位置与服务发布流程 |
| [dns](lan-dns.md) | LAN DNS：Blocky + PowerDNS（`lab.ddupan.top`）+ AD 域 | `192.168.10.127:53`；记录随创建者或 `terraform/hosts.tf` | 配置：external-dns 发布 HTTPRoute 名称；`records.yml` 只剩 split-horizon | `infrastructure/dns/README.md`、维护者说明 | DNS HA（单 DC 容错）进行中 |
| docker | 宿主 Docker 网络管理 | `laptop` | 记录已迁移地址池 | [架构约束](../architecture/constraints.md) 与 IaC | Docker bridge 使用 `172.28.0.0/16`，避免 DN42 |
| [ayatori](ayatori.md) | 基础设施控制平面（Database、LoadBalancer 领域） | `ayatori-dev` / `ayatori-prod` LXC 上的 k0s API | 配置：两环境 v0.4.0，由 Chef 部署（cd0e04b）；iam-login 登录；Compute 领域进行中 | `infrastructure/chef/policies/ayatori-*.rb`、`clusters/ayatori-*/` | 经 `clusters/ayatori-<env>` 申请数据库与负载均衡；离机备份待建 |
| [incus](incus.md) | laptop 系统容器与新 Linux VM 管理 | `https://incus.lab.ddupan.top`；本地 `sudo incus` | 配置：iam-login + `platform-admins`；Terraform root 归 CI，手改会被回滚 | `infrastructure/incus/README.md` | 离机备份待建 |
| [oci](oci.md) | 云主机、网络与站点互联 | `OCI ap-osaka-1` | 有恢复、接管与网络实施记录 | `infrastructure/oci/README.md` | 已有登录、站点网络与维护入口 |
| [openbao](openbao.md) | 秘密管理与内部 CA | `bao.lab.ddupan.top` | 2026-11-05 起 TPM 自动解封，Shamir 改为恢复密钥；人类经 iam-login 登录 | `infrastructure/openbao/README.md` | 异地恢复演练待完成 |
| [proxmox](proxmox.md) | PVE、虚拟化与主机基础设施 | `PVE 管理入口` | 已有基础设施 | `infrastructure/proxmox/ansible/` 与 `README-ha.md` | 已有管理入口；sandbox LB/根盘恢复流程见服务页；身份与 runner 设计见独立项目 |
| [vyos-router](vyos-router.md) | SDN 网关与 DHCP、到 IX/LB/OCI 的 BGP、DN42 出口 | `192.168.10.2` | 2026-11-18 现场验证 BGP 与配置收敛（changed=0） | `infrastructure/proxmox/ansible/roles/vyos_router/` | 已有检查与改配置流程 |
| [chef / Cinc](chef.md) | 节点配置：policy + lock，`converge.py` 推送，CI why-run、合并即 apply | `infrastructure/chef/converge.py` | 配置 | `infrastructure/chef/README.md` | 源码 README 中 LB 节点仍写“待部署” |
| [ayatori-loadbalancer](ayatori-loadbalancer.md) | Ayatori LB 数据面（HAProxy + lb-agent，BGP 向 VyOS 宣告 VIP） | VIP 池 `10.62.0.0/24`（prod）、`10.62.1.0/24`（dev） | 配置 | `infrastructure/loadbalancer/README.md`、`clusters/ayatori-prod/` | 源码 README 部署步骤过时 |
| [gcp](gcp.md) | CI 云端池（GKE Autopilot）、组织授权与账单告警 | `runs-on: [cloud]` / `[cloud-small]` | 配置；gcp-ci 由 CI 管理 | `infrastructure/gcp-*/terraform/README.md` | 赠金 2027-02-08 到期 |
| [samba-ad](samba-ad.md) | AD 身份、域 DNS 与域成员管理 | `dc1 / 192.168.10.5` | 有部署记录；维护者说明 DNS 部分已完成 | `infrastructure/samba-ad/README.md`、[LAN DNS](lan-dns.md) | 已有入域、目录浏览与日常管理入口 |

## 集群

| 组件 | 用途 | 记录入口 | 状态依据 | 来源 | 文档缺口 / 下一步 |
|---|---|---|---|---|---|
| homelab | k3s 的 Flux reconciliation 入口 | `flux-system namespace` | 已有部署记录；部分汇总滞后 | `clusters/homelab/README.md` | 同步 SPIRE 与新增组件状态 |
| sandbox | sandbox k3s 的 Flux 入口 | 见 [sandbox cluster](sandbox-cluster.md) | 配置 | `clusters/sandbox/` | — |
| ayatori-dev / ayatori-prod | Ayatori 资源声明（数据库租户、负载均衡） | 见 [Ayatori](ayatori.md) | 配置 | `clusters/ayatori-dev/`、`clusters/ayatori-prod/` | — |

## 已退役

页面保留退役原因与替代入口，不再作为接入对象。

| 组件 | 原用途 | 退役 | 替代 |
|---|---|---|---|
| [hydra](hydra.md) | 旧 OIDC 签发 PoC | 2026-10-05 下线，清单存 `archive/hydra`（82322df） | [iam-login](iam-login.md) |
| [authelia](authelia.md) | 旧主 OIDC broker 与 forward-auth | 2026-10-11 退役（b3b4d8f） | [iam-login](iam-login.md)；Gateway 不再有 forward-auth |
| [litellm-gateway](litellm-gateway.md) | 旧模型 API 网关 | 2026-11-03 退役（b8f8e1f） | [ai-gateway](ai-gateway.md) |
| [netbox](netbox.md) | 网络资产与地址管理评估 | 2026-10-04 下线（9532e11） | `infrastructure/network/ipam.yml` + DNS；不再引入 UI 权威数据 |
| gitea-runner | 旧常驻 Gitea Actions runner | 2026-09-21 删除（bb24c76） | [Dynamic Runner](gitea-dynamic-runner.md) 各池 |
| kata-lab / kata-lxc-lab / microvm-runner | Kata 与 microVM 试验目录 | 2026-10-01 归档到分支 `archive/kata-microvm-20260917`（55bb5be） | [Dynamic Runner](gitea-dynamic-runner.md)、[sandbox cluster](sandbox-cluster.md) 的 Kata |

## 计划、归档与范围外

- codex-proxy：维护者于 2026-09-16 表述为“应该是退役的”，按退役方向归档；源码目录仍保留，未确认现场清理情况，不再作为新接入对象。

- [旧 VictoriaMetrics Compose](victoriametrics-legacy.md)：旧配置和三个数据卷已于 2026-09-16 按维护者要求删除；现役监控在 platform/observability。

- [e5renew、research-auto 的范围变更](external-consumers.md)：2026-11-18 起纳入本库（只记部署与依赖），见上方应用表。
- [Gitea Dynamic Runner](gitea-dynamic-runner.md)：动态 Pod/VM/云端 runner 池，原名 gitea-microvm-runner；2026-10-05 起各 worker 直接作为 Gitea runner 拉任务，不再经 NATS。
- [PostgreSQL Tenant Operator](postgresql-tenant-operator.md)：计划中的 DBaaS 中间层，管理共享实例中的数据库与账号；现转入 Ayatori Database，采用独立 Database 资源与 Tenant 申请；设计修订不代表服务上线。
- [workload-sts](../architecture/workload-sts-history.md)：已归档的早期机器身份方案；停止开发、不部署 PoC，由 SPIFFE/SPIRE 替代。
- Keycloak、Casdoor：`archive/` 下有明确退役记录，替代入口为 iam-login（Authelia 亦已退役）。
- Traefik：归档目录保留历史 Gateway 示例，不作为当前接入流程。
- `docs/superpowers/`：已退役工作流，记录已完成的 CNPG/ZFS 迁移。
- `docs/cicd.md`、`docs/homelab-gitops-redesign.md`：部分实施设计，不代表所有阶段都上线。
- `docs/gitea-upgrade-plan.md`：包含已完成升级记录，现状以服务 README 和现场为准。
- 仓库外服务与独立源码仓库见[已确认的归属与范围](../verification.md#已确认的归属与范围)。
