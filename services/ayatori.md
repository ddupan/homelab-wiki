---
title: Ayatori 控制面
lifecycle: experimental
evidence: live-verified
last_reviewed: 2026-10-07
last_verified: 2026-10-07
sources:
  - https://git.ddupan.top/panxiao81/ayatori/src/tag/v0.1.0/deploy/README.md
  - https://git.ddupan.top/panxiao81/ayatori/pulls/27
  - https://git.ddupan.top/panxiao81/ayatori/pulls/28
  - https://git.ddupan.top/panxiao81/ayatori/pulls/30
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/198
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/202
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/204
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/208
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/211
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/216
  - https://git.ddupan.top/panxiao81/ayatori/pulls/32
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/224
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/227
  - 2026-10-04 v0.1.1 Dev/Prod 部署与 GitOps 同步、权限拒绝、prune 现场验证
  - https://git.ddupan.top/panxiao81/ayatori/pulls/33
  - https://git.ddupan.top/panxiao81/ayatori/pulls/34
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/222
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/232
  - 2026-10-04 v0.1.2 部署、手动备份、临时 LXC 恢复演练现场验证
  - https://git.ddupan.top/panxiao81/ayatori/pulls/38
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/255
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/260
  - 2026-10-05 v0.1.3 部署、中央采集与 Telegram 告警端到端现场验证
  - https://git.ddupan.top/panxiao81/ayatori/releases/tag/v0.1.4
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/262
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/263
  - 2026-10-07 v0.1.4 部署与证书到期指标、规则加载现场验证
  - 维护者于 2026-10-04 授权部署 Dev 与 Prod，并确认 Dev 可直接试验、Prod 只走发布流程
  - 2026-10-04 Dev/Prod 部署、幂等重跑与 Database 端到端验收（本页“当前状态与证据”）
---

# Ayatori 控制面

## 它解决什么问题

Ayatori 是 homelab 的基础设施控制平面：以 kube-apiserver + CRD 提供版本化 API，由
ayatori-manager 协调后端。当前上线的唯一领域是 Database：在共享 PostgreSQL 上按
Tenant 申请供应数据库与登录角色，把应用凭据写入 OpenBao 并在 Tenant status 公布位置，
释放后按 Retain/Delete 处置，支持导入已有数据库与重新开放。边界见
[控制面边界](../architecture/ayatori-control-plane.md)，资源模型见
[DBaaS 设计](postgresql-tenant-operator.md)。成熟度为 experimental：Dev 与 Prod 已上线并完成
端到端验收；Prod 已承载首个真实 Tenant（`iam-login`）；控制面每日本机备份，尚无离机副本。

## 从哪里使用

| 环境 | 主机 | API | PostgreSQL 实例 | Bao 应用凭据前缀 |
|---|---|---|---|---|
| Dev | `ayatori-dev.lab.ddupan.top`（192.168.10.11） | `https://192.168.10.11:6443` | `homelab-dev` → `pg-dev:5433` | `kv/ayatori/dev/applications/` |
| Prod | `ayatori-prod.lab.ddupan.top`（192.168.10.12） | `https://192.168.10.12:6443` | `homelab-prod` → `pg-prod:5432` | `kv/ayatori/prod/applications/` |

- 两台都是 [Incus](incus.md) 上的非特权 LXC，仅 LAN 可达。
- 登录：当前只有主机管理员入口，`ssh panxiao81@ayatori-<env>.lab.ddupan.top`（也接受 Bao SSH CA 签发的
  短期证书）后 `sudo k0s kubectl ...`。尚未给人或其他系统签发 kubeconfig，也没有接入 IdM。
- 前提：两台都是 Cinc 节点（[Chef](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/chef)），部署只需到 LXC 的 SSH（`panxiao81` 免密 sudo）；
  首次 SPIRE enrollment 另需操作者的 Bao token。

## 第一次使用

### 推荐：在 homelab-infra 以 GitOps 申请

每个环境的 Flux 从 homelab-infra `main` 同步 `clusters/ayatori-dev/` 或 `clusters/ayatori-prod/`。
在对应目录提交 PR，新增文件并加入该目录 `kustomization.yaml` 的 `resources`：

```yaml
# clusters/ayatori-prod/myapp.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: myapp
---
apiVersion: database.ayatori.ddupan.top/v1alpha1
kind: PostgreSQLTenant
metadata: {name: myapp, namespace: myapp}
spec:
  provision: {instanceRef: {name: homelab-prod}, database: myapp, loginRole: myapp}
  extensions: [pgcrypto]
```

合并后约 1 分钟内同步。目录只允许 Namespace、PostgreSQLTenant、PostgreSQLDatabase，其他对象会
使整个同步失败（`gitops-tenants` 无权限），需先移除。`prune` 开启：从目录删除 Tenant 即释放其
Database（默认 Retain，不删数据）；删除 namespace 会连带释放其中所有 Tenant。导入已有数据库
（`source: Import`）同样在此声明 PostgreSQLDatabase。

### 在主机上直接试验（仅 Dev）

不经 Git 直接创建（Dev 允许随意试验；Prod 只经上面的 GitOps 目录）：

```bash
ssh panxiao81@ayatori-dev.lab.ddupan.top
sudo k0s kubectl create namespace demo
sudo k0s kubectl apply -f - <<'EOF'
apiVersion: database.ayatori.ddupan.top/v1alpha1
kind: PostgreSQLTenant
metadata: {name: demo, namespace: demo}
spec:
  provision: {instanceRef: {name: homelab-dev}, database: demo_app, loginRole: demo_app}
  extensions: [pgcrypto]
EOF
sudo k0s kubectl -n demo get postgresqltenant demo -o jsonpath='{.status}'
```

预期数秒内 `Ready=True / CredentialsAvailable`，status 给出 `credentialRef`（KV v2 mount
`kv` 与路径）、`credentialVersion` 与不含认证信息的 `credentialURL`。凭据只交付到 OpenBao，
由消费方集群用自己的身份读取并投射（例如其 ESO）。消费方读取权限按应用单独授权：在
homelab-infra `infrastructure/openbao/terraform` 为消费方 SA 建 role 与只读该凭据路径的 policy，
参照 `apps/iam-login/README.md` 的 `iam-login-database`（ExternalSecret 固定 Tenant status 的
`credentialVersion`）。

清理：自动生成的 Database 默认 `reclaimPolicy: Retain`。要连同数据删除，先把该 Database
改为 `Delete` 再删 Tenant；Retain 释放后改策略会被 CEL 拒绝。

## 日常操作与限制

- 发布：攒一批变更再发版（功能 PR 不改版本号）。Ayatori 仓库打 annotated `vX.Y.Z` git tag（说明即发布
  说明，Release 工作流自动生成 Gitea Release），Release 工作流用 ko 构建 manager 镜像并以同名 tag
  推送 [zot](zot.md) `panxiao81/ayatori-manager`。Flux 同步的清单与镜像是同一组制品；节点部署
  （cookbook）是另一条版本线。
- 完全不可用的 release 不升版本：修复合并后删除并重打同名 tag，Release 覆盖同名镜像
  （CI 身份有 update，本机开发身份可读写删除），policy 中的镜像 digest 随之更新。
- 部署：homelab-cookbooks 的 `homelab_ayatori` cookbook（节点基线由 `homelab_base` 负责），环境声明是
  homelab-infra `infrastructure/chef/policies/ayatori-<env>.rb`（release tag 与按 digest 固定的 manager
  镜像、PostgreSQL、GitOps、LB）。在 laptop 执行 `infrastructure/chef/converge.py -l ayatori-<env>`
  （先 `--why-run`）。Promotion 即把 prod policy 的 release 与 digest 改为 Dev 已验收的版本。
- Dev 可用本地构建、按 digest 引用的镜像试验；Prod 只走 release + promotion。
- 运行形态：k0s controller-only（apiserver、etcd、只开 namespace 与证书签发相关控制器的 KCM）为 systemd；
  ESO、Flux source/kustomize-controller、ayatori-manager 为 podman quadlet（host 网络、只读根、
  各自的客户端证书，由 client-credentials 容器以 CSR 申请并自行续签，Ayatori ADR-0021）。Flux 从 release tag 同步
  Database CRD 与控制面对象；k0s、ESO、Flux 版本与 digest 固定在 cookbook 属性。
- 管理凭据：ESO 以 `kubernetes-ayatori-<env>` 登录 OpenBao，只读
  `kv/infra/postgresql/ayatori/<env>`，同步为 `ayatori-system/homelab-<env>-admin`。
- 限制：Flux 不选主、单实例；kustomize-controller 为 cluster-admin；第三方镜像只固定 digest，
  未验签；客户端证书在有效期过去 70–90% 时自行续签，续签失败过期时重新
  converge 即重新签发。宿主负载很高（2026-10-04 约 97/12 核）时 manager 可能因 Lease 超时退出，由
  systemd 自动重启。

## 监控与告警

中央 vmagent 以 VMStaticScrape（homelab-infra `platform/observability/metrics/scrapes/ayatori.yaml`）
采集每台 LXC 的 6 个目标，job 为 `ayatori-node`、`ayatori-kube-state-metrics`、`ayatori-manager`、
`ayatori-external-secrets`、`ayatori-flux-{source,kustomize}-controller`，带 `cluster=ayatori-<env>`。
规则在 `rules/ayatori.yaml`：目标不可用/缺失、控制面服务未运行、Instance 未就绪在 Prod 为 critical；
备份失败/过期、磁盘、内存、Flux 与 ESO 同步、Database 冲突/不可用、Tenant 未就绪、reconcile 错误为
warning。告警经 Alertmanager 发往 Telegram：采集标签 `env=dev` 的告警进 dev 频道（`telegram-dev`），
其余按级别进生产频道；新增规则若结果不带采集标签（如 `absent()`），须显式写 `env`。

LXC 内 node_exporter 只开启可信 collector：非特权 LXC 中 loadavg、vmstat、hwmon 是宿主数据，宿主负载
由宿主自己的 node-exporter 负责。CR 状态（Flux、ExternalSecret/SecretStore、Instance/Database/Tenant）
由 LXC 上的 kube-state-metrics 导出，ESO v2 自身不导出状态条件指标。
证书到期：`ayatori-cert-metrics.timer` 每小时导出 k0s PKI 与各 kubeconfig 客户端证书到期时间，剩余 30 天
warning、7 天 critical；kubeconfig 删除后重跑部署即重签，PKI 服务端证书重启 `k0scontroller` 轮换。

## 出问题时

只读检查（在对应主机 `sudo` 执行）：

```bash
systemctl is-active k0scontroller external-secrets flux-source-controller flux-kustomize-controller ayatori-manager
k0s kubectl get gitrepository,kustomization -A
k0s kubectl -n ayatori-system get secretstore,externalsecret
k0s kubectl get postgresqlinstance,postgresqldatabase
k0s kubectl get postgresqltenant -A
journalctl -u ayatori-manager -n 80 --no-pager
```

正常：五个服务 active；GitRepository 与两个 Kustomization Ready 且 revision 为部署的 tag；
SecretStore Valid、ExternalSecret SecretSynced；Instance `Ready=True / ManagementReady`。

- OpenBao 登录 403：kubernetes auth 不持有 reviewer JWT，用登录 JWT 自身调用 TokenReview，
  因此 JWT 必须带 API audience；检查 role 的 SA 名称、namespace 与 mount 中的 k0s CA。
- Bao 侧修复后 ESO 仍在退避：给 SecretStore/ExternalSecret 加 `force-sync=<时间戳>` 注解立即重试。
- Database 状态以 `status.credentialPhase`、`status.resourcePhase` 与 Conditions 消息为准；
  冲突（Conflict）表示需要人工核对，controller 不会自动接管或扩大删除范围。

## 运维入口

- 部署、发布与已知限制：Ayatori [deploy/README.md](https://git.ddupan.top/panxiao81/ayatori/src/branch/main/deploy/README.md)；
  Database 设计：Ayatori `docs/database/`。
- 环境声明：homelab-infra `infrastructure/chef/policies/ayatori-<env>.rb`，GitOps 目录 `clusters/ayatori-<env>/`；OpenBao mount/role/policy：
  `infrastructure/openbao/terraform/auth.tf`、`policies/ayatori-*.hcl`；zot 授权：`apps/zot/values.yaml`；
  LXC：`infrastructure/incus/terraform/`。
- 依赖：Incus、OpenBao、共享 PostgreSQL、zot、Gitea（Flux 拉取与制品下载）、GitHub/ghcr
  （第三方 CRD 与镜像）。Gitea 或 zot 不可用只影响新部署，已运行实例不受影响。
- 备份：每日 `ayatori-backup.timer` 以 `k0s backup`（etcd 快照、PKI、k0s.yaml）写入 Incus custom volume
  `ayatori-<env>-backup`（容器内 `/var/backups/ayatori`，宿主 `/var/lib/incus/storage-pools/ayatori/custom/default_ayatori-<env>-backup/`），
  保留 7 份；实例另有每日快照保留 7 天。二者与实例同在 `ayatori` 池，**不是离机备份**；备份年龄告警
  尚未接入。应用凭据随 OpenBao 快照，应用数据随共享 PostgreSQL 备份（pg-dev 不备份）。
- 恢复：按原地址重建 LXC 后 `k0s restore` 并重跑部署，步骤见 Ayatori deploy/README。恢复较旧快照
  不会破坏外部资源，但需人工对账：快照后新建的 Database 以 `source: Import` 重新登记，快照后已删除的
  记录按 Retain 删除。

## 当前状态与证据

2026-10-04 维护者授权后部署。Dev 与 Prod 先以 v0.1.0 上线并验收（git `c0422d9`，manager 镜像
`sha256:ba3a63aab2a8c5ea0576aed1562f85003dd0f7437149e0d36ffcf81c846efff0`），Dev 二次部署 `changed=0`；
随后两环境升级到 v0.1.1（git `239ad34`，manager 镜像
`sha256:c64c4e932f6cfb7e9bf07db602af2d6da5065d33209640b88e629ea01a150391`，仅部署 role 增加 GitOps
目录同步），Flux 三个 Kustomization 均 Ready，Instance Ready。随后两环境升级到 v0.1.2（git `843ed2d`，
首个 buildx 发布的 manager 镜像 `sha256:441480eb6d4b7187782e272aebf969088d49cdb9718368e359e3c582fe4e2a99`，
增加每日备份），各手动触发一次备份成功并写入备份卷。2026-10-05 两环境升级到 v0.1.3（git `8d04b7b`，
manager 镜像 `sha256:6bf930d91c73328f4897f545b8c216d3d802a04be325d97aa7567b71f69a9b57`，导出监控指标）。2026-10-07 升级到 v0.1.4（git `1d57f5f`，manager 镜像
`sha256:6a3fa9fece8e669371e87a2238a2e7c41216365e5366f9528e9efbea74dc64a5`，导出证书到期时间；
首个由 Release 工作流自动生成发布说明的版本）。Prod 已经 GitOps 目录承载 `iam-login`
Tenant（Bound / CredentialsAvailable）。

- v0.1.1 GitOps（Dev，以 homelab-infra 分支验证后切回 main）：目录中的 namespace + Tenant 被创建并
  Ready；加入 ConfigMap 被拒（`gitops-tenants` cannot patch configmaps）且未创建；移除后 namespace 与
  Tenant 被 prune、Database 回收，pg-dev 无残留。Dev/Prod 部署后 `gitops` Kustomization 均 Ready。

- Dev 验收：动态供应（含 pgcrypto、应用凭据实际登录）→ Delete 回收；Retain 释放 → Released 后
  改策略被拒 → 清除 tenantRef 重新开放 → 新 Tenant 以 databaseRef 申请并 Ready（凭据位置与版本
  不变）→ Delete 回收。PostgreSQL 无 `ayatori_e2e*` 残留，controller 身份读回收后的凭据为 404。
- Prod 验收：供应 → Delete 回收，PostgreSQL 无残留、凭据 404；prod controller 读 Dev 前缀为 403。
- 验收发现并修复两项 v0.1.0 不可用缺陷后重打同名 tag：OpenBao 登录 JWT 的 audience
  （[ayatori #28](https://git.ddupan.top/panxiao81/ayatori/pulls/28)、
  [homelab-infra #204](https://git.ddupan.top/panxiao81/homelab-infra/pulls/204)），以及重新开放的
  动态供应 Database 无法被申请（[ayatori #30](https://git.ddupan.top/panxiao81/ayatori/pulls/30)）。
- 监控（2026-10-05）：中央 12 个目标均 up，规则所需指标齐全；停止 Dev ESO 约 7 分钟后
  `AyatoriServiceInactive` 与 `AyatoriTargetDown` 触发，Alertmanager Telegram 发送计数上升；恢复后告警
  全部解除，Telegram 发送失败为 0。首版采集因 VMStaticScrape `jobName` 覆盖 endpoint 的 `job` 标签而
  选不到序列，已按组件拆分修复（#260）；首轮测试告警因标签名为 `environment` 进了生产频道，改为 `env`
  （#262）后复测，Dev 告警的 receiver 为 `telegram-dev`。
- 证书（2026-10-07）：中央两环境各 23 条证书到期指标，最近到期剩余 364 天；三条证书规则已加载，
  无 Ayatori 告警。observability Kustomization `prune=false`，#260 拆分后残留的旧 `monitoring/ayatori`
  采集对象造成重复采集，已人工删除。
- 恢复演练：从 Dev 以 `k0s backup --save-path=-` 流式写入临时 LXC（不落本机），`k0s restore` 后
  apiserver Ready，演练前标记、Instance、Flux 对象与同步的 Secret 均在，CA 指纹一致；演练容器不运行
  controller，结束后删除。
- 消费方：`iam-login` 以自有 SA `iam-login-database` 经 OpenBao 只读其凭据（homelab-infra
  `apps/iam-login/README.md`），本页未独立验证其运行。
- 未验证：导入（`source: Import`）在真实环境的路径、按原地址重建后的完整恢复、k0s 证书轮换。
