---
title: Homepage 起始页
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/homepage/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/envoy-gateway/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/0e740f9e344d107478f3b9af8580d4f895de2d6e
watch:
  - homelab-infra:apps/homepage/
  - homelab-infra:platform/envoy-gateway/README.md
  - homelab-infra:clusters/homelab/apps/homepage.yaml
---

# Homepage 起始页

## 它解决什么问题

`https://home.lab.ddupan.top` 是列出所有应用的起始页（[gethomepage](https://gethomepage.dev)），
按“应用 / 平台 / 基础设施”分组，并显示集群内服务的 Pod 状态。

## 从哪里使用

- 入口：`https://home.lab.ddupan.top`，LAN 或 Tailscale。
- 登录：无。页面只有链接，每个应用自行认证。

## 第一次使用

打开 `https://home.lab.ddupan.top`，点击磁贴进入对应应用；进入后按该应用自己的登录方式登录。

## 给服务加磁贴

- **经 Envoy Gateway 发布的服务：在它的 HTTPRoute 上加 `gethomepage.dev/*` annotation**，磁贴随路由增删。
  照抄 `apps/poweradmin/httproute.yaml`：`enabled`、`name`、`group`（`应用`/`平台`/`基础设施`）、`icon`、
  `description`、`href`。
- **必须写 `href`**：缺省时取 `hostnames[0]` 加 `rules[0].matches[0]`，多数路由会得到旧的 `ad` 名，
  没有 `matches` 的路由会崩溃。
- 状态徽标按 `app.kubernetes.io/name=<路由名>` 找 Pod；不对时设 `app` 或 `pod-selector`。
- 其他（集群外主机、Helm chart 渲染的路由）：写进 `apps/homepage/config/services.yaml`。
- 图标用 dashboard-icons 名（如 `gitea.svg`）或 `mdi-*`。

这也是[发布新服务](../guides/publish-service.md)流程的最后一步（`platform/envoy-gateway/README.md` 第 4 项）。

## 出问题时

- 磁贴缺失：确认 annotation 中 `enabled: "true"`，以及路由所在 namespace 的对象可被 Homepage 读取（集群级只读 RBAC，`rbac.yaml`）。
- 链接指向旧地址：补 `href`。

## 运维入口

- 源码：[apps/homepage/](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/homepage)，
  普通 manifest，Flux（`clusters/homelab/apps/homepage.yaml`）。`settings.yaml` 只固定分组顺序。
- 无持久数据，备份恢复不需要。

## 当前状态与证据

- 2026-11-03 上线配置（[0e740f9](https://git.ddupan.top/panxiao81/homelab-infra/commit/0e740f9e344d107478f3b9af8580d4f895de2d6e)），
  2026-11-13 加入公有云控制台链接。
