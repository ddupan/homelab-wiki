---
title: 共享 PostgreSQL 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-25
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

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#shared-postgresql)。


## 共享 etcd 设计边界

2026-09-25 维护者确定：为计划中的 k3s 外 PostgreSQL 引入的 etcd，应作为全 homelab
共享基础设施建设，PostgreSQL 是首个消费者。该共享定位已实现并完成首期部署验收；既有应用尚未迁移，
不改变本页现有 CNPG 入口。原研究将 etcd 列入数据库部署角色，新边界将其生命周期独立，
以便多个服务共用，减少重复部署与维护。

首期三成员已跨 laptop 与两台 PVE 部署，可与其他服务物理共置；
独立 IaC 管成员、认证、维护和快照，消费者只取得自己的账号与 key prefix 权限。
数据库卸载不能删除共享 etcd，全集群快照恢复也不能用作单个数据库的回滚。
现有 k3s 内部 datastore 不包含在本次迁移范围；其他消费者按实际需要接入。

维护者同时确定 etcd mTLS 证书由 OpenBao 中央 CA 签发，复用现有信任根，不引入
Pigsty 自建 CA。签发角色、peer 身份限制及消费者认证已部署；自动续签身份和 timer 已启用；
证书本地保存，正常启动不要求实时访问 Bao，Bao 本身不依赖此共享 etcd。
Patroni 的 etcd3 gateway 路径不支持证书 CN 对应的 RBAC 登录；维护者确定其独立随机密码
存入 Bao，由 Ansible 执行时读取，重复部署复用，轮换显式执行。该 secret 已在共享 etcd 部署阶段创建并验证 gateway 登录；Patroni 已部署。
PVE 改为裸机目前仅为后续倾向，没有迁移决定。

来源为本轮维护者设计指令及 homelab-infra
`infrastructure/shared-postgresql/RESEARCH.md`；文档来源为 [文档 acd4b55](https://git.ddupan.top/panxiao81/homelab-infra/commit/acd4b55)，实现由 [IaC PR #159](https://git.ddupan.top/panxiao81/homelab-infra/pulls/159) 跟踪。
本节记录数据库设计边界；共享 etcd 的现场部署与验证见独立服务页，本页 CNPG 的 `last_verified` 不因此更新。

共享 etcd 的首轮 IaC、隔离验证与部署前置条件见[共享 etcd](shared-etcd.md)。

### k3s 外实例的实现与验收边界（2026-09-25）

新 PostgreSQL 18.6 生产主从与独立开发实例已上线，现有 CNPG 应用数据尚未迁移。
生产稳定入口 `pg-prod.ad.ddupan.top:5432` 指向 VyOS `192.168.10.2` 上独立 HAProxy；
正常 primary 为 laptop SSD ZFS，PVE LXC150 为 standby。开发入口为
`pg-dev.ad.ddupan.top:5433`，同机独立用户/数据集。客户端要求中央 CA 与 verify-full TLS。

LXC151 的专属 HDD 卷存放 pgBackRest 仓库，真实 SSH/WAL 归档、首个 full 和每日 timer 已验收；
保留 3 个 full、本地连续 WAL，尚无异地备份，开发实例当前不备份。
真实备份已恢复到临时目录的隔离实例，SQL 可写与管理角色属性验证通过，未覆盖生产 PGDATA。
低负载停止 laptop 主库服务后，完整通过的一次演练约 9.2 秒恢复经稳定入口写入；旧主重新作为
replica 加入、计划回切 laptop 后复制与探针清理全部通过。这不是 SLA，也不覆盖冻结/网络分区等全部故障。

Bao PKI 与专用 `homelab-postgresql` SPIFFE 身份已通过 OIDC 管理会话首次创建；之后受限身份
完成签发、KV 读取与独立管理凭据交付。原始实例秘密不交给 Ayatori，控制面只读
`kv/infra/postgresql/ayatori/{prod,dev}` 中的 username/password。
生产与开发管理账号实际 TLS 登录和非 superuser CREATEDB/CREATEROLE 属性已验证。
配置、备份传输、代理与凭据重跑 `changed=0`；PG 每日续签已启用，实际 systemd 运行成功，
证书窗口检查与 SQL 验收无变更。只在续签后重载证书，不重启实例；尚未强制演练临期轮换。
数据库日常运行独立于 k3s；机器身份续签依赖现有 SPIRE 与 Bao，不等于运行时依赖。

生产 Patroni 原生指标已接入现有监控，两目标 up=1、五条 HA 规则 health=ok 且 inactive。
SQL 级 exporter、开发实例、备份年龄和证书到期告警尚未补齐。存储事故与持续观察边界见
[共享 etcd](shared-etcd.md#依赖维护与恢复)，不以短期验收证明底层长期稳定。

维护者明确 Ayatori 沿用独立控制面规划：本轮只准备 Instance、ExternalSecret、公开 CA、
Kustomize 与专用 ESO 只读 policy，没有向现有 k3s 安装 controller/CRD 或应用这些声明。
独立控制面还需创建实际 SecretStore/认证绑定并验收 Instance Ready；完整 Database/Tenant
供应能力以 Ayatori 自身实施为准。不能把现有 SQL 验证当作 Ayatori 已接管。

源码为 homelab-infra `infrastructure/shared-postgresql/README.md` 与
`ayatori/README.md`；部署、切换、恢复、续签及凭据引用的具体入口在那里维护，文档已发布 main；IaC 见 [IaC PR #159](https://git.ddupan.top/panxiao81/homelab-infra/pulls/159)，合并及 GitOps 接管仍待完成。
Terraform backend 已复用 `kv/k8s/seaweedfs-s3` 中受限 AK/SK；此前阻塞是 Bao 管理权限，已由
维护者重新 OIDC 登录解决，不是 S3 凭据缺失。旧 Ansible Vault 迁移仍后置。
