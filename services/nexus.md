---
title: Nexus Repository POC
lifecycle: experimental
evidence: configuration
last_reviewed: 2026-09-18
last_verified: null
sources: []
---

# Nexus Repository POC

Nexus Repository Community Edition POC 计划为一次性 CI runner 提供共享的 Ansible Galaxy、
Go Modules 与 OCI/BuildKit 缓存，减少每个 job 从公网重新下载依赖的时间。当前只有未提交的
GitOps 与 Terraform 配置，尚未部署、初始化或完成端到端验证；现役 zot 保持不变。

## 从哪里使用

- 计划入口：`https://nexus.ad.ddupan.top`，仅 LAN。
- 人类管理：POC 首次使用本地管理员；后续正式化优先使用 Samba AD LDAP。Community
  Edition 不提供原生 OIDC/SAML，因此不能把 Authelia OIDC 写成已支持入口。
- CI 读取：目标是对 public/group repository 开放 LAN 匿名只读。
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

预期首次请求从上游获取 collection，第二次在全新 runner 中由 Nexus 返回已缓存内容。
该预期尚未现场验证；验证时同时记录冷/热耗时和 Nexus 日志，不能只看命令退出码。

Go POC 使用：

```bash
GOPROXY=https://nexus.ad.ddupan.top/repository/go-public/ go mod download
```

私有 module 的 `GOPRIVATE`、认证和 fallback 需由实际 workflow 明确配置，不能把内部 module
路径意外发送到公共 proxy。

## POC 限制

- 单副本、50 GiB OpenEBS RWO PVC，资源上限 2 CPU / 4 GiB。
- 当前使用 embedded H2，仅用于 POC；正式保存唯一制品前迁移至外部 PostgreSQL。
- 当前没有独立备份或恢复验收，PVC 不能被视为备份。
- Terraform provider 已声明 Ansible 与 Go proxy/group；provider 1.17.0 尚未暴露 Nexus
  3.94 新增的原生 OCI repository resource。
- OCI 必须在补齐声明式 REST/provider 管理后再测试，不保留仅通过 UI 创建的长期配置。
- BuildKit registry cache 有待单独验证，普通 OCI image push 成功不能替代该测试。

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

实现入口为 homelab-infra 工作区中尚未提交的 `apps/nexus/` 与
`clusters/homelab/apps/nexus.yaml`。DNS 期望记录位于 `infrastructure/dns/records.yml`。
源码 README 维护部署、初始化、Terraform、验收与恢复边界。

部署依赖 Envoy Gateway、OpenEBS 和 LAN DNS；Terraform 管理依赖 Nexus 初始化后的受限管理
账号及 OpenBao 注入凭据。现阶段不依赖共享 PostgreSQL，正式化时才建立独立数据库与 role。

## 当前状态与证据

2026-09-18 已准备未提交的 Kubernetes、Flux、DNS 与 Terraform POC 配置，并完成本地渲染和
schema 检查后方可交付；未访问现场、未部署 Nexus、未申请凭据，也未修改或迁移 zot。
后续状态必须以合并记录、Flux 状态和客户端冷/热缓存验收分别更新，不能仅凭本页推断上线。
