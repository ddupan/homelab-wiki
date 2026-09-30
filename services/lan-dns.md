---
title: LAN DNS（Blocky、路由器与 Samba AD）
lifecycle: active
evidence: documented
last_reviewed: 2026-09-30
last_verified: null
sources:
  - 维护者于 2026-09-16 提供的现状说明
---

# LAN DNS

LAN 以 Blocky 为主要 DNS 入口，路由器同时承担 Blocky 上游和客户端备用 DNS 的角色。
Samba AD 继续提供域 DNS 服务，相关配置按维护者说明已完成。

## 当前配置口径

维护者于 2026-09-16 说明：已经尽量将主机 DNS 统一到 Blocky；
所有通过 DHCP 获取 DNS 配置的主机，下发的是主 DNS Blocky、副 DNS 路由器。
本页据此修正初轮盘点中的“Blocky 尚未成为正式 resolver”判断。

| 组件 | 职责 | 地址依据 |
|---|---|---|
| Blocky | LAN 主 DNS；上游为路由器 | 原仓库记录 `192.168.10.127` |
| NEC 路由器 | 运行 DNS 服务，作为 Blocky 上游及 DHCP 客户端的备用 DNS | 原仓库记录 `192.168.10.1` |
| Samba AD | 继续运行域 DNS，相关配置已完成 | 原仓库记录 `192.168.10.5` |

地址沿用初轮仓库记录，现状以维护者说明为准，本轮未查询现场。
维护者明确无需逐台确认主机；不将主机覆盖核实列为待办。

```text
DHCP 下发给客户端：
  主 DNS → Blocky
  副 DNS → 路由器

Blocky 的上游 → 路由器 DNS
Samba AD → 保留域 DNS 职责，相关配置已完成
```

路由器的“备用”是相对客户端主 DNS 而言；它同时是 Blocky 正常解析链路中的上游。
这张图只表达本次确认的关系，不把 AD 域或 DN42 条件转发简化成全部交给路由器。

## 主机如何使用

主机通过 DHCP 自动获取 DNS 配置：主 DNS 为 Blocky，副 DNS 为路由器。
当前知识库以此作为 LAN 客户端配置口径，无需另行进行主机覆盖盘点。

## NEC IX DHCP 地址池

2026-09-14 将主 LAN 动态池从 `192.168.10.10–250` 收窄为
`192.168.10.128–250`，并为 Buffalo AP（`d4:2c:46:09:07:b0`）固定分配
`192.168.10.10`。`.251–.254` 保留，尚未分配；不能因为扫描无响应就将其用于新设备。
DHCP 下发网关 `192.168.10.1`、主 DNS `192.168.10.127`、备用 DNS
`192.168.10.1`，租期为 4 小时。

地址池修改会清空 NEC IX 当前租约表，但终端可能继续使用旧地址直到续租。
变更后 Kata LXC 实验节点已续租为 `.128`；迁移其他动态客户端前应先检查活动任务，
并在续租后分别验证主机网络和其内部 k3s 等服务。地址池及预留段的声明同时维护在
`apps/netbox/terraform/topology.yml`。

回滚时不能直接恢复整份路由器配置；应先确认 `.10–.127` 没有静态占用，再在 DHCP
profile 中恢复原范围并移除 AP 固定绑定，保存后重新核对租约、DNS 和 NetBox 声明。

## 维护入口与待补充范围

以下路径相对于 homelab-infra，保留部署与操作细节的原有归属：

- `apps/blocky/README.md`：Blocky 部署、分流和检查方法。
- `infrastructure/samba-ad/README.md`：域 DNS 与 Samba 配置。
- `infrastructure/samba-ad/router-dns-nec-ix.md`：路由器 DNS 记录。
- `infrastructure/dns/README.md`、`records.yml`：跨视图 DNS 声明与所有权。

路由器自身的更上游和 AD/DN42 条件转发明细未在本次补充，也不因此自动产生核查任务。
需要进一步查询时，先向维护者确认当前工作和范围，不因旧文档差异直接发起现场检查。

## 关键服务 DNS 冗余目标（2026-09-30 已接受，待实现）

[9 月 30 日事故](../incidents/2026-09-30-dc-dns-openbao.md)确认单 DC DNS 停止会令
Bao 域名访问、ESO 和监控认证同时失败。维护者决定：完整 AD 高可用暂未建立时，
先让关键服务 DNS 容忍单 DC 故障。原有域权威与 RRset 所有权规则继续有效。

至少需要两个可独立提供受保护服务记录的 DNS 实例，覆盖不同宿主故障域，
备用启动不依赖先访问 AD/Bao 或故障中的 k3s。静态服务记录继续以
`infrastructure/dns/records.yml` 为声明入口，具体服务、分发及客户端切换方案待设计。
两个 resolver 都转发到同一 DC 或仅依靠缓存，不满足本次目标。

验收必须包含 DC 停止、缓存过期、备用冷启动、任一 DNS 宿主故障，以及 LAN/Pod
实际解析与 Bao TLS/ESO/监控认证。独立 DNS 不保证 LDAP、Kerberos 或 AD 动态记录高可用；
这些边界应分别标明。详细故障证据和整改标准以事故报告为准。

本节是已接受的目标，尚未部署；2026-09-30 仅现场验证 DC DNS 与 Bao 依赖链恢复，
没有重新验收本页全部 DHCP、Blocky 和路由器配置，因此不刷新整页 `last_verified`。
