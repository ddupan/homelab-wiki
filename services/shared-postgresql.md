---
title: 共享 PostgreSQL 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# 共享 PostgreSQL

集群内的多个服务共用一套 PostgreSQL，避免为每个应用维护独立数据库实例造成资源浪费。
共享实例已经在使用；计划中的 [PostgreSQL Tenant Operator](postgresql-tenant-operator.md)
将负责简化 database、role 和凭据的管理，目前不能把该计划当成已上线的自助申请入口。

共享使用的现状来自维护者于 2026-09-16 的说明。连接入口与部署配置来自 homelab-infra
工作区 `apps/shared-postgresql/`；本轮未连接数据库或查询 Kubernetes。

## 连接入口

| 使用场景 | 来源中记录的地址 |
|---|---|
| 集群内现有应用的兼容入口 | `shared-postgresql.shared-db.svc.cluster.local:5432` |
| CNPG 读写入口 | `shared-postgresql-rw.shared-db.svc.cluster.local:5432` |
| Tailscale 暴露所用的 Kubernetes Service | `shared-postgresql-tailscale`，namespace `shared-db` |

兼容 Service 的配置选择 CNPG primary。应用应使用 Service 地址，不固定到某个 Pod IP。
表中的 `.svc.cluster.local` 是集群内 DNS 地址；不能直接当作集群外客户端的可达地址。
Tailscale Service 配置存在不等于已经确认外部地址和访问权限，集群外接入须由维护者提供实际入口。

## 新应用接入前准备什么

向维护者说明应用名称、所需 database/role、扩展、连接数预期、网络来源及凭据消费方式。
由维护者按现有管理流程建立并授权，再提供连接参数和秘密引用；本页不提供尚未上线的 Tenant CR 示例。

应用使用自己的数据库与账号，不复用其他应用或实例管理员的凭据。
已有应用的秘密来源以各自 README 和配置为准，不能假定所有历史凭据已统一迁移到同一种流程。
使用 [OpenBao](openbao.md) 与 ESO 的应用，应消费受管秘密，不能直接修改 ESO 生成的副本。
连接 TLS 的要求及 CA 材料也应作为接入参数交付，不通过关闭校验解决连接问题。

## 第一次连接：确认目标数据库与身份

在已能访问集群内 Service、已安装 `psql` 的受控终端操作。
将下例占位符替换为已分配的 database 和应用 role；密码通过终端提示输入，不写入命令行或 wiki。
连接参数中的 TLS 配置沿用维护者交付的配置。

```bash
psql -X -W -v ON_ERROR_STOP=1 \
  -h shared-postgresql-rw.shared-db.svc.cluster.local -p 5432 \
  -U YOUR_APP_ROLE -d YOUR_APP_DATABASE \
  -c 'SELECT current_database(), current_user, 1 AS connection_ok;'
```

预期返回自己的数据库名、登录角色及 `connection_ok = 1`。
该示例不修改业务数据，也不证明建表、迁移或其他权限已经满足。
`-X` 避免加载本地 psql 启动脚本，`-W` 请求密码提示，`ON_ERROR_STOP` 使命令遇错退出。
语法见 [PostgreSQL psql 文档](https://www.postgresql.org/docs/current/app-psql.html)。
AI 接续任务时先确认操作范围，再执行现场查询；不能因为存在这段示例就自动登录数据库。

## 共享实例的维护边界

- 应用 schema migration 只面向自己的数据库，按应用升级流程执行；需要额外扩展或权限时先交由维护者处理。
- 连接池、慢查询和批量任务会影响共享资源，新增消费者时应说明负载预期。
- 数据库停用、role 删除和数据清理是独立操作，不能因应用 manifest 删除就推断数据库可一并删除。
- 配置文件记录 `instances: 1`，使用 CNPG 本身不代表已经配置数据库多副本高可用。

存储配置为 OpenEBS 的 `localpv-zfs-ceph`。持久卷存在不等于已有独立备份或完成恢复验收，
本页不对当前备份情况作未经验证的结论。
历史迁移文档中的 dump/restore 与回滚步骤属于迁移场景，不能整段重跑作为日常接入流程。
其中出现的旧服务名也不代表这些服务仍在运行。

## 遇到问题先看哪里

- 域名不解析或连接超时：先确认客户端位于何处、使用的入口及网络访问范围。
- 认证失败：核对 role、database 和应用自己的凭据来源；不要改用 `postgres` 绕过问题。
- 登录成功但操作被拒绝：区分数据库连接、schema、表和扩展权限，向维护者提供失败动作，不发送密码。
- 多个消费者同时异常：转到共享数据库和存储的运维入口，避免在各应用中分别覆盖连接配置。

源码入口为 homelab-infra 的 `apps/shared-postgresql/migration.md`、
`cloudnativepg-cluster.yaml` 和 `shared-postgresql-service.yaml`（后两者位于同一目录）。
服务依赖 Kubernetes、CNPG、集群 DNS 与持久存储；Tailscale 入口另依赖对应网络及授权。
