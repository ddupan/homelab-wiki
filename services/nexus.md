---
title: Nexus Repository
lifecycle: active
evidence: live-verified
last_reviewed: 2026-11-23
last_verified: 2026-09-20
sources:
  - homelab-infra `apps/nexus/README.md`、`apps/nexus/terraform/`
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/3cbf211
watch:
  - homelab-infra:apps/nexus/
  - homelab-infra:clusters/homelab/apps/nexus.yaml
---

# Nexus Repository

Nexus Repository Community Edition 提供 Ansible Galaxy、Go Modules、OCI 与 BuildKit 缓存的代理与仓库，
最初用于让一次性 CI runner 少从公网重复下载依赖。目前大部分 CI 依赖已改走
[artifact-keeper](artifact-keeper.md)，只有少数尚未迁移的消费者仍使用 Nexus；新的 CI 依赖接入应先看 artifact-keeper。
Nexus 已由 POC 转为正式使用，但数据库仍为 embedded H2、尚无独立备份，现役 zot 保持不变。

## 从哪里使用

- 入口：`https://nexus.lab.ddupan.top`，仅 LAN。旧名 `nexus.ad.ddupan.top` 仍由同一 HTTPRoute 服务，
  新配置一律用 lab 名。
- 人类管理：用 AD 账号经 LDAPS（`dc1.ad.ddupan.top:636`，内部 CA 校验主机名）登录；只有
  [`platform-admins`](samba-ad.md) 成员能登录，并映射为 `nx-admin`
  （Terraform 声明，[3cbf211](https://git.ddupan.top/panxiao81/homelab-infra/commit/3cbf211)，2026-10-16）。
  绑定账号 `svc-nexus` 的凭据只存于 OpenBao `kv/infra/nexus-ldap`。本地 `admin` 保留给 Terraform 并兼作
  break-glass，其密码在 `kv/infra/terraform/nexus`。Community Edition 不提供原生 OIDC/SAML。
- CI 读取：`ansible-public`、Ansible 返回制品 URL 使用的成员 proxy 与 `go-public` 已开放
  LAN 匿名只读；`oci-public` 与其 `oci-proxy` 成员同样匿名只读，`oci-hosted` 不开放匿名。
  Terraform 明确收窄权限，未使用默认的全仓库匿名角色。
- CI 发布：目标是少量按信任边界划分的本地 service account，凭据由 OpenBao 保存；
  尚未创建 publisher 或授予写权限。

不能在整个入口套用 Authelia browser forward-auth：`ansible-galaxy`、Go 和 OCI 客户端
不会完成浏览器登录。若以后给 UI 单独加 RUT/forward-auth，必须使用与 package API 分离
且不可绕过的入口，并先完成 Header 信任边界审计。

## 第一次使用

部署与 Terraform 初始化完成后，Ansible 客户端将 Galaxy server 指向：

```ini
[galaxy]
server_list = nexus

[galaxy_server.nexus]
url = https://nexus.lab.ddupan.top/repository/ansible-public/
```

然后在已有 `collections/requirements.yml` 的项目中运行：

```bash
ansible-galaxy collection install -r collections/requirements.yml \
  -p .ansible/collections
```

2026-09-20 使用两个全新客户端目录下载 `community.general:11.2.0`：冷缓存 8.49 秒、
热缓存 1.89 秒，两份 tarball SHA-256 一致。Nexus Ansible format 返回的制品 URL 指向
成员 proxy，因此匿名角色必须同时具备 group 与该 proxy 的只读权限。

Go POC 使用：

```bash
GOPROXY=https://nexus.lab.ddupan.top/repository/go-public/ go mod download
```

私有 module 的 `GOPRIVATE`、认证和 fallback 需由实际 workflow 明确配置，不能把内部 module
路径意外发送到公共 proxy。

2026-09-20 使用两个全新 Go module cache 下载 `golang.org/x/text@v0.30.0`：冷缓存
2.92 秒、热缓存 1.51 秒，均通过 `go-public` 匿名入口完成。

OCI 使用 path-based routing。公共镜像从
`nexus.lab.ddupan.top/oci-public/<namespace>/<image>:<tag>` 匿名拉取；写入使用
`nexus.lab.ddupan.top/oci-hosted/<namespace>/<image>:<tag>` 并要求认证。`oci-public` 当前按顺序组合
`oci-proxy`（Docker Hub，认证拉取）、`oci-proxy-ghcr`（ghcr.io）与 `oci-proxy-k8s`（registry.k8s.io）。
2026-09-20 验证（当时使用 `nexus.ad.ddupan.top`）：

- Alpine 代理冷拉 4.75 秒、热拉 0.80 秒，digest 一致；
- hosted push/pull 成功，匿名 pull 返回 401；
- amd64/arm64 OCI image index 可 push 与 inspect；
- Helm OCI chart push/pull digest 及本地 tarball SHA-256 一致；
- Cosign 签名和公钥验证成功，OCI 1.1 referrers 返回一个 Sigstore bundle；
- BuildKit `mode=max` registry cache 成功导出；销毁首个 builder 后，新 builder 从 Nexus
  导入缓存，两个 `RUN` step 均命中 `CACHED`。

## 限制

- 单副本、50 GiB OpenEBS RWO PVC，资源上限 2 CPU / 4 GiB。
- 当前仍使用 embedded H2；正式保存唯一制品前迁移至外部 PostgreSQL。
- 当前没有独立备份或恢复验收，PVC 不能被视为备份。
- Terraform（`sonatype-nexus-community/sonatyperepo` 1.19.3）管理全部 repository（含 OCI）、匿名权限、
  realm 与 AD 登录；原 OCI REST 调和器 `reconcile-oci.sh` 已退役（3cbf211）。`security_realms` 是整份替换，
  不要在 UI 中手工开关 realm 或创建长期 repository。
- 尚未创建正式 publisher service account；2026-09-20 的写入测试临时使用受管管理员凭据。

## 出问题时

先检查 Flux、Pod、PVC、Route 与最近日志：

```bash
kubectl -n flux-system get kustomization nexus
kubectl -n nexus get pod,pvc,service,httproute
kubectl -n nexus logs deployment/nexus --tail=100
```

首次启动可能持续数分钟。PVC 未 Bound 时先查 OpenEBS；Route 未 Accepted/ResolvedRefs 时查
Gateway parentRef 与 Service；公网依赖获取失败时区分 Nexus 本身、LAN DNS 和已知不稳定
WAN，不以重建 PVC 作为排障手段。

## 运维入口

实现入口为 homelab-infra 已合并的 `apps/nexus/` 与
`clusters/homelab/apps/nexus.yaml`。
源码 README 维护部署、初始化、Terraform、验收与恢复边界。

部署依赖 Envoy Gateway、OpenEBS 和 LAN DNS；Terraform 管理依赖 Nexus 初始化后的受限管理
账号及 OpenBao 注入凭据（CD 把 `kv/infra/terraform/nexus` 的 key 注入为 `TF_VAR_*`）。Terraform state 自
2026-10-04 起位于 SeaweedFS S3 `tfstate/nexus/terraform.tfstate`（`backend.tf`）。现阶段不依赖共享 PostgreSQL。

## 当前状态与证据

2026-09-20 现场确认 Flux Kustomization Ready、Nexus Pod Ready、50 GiB PVC Bound，HTTPRoute
经 HTTPS 状态 API 返回 200；Samba DNS apply 后复查 `changed=0`。Terraform 已创建 Ansible、
Go proxy/group、OCI Bearer Token Realm 和最小匿名只读角色，二次 plan 为 `No changes`；OCI
REST 调和器复查三个仓库均为 `in sync`。Ansible、Go、OCI、Helm、Cosign/referrers 与
BuildKit cache 的上述客户端测试均成功。实现来源为 homelab-infra PR #103、#108 与 #109。
`live-verified` 仅覆盖上述 POC 范围；`nexus.lab.ddupan.top` 入口、LDAPS/AD 登录与 OCI 仓库收归
Terraform（[3cbf211](https://git.ddupan.top/panxiao81/homelab-infra/commit/3cbf211)）是此后的变更。
