---
title: Homelab 共享 etcd
lifecycle: experimental
evidence: live-verified
last_reviewed: 2026-09-25
last_verified: 2026-09-25
---

# Homelab 共享 etcd

为 homelab 服务提供共享的配置、协调与选主存储。维护者已接受共享定位；首个消费者是
k3s 外 PostgreSQL 的 Patroni。三成员基础服务已部署，现有监控已接入，自动续签已启用；现有 k3s datastore 未迁移。

## 入口与第一次接入

部署拓扑为 laptop 原生 systemd、pve1/pve2 各一个无特权 LXC（150/151）。地址为
192.168.10.127、10.60.0.20、10.60.0.21，客户端端口 2379，三端点健康检查已通过。两个 LXC 的 rootfs 位于 `pve-rg` SSD DRBD 池。
实际接入前由管理流程交付三个 TLS endpoints、中央 CA、独立客户端证书和 Bao 秘密引用。
使用分配身份在自己的 prefix 内 put/get/delete 验证，并确认跨 prefix 被拒绝；不要使用管理员证书接应用。

证书由 OpenBao 中央 CA 签发，成员间 peer CN 受限。管理员原生 etcdctl 使用 CN=root 证书；
Patroni etcd3 gateway 使用无 CN 的 mTLS 证书加独立账号密码，不能复用管理员证书。
密码首次随机生成并存入 Bao，重复部署复用，缺失、读取失败或漂移均不静默重置。
首个消费者秘密路径为 `kv/infra/etcd/consumers/patroni-pg-prod`，授权 prefix 为
`/homelab/patroni/pg-prod/`；账号和随机密码已创建，真实 gateway 登录已验证；Patroni 已部署并通过自动切换验证。

## 依赖、维护与恢复

依赖主机网络、磁盘、systemd；证书签发及配置收敛依赖 Bao。运行使用本地证书，不要求 Bao 在线。
共享 etcd 的创建、维护和快照与数据库生命周期分离；删除 PostgreSQL 不删除 etcd。
全集群快照恢复必须协调所有消费者，不能作为单个业务的回滚。

源码实现提供每日每成员本地快照、独立认证初始化、消费者收敛和逐成员更新入口。
三个成员的原生指标已接入现有 VictoriaMetrics，不增加 exporter；内网 2381 listener 不提供 KV API。
六条规则覆盖成员采集、采集可见成员不足、无 leader、容量、fsync 和选举，现场三目标 up=1、规则 health=ok。
Alertmanager 已接入 [Telegram 通知](grafana.md#telegram-告警接入)，warning/critical 可向外通知；备份年龄与证书到期告警尚待补齐。

自动续签已启用：维护者恢复 OIDC 管理会话后，独立 cert auth、受限 policy 与每日 timer 已部署。
登录使用 laptop 现有 peer 证书，按 DNS SAN 限制身份；无 CN gateway 证书不能用于 Bao cert
登录（identity alias 为空），不会改动 etcd gateway 的无 CN 要求。首次实际续签流程三成员均
`changed=0`、service Result=success；程序固定副本由 root 管理，短期 token 用后撤销。
运行仍只依赖本地证书；续签和恢复步骤见源码 README。
业务负载下的存储延迟与完整灾难恢复演练仍待完成。
故障时先查 `homelab-etcd` systemd 日志和三端点健康；成员替换不能通过删除数据目录、重跑初始化处理。
详细操作与验收边界见 homelab-infra `infrastructure/etcd/README.md`。

存储故障处理：单成员 `NoLeader` 与频繁选举告警可能来自底层 I/O，不能直接认定整个集群失去 quorum。
2026-09-25 CT150 的 DRBD 根卷短暂丢失 quorum，ext4 journal 写入失败后进入 `emergency_ro`；
另外两成员仍健康。保存快照后停止 CT150，以 PVE 离线 fsck 修复、复查干净再启动，三成员健康及
Raft term/index 一致已重新验证，两容器根卷与新增 mp0 均可写。不要在挂载中的卷上 fsck 或直接强制 remount。
本项目两块新 HDD 数据卷后台同步上限已通过 IaC 限制为各 10 MiB/s；限速后短期未再见 PingAck 超时，
但唯一根因和长期稳定性未确证。没有更改全局 DRBD quorum/协议。对应入口为
`infrastructure/shared-postgresql/ansible/limit-resync.yml`，重复执行无变更；详细恢复过程见上述 runbook。
频繁选举规则包含 15 分钟历史窗口，故障恢复后需结合当前健康及计数判断。


## 证据与阶段边界

2026-09-25 维护者指定 laptop + 两台 PVE 各一个新 LXC，并明确复用 Bao 中央 CA；旧 Vault 迁移后置。
现场部署已应用独立 Bao PKI roles/policies，创建 LXC 150/151 并启用三成员 mTLS、认证及消费者 RBAC。
PVE 两个 LXC 已直接迁移底层 rootfs 到 `pve-rg`；逐成员停机迁卷、启动后检查 quorum，未重建容器或数据库。
2026-09-25 现场核实两个 rootfs 的目标存储与运行状态，三个 endpoint 均成功提交健康探测。
当前 PVE LXC `move-volume` 要求容器停止；操作入口为源码 `ansible/move-storage.yml`。

本地临时三节点 etcd 3.7.2 测试通过：mTLS、认证和消费者幂等、prefix 隔离、gateway 登录/写入、
密码缺失/漂移失败关闭、快照离线恢复与停止一成员后的写入。假 Bao 测试不证明真实 PKI/policy 正确；
测试进程 RSS 约 37–40 MiB 不是生产容量承诺。Terraform validate 与 Ansible lint 通过。
证书签发、秘密创建、gateway 登录和机器身份续签均已在真实服务验证。

来源为维护者指令、只读前置核查及 homelab-infra `infrastructure/etcd/`；
文档已直接发布 main（[文档 acd4b55](https://git.ddupan.top/panxiao81/homelab-infra/commit/acd4b55)），实现见 [IaC PR #159](https://git.ddupan.top/panxiao81/homelab-infra/pulls/159)，尚未合并。与数据库的关系见[共享 PostgreSQL](shared-postgresql.md#共享-etcd-设计边界)。
