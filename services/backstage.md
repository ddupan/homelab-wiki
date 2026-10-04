---
title: Backstage
lifecycle: experimental
evidence: documented
last_reviewed: 2026-10-04
last_verified: null
sources:
  - 维护者于 2026-09-25 提供的首版基础设施接入要求
  - homelab-infra apps/authelia/values.yaml 与 infrastructure/dns/records.yml（2026-09-25 时尚未提交）
  - homelab-infra apps/backstage/（首版部署 29b3bde 起）
  - 2026-10-04 只读查看 Flux Kustomization、Pod 与 HTTPRoute 状态
---

# Backstage

服务目录与文档统一入口。源码 `apps/backstage/`，由 Flux 部署。

2026-10-04 只读查看：Flux Kustomization `backstage` Ready、Pod 1/1 Running，
HTTPRoute 为 `backstage.ad.ddupan.top`。未验证 OIDC 登录、目录内容或数据库 schema migration，
故 `last_verified` 仍为 null。下文除特别注明外，均为 2026-09-25 首版前置条件的记录，
其中“预定”“尚待部署”指当时状态。

## 入口与第一次使用

预定 LAN 入口：<https://backstage.ad.ddupan.top>；远程客户端需要 LAN 路由与内网 DNS。
应用上线后，从该地址选择 OIDC 登录，在 [Authelia](authelia.md) 完成 AD 身份认证与
二次认证，再返回 Backstage 服务目录。此使用路径尚待应用部署后验收。

OIDC client 为 `backstage`，采用 `client_secret_basic`、`two_factor` 和现有 `gitea`
claims policy；scope 为 `openid profile email groups`。回调为
`https://backstage.ad.ddupan.top/api/auth/oidc/handler/frame`。
应用内权限及目录内容由 Backstage 自身配置，不由 OIDC 登录成功推导。

## 依赖与维护边界

- [共享 PostgreSQL](shared-postgresql.md)：使用同名 `backstage` LOGIN role 与数据库，
  role 为数据库 owner；密码来源为 OpenBao `kv/k8s/backstage` 的 `POSTGRES_PASSWORD`。
  初始化仅在缺失时创建，不自动轮换已有角色密码或改动已有库 owner。
- [Authelia](authelia.md)：客户端声明位于 homelab-infra `apps/authelia/values.yaml`。
- [LAN DNS](lan-dns.md)：`infrastructure/dns/records.yml` 声明 Samba A 记录，
  指向 Envoy 入口 `192.168.10.127`，通过 `infrastructure/samba-ad/ansible/provision-dc.yml --tags dns` 应用。
- 应用部署、HTTPRoute、秘密消费与端到端验收属于应用首版发布步骤，本次不替代这些步骤。

Authelia 本次使用当前 chart `0.11.6` 和线上 values 的增量客户端列表升级。
源码 values 尚缺线上 `hydra-login` client 与 `hydra` claims policy；
直接用源码全量覆盖会丢失这些配置。后续升级应先比对 `helm get values`，保留既有配置。
持久化数据库备份与应用恢复方案尚未在本次接入中验收。

## 故障入口

域名问题先查询 Samba DC：`dig @192.168.10.5 backstage.ad.ddupan.top A`，
预期为 `192.168.10.127`。登录问题核对 client ID、回调、秘密一致性与 Authelia Pod 状态；
数据库认证问题核对 OpenBao 会话及应用 role，不输出秘密或改用管理员账号运行应用。

## 验证边界

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
建表权限测试通过并回滚。未授予跨数据库管理权限，未验证应用 schema migration。
本页 `last_verified` 保持 null，因为 Backstage 应用尚未进行端到端验证。

本页草稿写于 2026-09-25，2026-10-04 补发；当时源码与本页均未提交，同步记录见
[验证记录](../verification.md#backstage-首版前置条件)。源码之后已提交，部署见 `apps/backstage/`。
