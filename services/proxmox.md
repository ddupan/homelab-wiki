---
title: Proxmox 日常管理入口
lifecycle: active
evidence: documented
last_reviewed: 2026-11-23
last_verified: 2026-09-25
sources:
  - homelab-infra `infrastructure/proxmox/README-ha.md`、`ansible/auth.yml`、`site.yml`、`ha.yml`、`inventory/`
watch:
  - homelab-infra:infrastructure/proxmox/README-ha.md
  - homelab-infra:infrastructure/proxmox/ansible/inventory/
  - homelab-infra:infrastructure/proxmox/ansible/auth.yml
  - homelab-infra:infrastructure/proxmox/ansible/site.yml
  - homelab-infra:infrastructure/proxmox/ansible/ha.yml
  - homelab-infra:infrastructure/proxmox/ansible/roles/pve_auth/
  - homelab-infra:infrastructure/proxmox/ansible/roles/pve_acme/
  - homelab-infra:infrastructure/proxmox/ansible/roles/pve_ha/
  - homelab-infra:infrastructure/sandbox-cluster/README.md
---

# Proxmox

Proxmox 承载 VM/LXC 与相应主机、网络和存储资源：三节点集群 `homelab`，
pve1 `192.168.10.4`、pve2 `192.168.10.7`、pve3 `192.168.10.9`。
节点配置由 `infrastructure/proxmox/ansible/` 管理，以代码为准。

## 打开管理界面

节点名为 `pve1.ad.ddupan.top`、`pve2.ad.ddupan.top`、`pve3.ad.ddupan.top`，
Web UI 在 Proxmox 默认 HTTPS 端口 `8006`：

```text
https://pve1.ad.ddupan.top:8006/
```

端口与节点代理行为见 [Proxmox pveproxy 文档](https://github.com/proxmox/pve-docs/blob/master/pveproxy.adoc)。
`pve_auth` role 声明 `ad` realm，通过 LDAPS 连接 `dc1.ad.ddupan.top:636`，启用证书校验；
域用户登录时选择 `ad` realm，可用权限取决于账号同步及 ACL。`auth.yml` 独立管理该配置。
`pve_acme` role 使用 OpenBao 内部 CA 为节点域名签证书，浏览器需信任该 CA。
PVE 没有接入 iam-login OIDC。

## 第一次定位一台虚拟机

1. 登录后在资源树中找到目标 VM/LXC，核对名称、VMID 和所在节点。
2. 查看 Summary 与任务记录，区分 guest 状态、节点状态和最近操作结果。
3. 查看 Hardware/Resources 与网络、磁盘配置，确认对应的业务服务。
4. 需要 guest 内部诊断时，再按授权使用 Console 或该 guest 的 SSH 入口。

VMID 可能被复用，不能仅凭一个旧 VMID 判断当前对象归属。
控制台可打开也不等于客户机网络、存储和业务健康。
启动、关闭、迁移、克隆及删除都是独立变更，不作为“查看状态”的附带动作。

## 持久配置与短命 VM 的职责

Ansible 管理节点软件、内核、网络、LINSTOR/DRBD 与 watchdog 等主机配置。
VM 和集群对象的管理工具以对应目录为准。UI 中临时改动需回写对应受管来源，避免后续自动化覆盖。

动态 CI VM 的使用接口见 [Gitea Dynamic Runner](gitea-dynamic-runner.md)，
其生命周期由 runner controller 负责，不逐台登记进长期 Terraform state。
每个动态 Pod/VM 独立取得 SPIFFE 身份；workflow 决定登录与请求 token。

## 网络、HA 与存储边界

VLAN/VNet 分段不能证明 guest 的机器身份；IP、MAC、VMID 的自报值不能代替可信身份验证。
修改 bridge、SDN 或路由 guest 时，先明确承载哪些业务与管理路径，不能只看当前登录是否仍连通。

集群中只有 `vm:100`（VyOS 路由器）是 HA 资源（`pve_ha` role 默认值），其他 guest 不启用 HA。
HA 描述的是故障后重新启动的路径，不承诺无中断切换。因为有 HA 资源，fencing 在整个集群生效：
失去 quorum 的节点会自重启。watchdog 使用各节点的硬件模块（pve1 `iTCO_wdt`，pve2/pve3 `sp5100_tco`，
见 inventory `host_vars`），模块变更在节点重启后生效。`ha.yml` 独立于节点基线 `site.yml`，
避免基线维护顺带改变 HA/fencing 行为。

PVE 主机存储、DRBD 副本和 k3s 的 [OpenEBS](openebs.md) 是不同管理层，
不能互相替代容量、冗余或恢复验证。快照和副本也不能自动证明具备独立备份。

故障入口依次为目标任务日志、guest、宿主节点、存储和集群网络；
涉及 quorum、fencing 或 watchdog 的处理先读 `README-ha.md`，不要套用普通单机重启排障。
长期配置入口为 `infrastructure/proxmox/ansible/`，按实际变更选择对应 playbook。

来源文件的固定版本见[来源追溯](../sources.md#proxmox)。

## Sandbox LB 与根文件系统恢复

> 2026-11-03 起 sandbox 入口已从 VyOS HAProxy 迁到 Ayatori LoadBalancer
> （homelab-infra `clusters/ayatori-prod/sandbox-k8s.yaml`、`sandbox-postgresql.yaml`，commit `0d59044`、`9f040fb`），
> VyOS 上不再有 `load-balancing haproxy`。下面的入口地址与第 7 步是 2026-09-25 事故时的记录；
> 根盘与数据库恢复步骤仍然适用，入口检查改按 Ayatori LoadBalancer 的声明进行。

当时 Sandbox 的 VyOS 入口为 PostgreSQL `10.60.0.1:5432`、K3s API
`10.60.0.13:6443`、OpenSandbox `10.60.0.13:8080`。数据库只转发到
sandbox1 `10.60.0.11:5432`；K3s 转发到两个节点的 `6443`；OpenSandbox
转发到两个节点的 `30080`。OpenSandbox `/health` 返回 200 不代表 K3s 控制面可用。
当时 OpenSandbox 的 LB 条目在 VyOS 现场存在，但不在 Ansible 模板中。

排障先检查 HAProxy 监听和每个 backend 的状态，再直连后端。若后端拒绝连接，
检查 PostgreSQL、K3s 与根文件系统，而不是仅重启 LB。
`findmnt -no SOURCE,FSTYPE,OPTIONS /` 即使显示 `rw`，同时出现
`emergency_ro` 也不能视为正常可写。

DRBD 对端失联导致 quorum 丢失时，`on-no-quorum=io-error` 会向文件系统返回
I/O 错误；ext4 可能中止 journal 并进入只读。DRBD 后来恢复 UpToDate/quorum
并不会自动解除文件系统的故障状态。检查宿主日志时用 `journalctl --utc`，
不要直接把宿主本地时间与 guest 的 UTC 时间比较。

在已获停机恢复授权后，按以下顺序处理：

1. 用 `pct config <VMID>`、`pvesm path <rootfs-volume>` 和 `drbdsetup status <resource> --verbose`
   核对容器、卷和副本关系。确认链路稳定、quorum 正常、数据副本 UpToDate，且没有其他节点挂载该卷。
2. 正常关闭故障容器，确认 stopped、卷未挂载且无遗留占用。禁止在运行中的根盘执行 fsck。
3. 执行 `pct fsck <VMID> --device rootfs --force 1`。本机 PVE 使用 `fsck -a -l -f`；
   底层返回 1 表示已修复，PVE 仍可能把它显示为命令失败。必须核对完整输出，不能把其他错误码当成功。
4. 对同一已停机、未挂载卷执行 `e2fsck -fn <verified-device>`；返回 0 后再启动容器。
   若自动安全修复未通过，暂停并评估数据恢复，不盲目加 `-y`、清空 WAL 或重建数据库。
5. 等待 PostgreSQL 完成 crash recovery；验证主库 `pg_is_in_recovery()=false`、
   standby 保持 recovery、`pg_stat_replication` 为 streaming/sync，检查 replay lag。
   不把普通 TCP check 当成数据库可写性证明，也不自动提升 standby。
6. 检查两个 K3s 服务、两个直连 API 和 VIP 的 `/readyz`、节点与 Pod Ready。
   数据库已恢复而某个 K3s 长期停在 activating 时，核对日志与进程；必要时只重启该 K3s 服务。
7. 从 VyOS 再核对每个 backend 为 UP，并验证 OpenSandbox `/health`。

2026-09-25 现场验证范围：sandbox1 根盘离线修复和只读复检通过，重新挂载不再有
`emergency_ro`；数据库恢复同步复制，采样 replay lag 为 0；两个 API 与 VIP 的
`/readyz` 均为 ok，两个节点及全部 Pod Ready。故障证据为目标 DRBD 对端 PingAck
超时、quorum 丢失及紧随其后的 ext4 写入错误；对端连接超时的上游原因尚未确定。
当时未修改 VyOS LB、DRBD quorum 策略或集群网络，存储网络复发风险没有因此消除。

事后复盘将触发线索收敛为：新 PG HDD 数据卷在 17:12 开始的初始同步发生重叠，
随后多个既有 DRBD 资源失去 quorum；15:30–15:32 的 etcd rootfs 迁移与后来的新数据卷创建
应分开记录。资源争用的具体瓶颈尚未实证。容器 `serial: 1` 和 etcd health 不等于 DRBD
同步完成；新卷维护需在创建前建立同步预算，并在允许下一卷前等待所有必要副本同步。
复盘时 PG 创建流程已在创建后加限速，但仍有初始未限速窗口，也没有同步完成屏障。

事故报告由 wiki 统一维护：[2026-09-25 DRBD quorum 抖动与 sandbox 控制面中断](../incidents/2026-09-25-drbd-quorum-sandbox.md)。
其中保存统一 UTC 时间线、跨资源影响边界、相关操作会话和后续验收条件；本页保留可复用恢复方法。
