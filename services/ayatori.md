---
title: Ayatori 控制面
lifecycle: experimental
evidence: live-verified
last_reviewed: 2026-10-04
last_verified: 2026-10-04
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
端到端验收，尚未承载真实应用 Tenant，备份尚未建立。

## 从哪里使用

| 环境 | 主机 | API | PostgreSQL 实例 | Bao 应用凭据前缀 |
|---|---|---|---|---|
| Dev | `ayatori-dev.ad.ddupan.top`（192.168.10.11） | `https://192.168.10.11:6443` | `homelab-dev` → `pg-dev:5433` | `kv/ayatori/dev/applications/` |
| Prod | `ayatori-prod.ad.ddupan.top`（192.168.10.12） | `https://192.168.10.12:6443` | `homelab-prod` → `pg-prod:5432` | `kv/ayatori/prod/applications/` |

- 两台都是 [Incus](incus.md) 上的非特权 LXC，仅 LAN 可达。
- 登录：当前只有主机管理员入口，`ssh panxiao81@ayatori-<env>.ad.ddupan.top` 后
  `sudo k0s kubectl ...`。尚未给人或其他系统签发 kubeconfig，也没有接入 IdM。
- 前提：执行部署的机器只需 Ansible 与到两台 LXC 的 SSH（`panxiao81` 免密 sudo）；部署过程不读取任何凭据。

## 第一次使用

在 Dev 申请一个带 pgcrypto 的数据库（Dev 允许随意试验，Prod 先确认用途）：

```bash
ssh panxiao81@ayatori-dev.ad.ddupan.top
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
由消费方集群用自己的身份读取并投射（例如其 ESO）；**消费方读取应用凭据的 Bao 策略尚未
建立**，按应用单独授权时再补。

清理：自动生成的 Database 默认 `reclaimPolicy: Retain`。要连同数据删除，先把该 Database
改为 `Delete` 再删 Tenant；Retain 释放后改策略会被 CEL 拒绝。

## 日常操作与限制

- 发布：Ayatori 仓库打 `vX.Y.Z` git tag，Release 工作流用 ko 构建 manager 镜像并以同名 tag
  推送 [zot](zot.md) `panxiao81/ayatori-manager`。部署 role、Flux 同步的清单与镜像是同一组制品。
- 完全不可用的 release 不升版本：修复合并后删除并重打同名 tag，Release 覆盖同名镜像
  （CI 身份有 update，本机开发身份可读写删除），部署时 role 重新拉取并按镜像 ID 变化重启。
- 部署：在 laptop 执行 homelab-infra `infrastructure/ayatori/ansible/deploy.sh dev|prod`，经 SSH
  部署；`requirements-<env>.yml` 各钉一个 release。Promotion 即把 prod 改为 Dev 已验收的 tag。
- Dev 可本地构建镜像直接加载试验；Prod 只走 release + promotion。
- 运行形态：k0s controller-only（apiserver、etcd、只开 namespace 控制器的 KCM）为 systemd；
  ESO、Flux source/kustomize-controller、ayatori-manager 为 podman quadlet（host 网络、只读根、
  各自 k0s 证书用户）。Flux 从 release tag 同步 Database CRD 与控制面对象；k0s、ESO、Flux 版本与
  digest 固定在 role defaults。
- 管理凭据：ESO 以 `kubernetes-ayatori-<env>` 登录 OpenBao，只读
  `kv/infra/postgresql/ayatori/<env>`，同步为 `ayatori-system/homelab-<env>-admin`。
- 限制：Flux 不选主、单实例；kustomize-controller 为 cluster-admin；第三方镜像只固定 digest，
  未验签；k0s 客户端证书一年到期，删除 `/etc/ayatori-control-plane/<identity>/kubeconfig` 后重跑
  部署轮换。宿主负载很高（2026-10-04 约 97/12 核）时 manager 可能因 Lease 超时退出，由
  systemd 自动重启。

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

- 部署 role、发布与已知限制：Ayatori [deploy/README.md](https://git.ddupan.top/panxiao81/ayatori/src/tag/v0.1.0/deploy/README.md)；
  Database 设计：Ayatori `docs/database/`。
- 环境声明：homelab-infra `infrastructure/ayatori/ansible/`；OpenBao mount/role/policy：
  `infrastructure/openbao/terraform/auth.tf`、`policies/ayatori-*.hcl`；zot 授权：`apps/zot/values.yaml`；
  LXC：`infrastructure/incus/terraform/`。
- 依赖：Incus、OpenBao、共享 PostgreSQL、zot、Gitea（Flux 拉取与制品下载）、GitHub/ghcr
  （第三方 CRD 与镜像）。Gitea 或 zot 不可用只影响新部署，已运行实例不受影响。
- 备份恢复：**尚未建立**。etcd（全部 CR 与 Database 已确认的 OID/凭据版本）与 k0s PKI 只存在于
  各 LXC 的 rootfs；应用数据在共享 PostgreSQL，按其自身备份。

## 当前状态与证据

2026-10-04 维护者授权后部署：Dev 与 Prod 均运行 v0.1.0（git `c0422d9`，manager 镜像
`sha256:ba3a63aab2a8c5ea0576aed1562f85003dd0f7437149e0d36ffcf81c846efff0`），Flux revision
`v0.1.0@c0422d9`，Instance Ready。Dev 二次部署 `changed=0`。

- Dev 验收：动态供应（含 pgcrypto、应用凭据实际登录）→ Delete 回收；Retain 释放 → Released 后
  改策略被拒 → 清除 tenantRef 重新开放 → 新 Tenant 以 databaseRef 申请并 Ready（凭据位置与版本
  不变）→ Delete 回收。PostgreSQL 无 `ayatori_e2e*` 残留，controller 身份读回收后的凭据为 404。
- Prod 验收：供应 → Delete 回收，PostgreSQL 无残留、凭据 404；prod controller 读 Dev 前缀为 403。
- 验收发现并修复两项 v0.1.0 不可用缺陷后重打同名 tag：OpenBao 登录 JWT 的 audience
  （[ayatori #28](https://git.ddupan.top/panxiao81/ayatori/pulls/28)、
  [homelab-infra #204](https://git.ddupan.top/panxiao81/homelab-infra/pulls/204)），以及重新开放的
  动态供应 Database 无法被申请（[ayatori #30](https://git.ddupan.top/panxiao81/ayatori/pulls/30)）。
- 未验证：导入（`source: Import`）在真实环境的路径、真实应用消费凭据、备份恢复、k0s 证书轮换。
