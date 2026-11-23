---
title: e5renew（homelab 部署）
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/e5renew/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/e5renew/database.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/clusters/ayatori-prod/e5renew.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/clusters/homelab/apps/e5renew.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/2cd90d315e027a4211121a216853d8460778c2cc
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/35692bc7c16f12aa1163f0f2e28fd4103008f68a
  - 维护者 2026-11-18 说明（纳入 wiki 范围）
watch:
  - homelab-infra:apps/e5renew/
  - homelab-infra:clusters/ayatori-prod/e5renew.yaml
  - homelab-infra:clusters/homelab/apps/e5renew.yaml
---

# e5renew（homelab 部署）

## 它解决什么问题

本页只记录 homelab-infra 一侧的部署与依赖。应用本身、功能与使用说明见应用仓库
[panxiao81/e5renew](https://github.com/panxiao81/e5renew)（chart 在 `helm/e5renew`）。

## 从哪里使用

- 入口：`e5renew.ddupan.top`，经 Cloudflare Tunnel 公网发布（`infrastructure/cloudflared/terraform`）。
- 登录与使用：见应用仓库。

## 日常操作与限制

- 部署：Flux（`clusters/homelab/apps/e5renew.yaml` → `apps/e5renew/`），HelmRelease 的 GitRepository
  固定到 chart 的 commit；升级 chart 即改该 commit。
- **Entra client secret 必须定期在本机轮换**：Terraform（`apps/e5renew/terraform/`）签发 365 天有效的 secret，
  签发 300 天后的下一次 apply 换新；不在 CI（CI 没有可用的 Azure 身份）。需要 `az login`（应用注册所有者），
  步骤与之后的 ESO 强制同步、Deployment 重启见源码 README。应用注册本身是手工建的。

## 依赖

| 依赖 | 说明 |
|---|---|
| [pg-prod](shared-postgresql.md) | Ayatori 租户 `e5renew`（`clusters/ayatori-prod/e5renew.yaml`）；应用经连接池 6432，迁移 Job 直连 5432 |
| [OpenBao](openbao.md) + [ESO](external-secrets.md) | 数据库凭据（Ayatori 应用路径）、`kv/k8s/e5renew-azuread`（Entra client secret）、`kv/k8s/e5renew` |
| Cloudflare Tunnel | 公网入口 |
| Microsoft Entra | 应用注册 `e5renew` |

## 运维入口

- 源码：[apps/e5renew/](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/e5renew)。
- 备份恢复：数据库随 pg-prod 的备份，没有单独方案。

## 当前状态与证据

- 2026-10-13 自 k3s 内 CNPG 迁到 pg-prod，同时改由 Flux 部署、凭据来自 OpenBao
  （[2cd90d3](https://git.ddupan.top/panxiao81/homelab-infra/commit/2cd90d315e027a4211121a216853d8460778c2cc)）；
  同日加入 Terraform 管理的 client secret 轮换（[35692bc](https://git.ddupan.top/panxiao81/homelab-infra/commit/35692bc7c16f12aa1163f0f2e28fd4103008f68a)）。
- 当前 client secret 的到期时间见 Terraform state 或 Entra 应用注册。
