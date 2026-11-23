---
title: research-auto（homelab 部署）
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/research-auto/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/research-auto/service.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/clusters/ayatori-prod/research-auto.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/417bf265dbc58e782b91e78084b67e6fb9ee76f5
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/ed0ac6e4da9a1cb93345865ca0ce38b864bd2861
  - 维护者 2026-11-18 说明（纳入 wiki 范围）
watch:
  - homelab-infra:apps/research-auto/
  - homelab-infra:clusters/ayatori-prod/research-auto.yaml
  - homelab-infra:clusters/homelab/apps/research-auto.yaml
---

# research-auto（homelab 部署）

## 它解决什么问题

本页只记录 homelab-infra 一侧的部署与依赖。应用代码与使用说明见
[panxiao81/research-auto](https://github.com/panxiao81/research-auto)；该仓库已移除 k8s 清单，
部署声明自 2026-10-04 起由 homelab-infra 经 Flux 管理。

## 从哪里使用

- 入口：API Service `research-auto-api` 为 `loadBalancerClass: tailscale`，只经 [Tailscale](tailscale.md) 访问；
  主机名由 Tailscale operator 分配，可在 tailnet 设备列表中查看。
- 使用方法：见应用仓库。

## 日常操作与限制

- 组件：`research-auto-api` 与 `research-auto-worker` 两个 Deployment，外加一个 PVC。
- 升级：改 `api-deployment.yaml` / `worker-deployment.yaml` 中的 `ghcr.io/panxiao81/research-auto:sha-*` 并提交；
  直接 `kubectl set image` 会被 Flux 改回。
- break-glass：Bao 不可用时按 `secrets.example.yaml` 填写 gitignored 的 `secrets.yaml` 手工 apply，Bao 恢复后 ESO 覆盖回去。

## 依赖

| 依赖 | 说明 |
|---|---|
| [pg-prod](shared-postgresql.md) | Ayatori 租户，库 `research_auto`（`clusters/ayatori-prod/research-auto.yaml`）；应用经连接池 6432，initContainer 的 yoyo 迁移直连 5432 |
| [OpenBao](openbao.md) + [ESO](external-secrets.md) | `kv/k8s/research-auto`（应用凭据）；数据库凭据经 `database.yaml` 同步为 Secret `research-auto-pgprod` |
| [SeaweedFS](seaweedfs.md) | 专用 `research-auto` 身份，只能访问 `research` bucket；与 `kv/k8s/seaweedfs-s3` 中同名身份是两份副本 |
| [Tailscale](tailscale.md) | API 入口 |

## 运维入口

- 源码：[apps/research-auto/](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/research-auto)，
  Flux `clusters/homelab/apps/research-auto.yaml`。
- 备份恢复：数据库随 pg-prod 的备份；PVC 与 S3 数据没有单独方案。

## 当前状态与证据

- 2026-10-04 部署改由 homelab-infra Flux 管理（[417bf26](https://git.ddupan.top/panxiao81/homelab-infra/commit/417bf265dbc58e782b91e78084b67e6fb9ee76f5)），
  2026-10-13 数据库切到 pg-prod（[ed0ac6e](https://git.ddupan.top/panxiao81/homelab-infra/commit/ed0ac6e4da9a1cb93345865ca0ce38b864bd2861)）。
