---
title: Backstage
lifecycle: experimental
evidence: documented
last_reviewed: 2026-11-23
last_verified: null
sources:
  - 维护者于 2026-09-25 提供的首版基础设施接入要求
  - homelab-infra apps/authelia/values.yaml 与 infrastructure/dns/records.yml（2026-09-25 时尚未提交）
  - homelab-infra apps/backstage/（首版部署 29b3bde 起）
  - 2026-10-04 只读查看 Flux Kustomization、Pod 与 HTTPRoute 状态
  - backstage PR #10、#11（TechDocs 改由 CI 发布到 S3）、#12（catalog 发现，2026-10-04 合并）
  - homelab-infra apps/seaweedfs/terraform/techdocs.tf、infrastructure/openbao/terraform/auth-spire.tf
  - ci-actions publish-techdocs
  - backstage PR #13、homelab-infra PR #242（Flux 对象展示，2026-10-04 合并）
  - homelab-infra PR #246（服务实体，2026-10-05 合并）
  - homelab-infra PR #280、#281（入口链接、System 与依赖，2026-10-07 合并）
  - 2026-10-04 通过 Backstage catalog 与 TechDocs API 读取 homelab-backstage、homelab-wiki
  - homelab-infra apps/backstage/README.md、clusters/ayatori-prod/backstage.yaml
watch:
  - homelab-infra:apps/backstage/
  - homelab-infra:clusters/ayatori-prod/backstage.yaml
  - homelab-infra:apps/iam-login/terraform/clients.tf
  - homelab-infra:apps/seaweedfs/terraform/techdocs.tf
  - homelab-infra:catalog-info.yaml
---

# Backstage

服务目录与文档统一入口。源码 `apps/backstage/`，由 Flux 部署。

文末“验证边界”是 2026-09-25 首版（Authelia、CNPG 时期）的历史记录。

## 入口与第一次使用

LAN 入口：<https://backstage.lab.ddupan.top>（PowerDNS，external-dns 发布）；旧名 `backstage.ad.ddupan.top`
只做 301 跳转。远程客户端需要 LAN 路由与内网 DNS。打开后选择 OIDC 登录，在 [iam-login](iam-login.md)
（`sso.ddupan.top`）完成身份认证，再返回 Backstage 服务目录。

OIDC 客户端由 homelab-infra `apps/iam-login/terraform/clients.tf` 注册，回调为
`https://backstage.lab.ddupan.top/api/auth/oidc/handler/frame`；secret 由 Terraform 写入 OpenBao
`kv/k8s/backstage-sso`，经 `sso-external-secret.yaml` 同步为 `backstage-sso` Secret。原 Authelia 客户端键已于
2026-10-11 删除。应用内权限及目录内容由 Backstage 自身配置，不由 OIDC 登录成功推导。

## 目录与文档发布

TechDocs 不在 Backstage 内构建（`builder: external`）。各仓库用 job id 为 `techdocs` 的
workflow 调用 `https://git.ddupan.top/panxiao81/ci-actions/publish-techdocs@v1`，
生成站点后上传到 [SeaweedFS](seaweedfs.md) 的 `techdocs` bucket；Backstage 以只读身份读取。
仓库需要根目录的 `mkdocs.yml` 与带 `backstage.io/techdocs-ref` 注解的 `catalog-info.yaml`。
发布凭据由 OpenBao role `ci-techdocs-publisher` 授予，只匹配
`spiffe://ddupan.top/ci/panxiao81/*/techdocs`；bucket、IAM 用户与写入 Bao 的凭据由
homelab-infra `apps/seaweedfs/terraform/techdocs.tf` 管理。所有仓库共用一个发布身份，
任一仓库可覆盖其他实体的文档。

catalog 实体来自各仓库的 `catalog-info.yaml`。上游 Gitea provider 只遍历组织，
Backstage 改用自写 provider：每 30 分钟列出 `panxiao81` 名下的非空、未归档仓库，为每个仓库
注册指向默认分支 `catalog-info.yaml` 的可选 Location；没有该文件的仓库不报错、不进目录。
新仓库放好 `catalog-info.yaml` 即在 30 分钟内出现，无需登记。迁到组织后应换回上游 provider。

2026-10-04 已验证：provider 注册 9 个仓库，catalog 中 9 个 Location 均无错误；
homelab-backstage 与 homelab-wiki 均经该 provider 进入目录（`managed-by-location` 指向各自
仓库的 `src/branch/main/catalog-info.yaml`），Backstage TechDocs API 对两者的 `index.html`
返回 HTTP 200（分别发布 54、107 个文件）。同日只读查看：Flux Kustomization `backstage` Ready、Pod 1/1 Running。

## Flux 可见性

实体 Kubernetes 标签页通过 Kubernetes 插件的 `kubernetes.customResources` 展示带
`backstage.io/kubernetes-id` label 的 Flux 对象：Kustomization、Git/Helm/OCI Repository、
ImageRepository、ImagePolicy（只列集群提供的 v1）。`backstage-read-only` 对这些类型只有
get/list/watch；HelmRelease 不可读，因为 `spec.values` 可能内联敏感配置。其他组件要显示
自己的 Flux 对象，在 homelab-infra 给对象加与实体注解相同的 label。
未采用 `@backstage-community/plugin-flux`：0.3.4 同时查询 Flux 2.9 已不提供的 v1beta2，
后端返回 NOT_FOUND 会让卡片只显示错误。

2026-10-04 已验证：Backstage 服务账号可 list 上述类型，不可读 HelmRelease/Secret、不可 patch；
`/api/kubernetes/services/homelab-backstage` 无错误返回 Kustomization、ImageRepository、
ImagePolicy 各一（经 API，未在浏览器中查看标签页）。

## 服务实体

homelab-infra 根目录的 `catalog-info.yaml` 为每个 Flux Kustomization 声明一个 Component
（Backstage 本身除外，`flux-image-automation` 并入 `flux`），经 catalog 自动发现进入目录。
实体按命名空间关联集群资源：`backstage.io/kubernetes-namespace` 加选中全部对象的
selector `!backstage.io/none`。不用 Flux 的 `kustomize/helm.toolkit.fluxcd.io/name` label，
因为 Flux 只给顶层对象打 label，Pod 与 operator 生成的工作负载都没有，会在 Kubernetes
标签页中缺失。前提是每个服务独占命名空间。不由这些 Kustomization 管理的命名空间
（例如 cloudflared、tailscale）尚未建实体，需要时在该文件追加。

实体还带入口链接（Web UI 与 API 端点）并按 System 分组：identity、delivery、storage、
networking、observability、platform、applications、developer-portal。`dependsOn` 只记录有配置
依据的应用级依赖（数据库、认证、目录、对象存储、镜像仓库、邮件），envoy-gateway、
external-secrets、cert-manager、openebs、flux 等通用平台组件不画，Catalog Graph 因此可读。
集群外的 openbao、proxmox、incus、samba-ad 只有链接；共享数据库为 `kind: Resource`。
2026-10-07 已验证：27 个 Component、1 个 Resource、8 个 System，全部有归属，25 条依赖关系。

2026-10-05 已验证：目录中 22 个 Component；zot、observability、flux 的 Kubernetes 数据
无错误返回，且包含 Pod（分别 2、13、6 个）。

## 依赖与维护边界

- [共享 PostgreSQL](shared-postgresql.md)：pg-prod 上的 `backstage` 库由 [Ayatori](ayatori.md) 供应
  （`clusters/ayatori-prod/backstage.yaml`），凭据经 `apps/backstage/database.yaml` 同步为 `backstage-pgprod`。
  **直连 5432、不走连接池**（events 用 LISTEN/NOTIFY），TLS 为 verify-full。2026-10-13 自 k3s 内 CNPG（`shared-db`）
  以 `pg_dump`/`pg_restore --no-owner` 迁入。`kv/k8s/backstage` 中旧的 `POSTGRES_PASSWORD` 已不再使用。
- [iam-login](iam-login.md)：OIDC 客户端在 `apps/iam-login/terraform/clients.tf`。
- DNS：`backstage.lab.ddupan.top` 由 external-dns 发布到 PowerDNS，无需手工登记。
- OpenBao `kv/k8s/backstage` 提供 `BACKEND_SECRET`、`AUTH_SESSION_SECRET`、`GITEA_TOKEN`；任何前置缺失时 Flux
  Kustomization 保持 NotReady，而不会回退到明文 Secret。

## 故障入口

域名问题先确认使用的是 `backstage.lab.ddupan.top` 及客户端的内网 DNS。登录问题核对 iam-login 客户端回调、
`backstage-sso` ExternalSecret 同步状态与 iam-login 服务状态；
数据库认证问题核对 OpenBao 会话及应用 role，不输出秘密或改用管理员账号运行应用。

## 验证边界（2026-09-25 首版历史记录）

以下记录对应已退役的 Authelia 与 CNPG `shared-db`，仅作历史。
2026-09-25 已现场验证 Authelia Helm revision 21 为 deployed，Pod 为 1/1 Running，
OIDC discovery 可读且 issuer 为 `https://auth.ddupan.top`；升级前后 values 比较确认
仅新增 Backstage client，原客户端和 claims policy 保留。
Samba DNS 首次应用仅新增 Backstage RRset，权威查询返回预期地址；重复执行 changed=0。

数据库已通过本机 SPIFFE `spiffe://ddupan.top/dev/panxiao81` 登录
`auth/jwt-spire/login` 的 `local-development` role 后完成初始化。该身份可读取
`kv/data/k8s/backstage`；先前 403 来自未经 SPIFFE 刷新的旧 CLI 会话，
其具体身份未能确认，不代表本机 SPIFFE 缺少权限。

已验证 `backstage` 为可登录、非 superuser、无 CREATEDB 的角色，拥有同名数据库；
使用 Bao 中的密码通过 `shared-postgresql-rw.shared-db.svc.cluster.local` 登录成功，
建表权限测试通过并回滚，未授予跨数据库管理权限。
同步记录见[验证记录](../verification.md#backstage-首版前置条件)。
