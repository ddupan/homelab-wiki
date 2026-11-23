---
title: Authelia
lifecycle: retired
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - 维护者于 2026-09-16 确认当前状态
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/b3b4d8fd1cb879e2e0b640e52b86c219268e0620
  - homelab-infra apps/iam-login/README.md
watch:
  - homelab-infra:apps/iam-login/README.md
  - homelab-infra:platform/envoy-gateway/README.md
---

# Authelia

> **已于 2026-10-11 退役（仓库侧）**：所有 OIDC 客户端（Gitea、Grafana、Backstage、OpenBao、Incus）
> 已迁到 [iam-login](iam-login.md)（`https://sso.ddupan.top`）。仓库删除了 `apps/authelia`、
> `auth.ddupan.top` 的证书/监听器/DNS/隧道入口、ExternalSecrets 与探针，Gitea 去掉 `authelia` 登录源，
> 见 [b3b4d8f](https://git.ddupan.top/panxiao81/homelab-infra/commit/b3b4d8fd1cb879e2e0b640e52b86c219268e0620)。
> 该 commit 说明 `prune: false` 的对象与 Helm release 需在现场手工删除。
> 新应用的人类登录请作为 OIDC client 接入 iam-login（源码 `apps/iam-login/README.md`）；
> Envoy Gateway 上原有的 Authelia forward-auth 已随之移除（`platform/envoy-gateway/README.md`）。
> `auth.ddupan.top` 不再是登录入口。以下为历史记录。

## 历史：退役前状态

基础状态（active）由维护者于 2026-09-16 明确。2026-09-25 新增 [Hydra 人类登录 PoC](hydra.md)，
以标准 OIDC client 复用 Authelia；其原有应用客户端、Samba AD 后端及 MFA 策略保留。
该次仅验证新增配置有效和 Pod 就绪，未更新本页原有功能的整体验收日期。

## 用途与入口

Authelia 承担人类用户的统一登录与应用 OIDC 接入。现有架构中，Samba AD 提供用户目录，
Authelia 提供网页认证与 OIDC；机器和 workload 身份由 [SPIFFE/SPIRE](spire.md) 提供。
SPIRE 的 OIDC discovery 用于机器身份验签，不构成另一个人类登录 broker。

当时的登录入口为 `https://auth.ddupan.top`（已下线，勿再使用）。

## 历史：OIDC 阶段记录

当时 `apps/authelia/README.md` 中将 OIDC 描述为后续阶段的内容属于旧记录。
旧 Keycloak、Casdoor 位于源码仓库 `archive/`，不属于当前 OIDC 登录方案；
无需为统一身份重新引入它们。

Authelia 作为 broker 上线不等于所有应用都已接入 OIDC：当时的 forward-auth 接入与 OIDC
是不同的应用认证方式。

## 历史：维护入口

以下路径相对于 homelab-infra。`apps/authelia/` 已在 b3b4d8f 删除，可在该 commit 的父版本查阅；
`archive/keycloak/RETIRED.md`、`archive/casdoor/RETIRED.md` 为更早身份方案的退役记录。

## 历史：Backstage 接入

2026-09-25 新增 [Backstage 客户端](backstage.md)，沿用二次认证。此次仅验证配置与 Pod 就绪，
应用实际登录尚待首版部署（指当时；Backstage 之后已部署，登录仍未验收）；线上 Hydra 配置与本地 values 的差异及保留方式见该服务页。

## 历史：Incus 接入

[Incus](incus.md) 使用独立 public client 与 PKCE S256，专属策略默认拒绝，
仅允许 `panxiao81` 且要求 MFA；不依赖待重构的组。配置通过 live Helm values
增量合并，保留现有客户端。2026-09-25 已验证部署、浏览器授权跳转和设备授权发起；
维护者同日确认真实用户 MFA 登录并返回 Incus 控制台成功。来源 `apps/authelia/clients/incus.yaml` 见 [d45e0b9](https://git.ddupan.top/panxiao81/homelab-infra/commit/d45e0b94e80cb8a509df46a14cd7e89d5381b124)。
