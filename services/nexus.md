---
title: Nexus Repository POC
lifecycle: experimental
evidence: live-verified
last_reviewed: 2026-09-20
last_verified: 2026-09-20
sources: []
---

# Nexus Repository POC

Nexus Repository Community Edition POC 为一次性 CI runner 提供共享的 Ansible Galaxy、
Go Modules、OCI 与 BuildKit 缓存，减少每个 job 从公网重新下载依赖的时间。GitOps 已部署，
上述代理与缓存链路均已完成现场验证；数据库和备份仍是 POC，现役 zot 保持不变。

## 从哪里使用

- 入口：`https://nexus.ad.ddupan.top`，仅 LAN。
- 人类管理：当前使用本地管理员，凭据受管于 OpenBao `kv/infra/nexus`；尚未配置 LDAP。
  后续正式化优先使用 Samba AD LDAP。Community
  Edition 不提供原生 OIDC/SAML，因此不能把 Authelia OIDC 写成已支持入口。
- CI 读取：`ansible-public`、Ansible 返回制品 URL 使用的成员 proxy 与 `go-public` 已开放
  LAN 匿名只读；`oci-public` 与其 `oci-proxy` 成员同样匿名只读，`oci-hosted` 不开放匿名。
  Terraform 明确收窄权限，未使用默认的全仓库匿名角色。
- CI 发布：目标是少量按信任边界划分的本地 service account，凭据由 OpenBao 保存；
  当前 POC 尚未创建 publisher 或授予写权限。

不能在整个入口套用 Authelia browser forward-auth：`ansible-galaxy`、Go 和 OCI 客户端
不会完成浏览器登录。若以后给 UI 单独加 RUT/forward-auth，必须使用与 package API 分离
且不可绕过的入口，并先完成 Header 信任边界审计。

## 第一次使用

部署与 Terraform 初始化完成后，Ansible 客户端将 Galaxy server 指向：

```ini
[galaxy]
server_list = nexus

[galaxy_server.nexus]
url = https://nexus.ad.ddupan.top/repository/ansible-public/
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
GOPROXY=https://nexus.ad.ddupan.top/repository/go-public/ go mod download
```

私有 module 的 `GOPRIVATE`、认证和 fallback 需由实际 workflow 明确配置，不能把内部 module
路径意外发送到公共 proxy。

2026-09-20 使用两个全新 Go module cache 下载 `golang.org/x/text@v0.30.0`：冷缓存
2.92 秒、热缓存 1.51 秒，均通过 `go-public` 匿名入口完成。

OCI 使用 path-based routing。公共镜像从
`nexus.ad.ddupan.top/oci-public/<namespace>/<image>:<tag>` 匿名拉取；写入使用
`nexus.ad.ddupan.top/oci-hosted/<namespace>/<image>:<tag>` 并要求认证。2026-09-20 验证：

- Alpine 代理冷拉 4.75 秒、热拉 0.80 秒，digest 一致；
- hosted push/pull 成功，匿名 pull 返回 401；
- amd64/arm64 OCI image index 可 push 与 inspect；
- Helm OCI chart push/pull digest 及本地 tarball SHA-256 一致；
- Cosign 签名和公钥验证成功，OCI 1.1 referrers 返回一个 Sigstore bundle；
- BuildKit `mode=max` registry cache 成功导出；销毁首个 builder 后，新 builder 从 Nexus
  导入缓存，两个 `RUN` step 均命中 `CACHED`。

## POC 限制

- 单副本、50 GiB OpenEBS RWO PVC，资源上限 2 CPU / 4 GiB。
- 当前使用 embedded H2，仅用于 POC；正式保存唯一制品前迁移至外部 PostgreSQL。
- 当前没有独立备份或恢复验收，PVC 不能被视为备份。
- Terraform provider 管理 Ansible/Go、Realm 与权限；provider 1.17.0 尚未暴露 Nexus 3.94
  新增的原生 OCI repository resource，因此 OCI 仓库由实例 Swagger 固定 schema 的幂等 REST
  调和器管理，不通过 UI 留下非声明式配置。
- 尚未创建正式 publisher service account；本轮写入测试临时使用受管管理员凭据。

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
`clusters/homelab/apps/nexus.yaml`。DNS 记录位于 `infrastructure/dns/records.yml`。
源码 README 维护部署、初始化、Terraform、验收与恢复边界。

部署依赖 Envoy Gateway、OpenEBS 和 LAN DNS；Terraform 管理依赖 Nexus 初始化后的受限管理
账号及 OpenBao 注入凭据。现阶段不依赖共享 PostgreSQL，正式化时才建立独立数据库与 role。

## 当前状态与证据

2026-09-20 现场确认 Flux Kustomization Ready、Nexus Pod Ready、50 GiB PVC Bound，HTTPRoute
经 HTTPS 状态 API 返回 200；Samba DNS apply 后复查 `changed=0`。Terraform 已创建 Ansible、
Go proxy/group、OCI Bearer Token Realm 和最小匿名只读角色，二次 plan 为 `No changes`；OCI
REST 调和器复查三个仓库均为 `in sync`。Ansible、Go、OCI、Helm、Cosign/referrers 与
BuildKit cache 的上述客户端测试均成功。实现来源为 homelab-infra PR #103、#108 与 #109。
尚未验证备份恢复或外部 PostgreSQL，也未创建正式 publisher account、修改或迁移 zot，
因此本页的 `live-verified` 仅覆盖已明确列出的 POC 范围。
