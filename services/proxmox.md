---
title: Proxmox 日常管理入口
lifecycle: active
evidence: documented
last_reviewed: 2026-09-25
last_verified: 2026-09-25
---

# Proxmox

Proxmox 承载 VM/LXC 与相应主机、网络和存储资源。
本页依据 homelab-infra 工作区 `infrastructure/proxmox/README.md`、`README-ha.md`
及已有 DNS 名称整理使用入口；初轮未检查集群成员、VM、HA 或存储现场状态。
2026-09-25 的有限现场验证仅覆盖下文 sandbox 存储恢复与 LB 链路，不代表整套 PVE/HA 验收。
源码 README 尚未跟踪，HA 文档有工作区修改；配置已进一步核对 `auth.yml`、`site.yml`、
`ha.yml` 与对应 role defaults，不将文档中的历史阶段备注当作当前配置。

维护者于 2026-09-16 明确：本组件优先 IaC，以代码为准。Ansible/Terraform 的声明及任务
是配置依据，README 负责解释；代码存在不等于本轮已验证部署结果。

## 打开管理界面

DNS 清单记录 `pve1.ad.ddupan.top`、`pve2.ad.ddupan.top`、`pve3.ad.ddupan.top`。
Proxmox 默认 HTTPS 管理端口是 `8006`，因此可按维护者确认的节点尝试：

```text
https://pve1.ad.ddupan.top:8006/
```

这是节点名与上游默认端口组合出的入口示例，未验证可达性或证书配置。
端口与节点代理行为见 [Proxmox pveproxy 文档](https://github.com/proxmox/pve-docs/blob/master/pveproxy.adoc)。
`pve_auth` role 声明 `ad` realm，通过 LDAPS 连接 `dc1.ad.ddupan.top:636`，启用证书校验；
域用户按此配置选择 `ad` realm，实际可用权限取决于账号同步及 ACL。`auth.yml` 独立管理该配置。
`pve_acme` role 使用 OpenBao 内部 CA 为节点域名签证书，浏览器需具有相应 CA 信任。
这些是代码声明，不是新的登录验证；不能因 Authelia 是 Web SSO 主入口就推断 PVE 已接入 OIDC。

## 第一次定位一台虚拟机

1. 登录后在资源树中找到目标 VM/LXC，核对名称、VMID 和所在节点。
2. 查看 Summary 与任务记录，区分 guest 状态、节点状态和最近操作结果。
3. 查看 Hardware/Resources 与网络、磁盘配置，确认对应的业务服务。
4. 需要 guest 内部诊断时，再按授权使用 Console 或该 guest 的 SSH 入口。

VMID 可能被复用，不能仅凭一个旧 VMID 判断当前对象归属。
控制台可打开也不等于客户机网络、存储和业务健康。
启动、关闭、迁移、克隆及删除都是独立变更，不作为“查看状态”的附带动作。

## 持久配置与短命 VM 的职责

源目录使用 Ansible 管理节点软件、内核、网络、LINSTOR/DRBD 与 watchdog 等主机配置。
VM 和集群对象的具体管理工具以对应目录为准，不把迁移到 Terraform 的设想写成全部完成。
UI 中临时改动需回写对应受管来源，避免后续自动化覆盖。

动态 CI VM 的使用接口见 [Gitea Dynamic Runner](gitea-dynamic-runner.md)，
其生命周期由 runner controller 负责，不能逐台登记进长期 Terraform state。
每个动态 Pod/VM 应独立取得 SPIFFE 身份；workflow 决定登录与请求 token。
源码 README 的 SDN-backed identity 和 AppRole bootstrap 段落属于早期设计记录，
不作为当前统一身份原则或最新 runner 实现的依据。

## 网络、HA 与存储边界

现有设计记录中的 VLAN/VNet 分段不能直接证明 guest 的机器身份；
IP、MAC、VMID 的自报值不能代替可信身份验证。
修改 bridge、SDN 或路由 guest 时，先明确承载哪些业务与管理路径，不能只看当前登录是否仍连通。

`README-ha.md` 记录了 VyOS guest 的 HA 和 watchdog 工作。它描述的是故障后重新启动的路径，
不应承诺无中断切换，也不能推断其他 guest 全部启用 HA。
`pve_ha` role 的资源默认值只列 `vm:100`，`ha.yml` 独立于节点基线 `site.yml`，
避免基线维护顺带改变 HA/fencing 行为。watchdog 的实际选择还需结合 inventory 覆盖与任务实现；
本轮不从旧 README 的 softdog 标题推断当前现场状态。

PVE 主机存储、DRBD 副本和 k3s 的 [OpenEBS](openebs.md) 是不同管理层，
不能互相替代容量、冗余或恢复验证。快照和副本也不能自动证明具备独立备份。

故障入口依次为目标任务日志、guest、宿主节点、存储和集群网络；
涉及 quorum、fencing 或 watchdog 的处理先读 `README-ha.md`，不要套用普通单机重启排障。
长期配置入口为 `infrastructure/proxmox/ansible/`，并按实际变更选择对应 playbook。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#proxmox)。


## Sandbox LB 与根文件系统恢复

> 2026-11-03 起 sandbox 入口已从 VyOS HAProxy 迁到 Ayatori LoadBalancer
> （homelab-infra `clusters/ayatori-prod/sandbox-k8s.yaml`、`sandbox-postgresql.yaml`，commit `0d59044`、`9f040fb`），
> VyOS 上不再有 `load-balancing haproxy`。下面的入口地址与第 7 步是 2026-09-25 事故时的记录；
> 根盘与数据库恢复步骤仍然适用，入口检查改按 Ayatori LoadBalancer 的声明进行。

当时 Sandbox 的 VyOS 入口为 PostgreSQL `10.60.0.1:5432`、K3s API
`10.60.0.13:6443`、OpenSandbox `10.60.0.13:8080`。数据库只转发到
sandbox1 `10.60.0.11:5432`；K3s 转发到两个节点的 `6443`；OpenSandbox
转发到两个节点的 `30080`。OpenSandbox `/health` 返回 200 不代表 K3s 控制面可用。
配置依据为源码 `infrastructure/sandbox-cluster/README.md`、
`infrastructure/proxmox/ansible/roles/vyos_router/` 及本轮 VyOS 现场检查；
OpenSandbox 的 LB 条目在现场存在，不能推断旧 Ansible 模板已经管理该条目。

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
本轮未修改 VyOS LB、DRBD quorum 策略或集群网络。此处保存恢复方法及有限验证边界，
不代表已经消除存储网络复发风险。


本次进一步复盘将触发线索收敛为：新 PG HDD 数据卷在 17:12 开始的初始同步发生重叠，
随后多个既有 DRBD 资源失去 quorum；15:30–15:32 的 etcd rootfs 迁移与后来的新数据卷创建
应分开记录。资源争用的具体瓶颈尚未实证。容器 `serial: 1` 和 etcd health 不等于 DRBD
同步完成；新卷维护需在创建前建立同步预算，并在允许下一卷前等待所有必要副本同步。
目前 PG 创建流程虽已在创建后加限速，仍存在初始未限速窗口，尚未补齐同步完成屏障。

事故报告由 wiki 统一维护：[2026-09-25 DRBD quorum 抖动与 sandbox 控制面中断](../incidents/2026-09-25-drbd-quorum-sandbox.md)。
其中保存统一 UTC 时间线、跨资源影响边界、相关操作会话和后续验收条件；本页保留可复用恢复方法。
