---
title: 按任务查找文档
last_reviewed: 2026-11-18
---

# 按任务查找文档

先找任务，再读相关服务页；不必一次读取整个仓库。
需要环境清单时看[服务总览](../services/index.md)，准备变更时先读[架构约束](../architecture/constraints.md)。

| 要做什么 | 先读 | 需要时再读 |
|---|---|---|
| 评估独立 IAM 与 AI agent 身份 | [iam-login](../services/iam-login.md)、[独立 IAM 草案](../architecture/independent-iam-draft.md) | [Hydra（已退役）](../services/hydra.md) 的 PoC 记录 |
| 设计或实现 Ayatori 控制面能力 | [Ayatori 控制面边界](../architecture/ayatori-control-plane.md) | Ayatori 仓库 ADR、对应领域 API 与 adapter 文档 |
| 部署、发布 Ayatori 或用它申请数据库 | [Ayatori 控制面](../services/ayatori.md) | [Incus](../services/incus.md)、[OpenBao](../services/openbao.md)、[共享 PostgreSQL](../services/shared-postgresql.md) |
| 发布新的 LAN Web 服务 | [发布新服务](publish-service.md) | [DNS](../services/lan-dns.md)、[iam-login](../services/iam-login.md)、[homepage](../services/homepage.md) |
| 写 CI 或选择 Pod/VM runner | [Gitea / Actions](../services/gitea.md) | [Dynamic Runner](../services/gitea-dynamic-runner.md)、[SPIFFE](../services/spire.md)、[`ci-actions@v1`](https://git.ddupan.top/panxiao81/ci-actions/src/tag/v1) |
| 为 CI 缓存依赖（PyPI/npm/Go/Galaxy/Terraform 等） | [artifact-keeper](../services/artifact-keeper.md) | 少量未迁移的仍在 [Nexus](../services/nexus.md)；另见 [Dynamic Runner](../services/gitea-dynamic-runner.md)、[OpenBao](../services/openbao.md) |
| 拉取或发布容器镜像 | [zot](../services/zot.md) | [SPIFFE](../services/spire.md)；S3 后端维护才读 SeaweedFS |
| 使用 S3 对象存储 | [SeaweedFS](../services/seaweedfs.md) | [OpenBao](../services/openbao.md) |
| 给应用分配数据库 | [共享 PostgreSQL](../services/shared-postgresql.md) | [计划中的 DBaaS](../services/postgresql-tenant-operator.md) |
| 给应用提供秘密或存储 | [External Secrets](../services/external-secrets.md)、[OpenEBS](../services/openebs.md) | [OpenBao](../services/openbao.md) |
| 盘点或补齐监控与告警 | [监控覆盖与补齐计划](monitoring-coverage.md) | [基础监控运维](monitoring-foundation.md)、[Grafana](../services/grafana.md) |
| 排查内存、日志或追踪 | [Grafana](../services/grafana.md) | 对应服务源码 runbook |
| 排查域名解析 | [LAN DNS](../services/lan-dns.md)或[Pod DNS](../services/k3s-dns.md) | [Tailscale](../services/tailscale.md)，如果请求来自远程客户端 |
| 排查登录或域权限 | [iam-login](../services/iam-login.md)、[Samba AD](../services/samba-ad.md) | 具体应用的权限说明 |
| 为 workload 提供机器身份 | [SPIFFE](../services/spire.md) | 目标服务的 token 与权限规则；进度回到 #34 |
| 使用消息队列 | [NATS](../services/nats.md) | consumer 项目自己的协议与队列文档 |
| 调用模型或处理文档 | [ai-gateway](../services/ai-gateway.md)、[Marker](../services/marker.md) | [OpenViking](../services/openviking.md)，如果需要检索 |
| 让应用发送邮件 | [SMTP relay](../services/smtp-relay.md) | 消费者的发信配置 |
| 远程访问或查看地址规划 | [Tailscale](../services/tailscale.md) | 地址规划见 homelab-infra `infrastructure/network/ipam.yml`；已用地址以 DNS 为准 |
| 改路由、SDN 网关/DHCP、到 OCI 或 DN42 的连通 | [VyOS 路由器](../services/vyos-router.md) | [OCI](../services/oci.md)、[Proxmox](../services/proxmox.md)；网络规划见 homelab-infra `infrastructure/network/` |
| 改节点配置（etcd、Ayatori、LB、dc1 等） | [Chef / Cinc](../services/chef.md) | 对应 policy 与 cookbook |
| 申请负载均衡 VIP | [Ayatori LoadBalancer](../services/ayatori-loadbalancer.md) | [Ayatori](../services/ayatori.md)、[VyOS 路由器](../services/vyos-router.md) |
| 用云端 runner 或查看云账单 | [GCP](../services/gcp.md) | [Dynamic Runner](../services/gitea-dynamic-runner.md) |
| 管理云主机或虚拟机 | [OCI](../services/oci.md)、[Proxmox](../services/proxmox.md) | 对应 IaC 和网络/HA runbook |
| 使用 PS3 内容或 KMS 服务 | [ps3netsrv](../services/ps3netsrv.md)、[vlmcsd](../services/vlmcsd.md) | 各自客户端配置 |

## 给 AI 接续一个任务

提供目标、目标服务、已经授权的操作范围，以及你掌握但尚未写入文档的变化。
一个简短的任务交接可以这样写：

```text
目标：为某个新应用增加 LAN HTTPS 入口。
入口文档：guides/publish-service.md。
已有条件：应用 namespace、Service 名称与端口、计划域名。
本次范围：先准备配置与文档 PR；尚未授权现场部署。
动态背景：相关 ticket / PR，或维护者最新说明。
完成条件：配置可审阅，检查通过，说明来源与未执行的验证。
```

这个例子的范围仅用于演示，不能覆盖具体任务已经获得的授权。
Samba AD、OCI、Proxmox 已明确以 IaC 为准，可直接核对其代码；其他动态项目按既定规则对齐来源。
身份设计、配置声明、历史实施记录和本次现场证据应分别表达。

## 找到资料后如何判断是否足够

服务页中的 `last_reviewed` 表示文档审阅时间，`last_verified` 才表示对应现场验证时间。

检索、转换或 AI 摘要用于定位原文；结论仍应关联到源码、维护者说明或 ticket。
工作完成后，将持久使用方法写入服务页，将一次变化留在 commit/PR，动态进度回到原项目 ticket。
原仓库 README 同步目前按维护者要求暂缓，不将其列为每次任务的前置条件。

- [证书、秘密同步与 GitOps 监控](monitoring-controllers.md)：证书临期、ESO 同步与 Flux Ready 排障。
- [CNPG、NATS 与 SeaweedFS 监控](monitoring-data-services.md)：数据库连接、消息容量与存储故障。

- [OpenBao 监控接入维护](openbao-monitoring-maintenance.md)：窗口准备、YubiKey 人工解封交接与回滚。
