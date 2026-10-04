---
title: Authelia
lifecycle: active
evidence: documented
last_reviewed: 2026-09-25
last_verified: null
sources:
  - 维护者于 2026-09-16 确认当前状态
---

# Authelia

**Authelia 继续作为 homelab 的主 OIDC 入口与人类认证后端工作，状态为 active。**
基础状态由维护者于 2026-09-16 明确。2026-09-25 新增 [Hydra 人类登录 PoC](hydra.md)，
以标准 OIDC client 复用 Authelia；其原有应用客户端、Samba AD 后端及 MFA 策略保留。
该次仅验证新增配置有效和 Pod 就绪，未更新本页原有功能的整体验收日期。

## 用途与入口

Authelia 承担人类用户的统一登录与应用 OIDC 接入。现有架构中，Samba AD 提供用户目录，
Authelia 提供网页认证与 OIDC；机器和 workload 身份由 [SPIFFE/SPIRE](spire.md) 提供。
SPIRE 的 OIDC discovery 用于机器身份验签，不构成另一个人类登录 broker。

登录入口沿用源码仓库记录：<https://auth.ddupan.top>。
从已接入的应用选择其 SSO 登录入口，按 Authelia 页面完成认证后返回应用。
具体应用入口和访问权限仍由各服务文档说明。

## 当前状态与历史记录

源码工作区 `apps/authelia/README.md` 中将 OIDC 描述为后续阶段的内容属于旧记录，
不能继续作为当前部署状态依据。旧 Keycloak、Casdoor 位于源码仓库 `archive/`，
不属于当前 OIDC 登录方案；目前无需为统一身份而重新引入它们。

本次只更新知识库状态，未修改原工作区 README，也未将 broker active 扩大解释为
所有应用都已接入 OIDC。现有 forward-auth 接入与 OIDC 是不同的应用认证方式，
具体配置继续以各服务说明为准。

## 维护入口

以下路径相对于 homelab-infra：

- `apps/authelia/`：Authelia 部署配置；README 中过时的 OIDC 阶段说明待同步。
- `infrastructure/samba-ad/README.md`：用户目录与 AD。
- `platform/envoy-gateway/README.md`：网关认证集成。
- `archive/keycloak/RETIRED.md`、`archive/casdoor/RETIRED.md`：旧身份方案的退役记录。

新增应用的 OIDC 接入与权限配置在对应源码和服务文档中维护，不在知识库保存实际 client secret。

## Backstage 接入

2026-09-25 新增 [Backstage 客户端](backstage.md)，沿用二次认证。此次仅验证配置与 Pod 就绪，
应用实际登录尚待首版部署（指当时；Backstage 之后已部署，登录仍未验收）；线上 Hydra 配置与本地 values 的差异及保留方式见该服务页。

## Incus 接入

[Incus](incus.md) 使用独立 public client 与 PKCE S256，专属策略默认拒绝，
仅允许 `panxiao81` 且要求 MFA；不依赖待重构的组。配置通过 live Helm values
增量合并，保留现有客户端。2026-09-25 已验证部署、浏览器授权跳转和设备授权发起；
维护者同日确认真实用户 MFA 登录并返回 Incus 控制台成功。来源 `apps/authelia/clients/incus.yaml` 已推送为 [d45e0b9](https://git.ddupan.top/panxiao81/homelab-infra/commit/d45e0b94e80cb8a509df46a14cd7e89d5381b124)，尚未合并 main。
