---
title: LAN DNS（Blocky、路由器与 Samba AD）
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
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

## 维护入口与待补充范围

以下路径相对于 homelab-infra，保留部署与操作细节的原有归属：

- `apps/blocky/README.md`：Blocky 部署、分流和检查方法。
- `infrastructure/samba-ad/README.md`：域 DNS 与 Samba 配置。
- `infrastructure/samba-ad/router-dhcp-nec-ix.md`：路由器 DHCP 记录。
- `infrastructure/samba-ad/router-dns-nec-ix.md`：路由器 DNS 记录。
- `infrastructure/dns/README.md`、`records.yml`：跨视图 DNS 声明与所有权。

本次只更新知识库；原工作区中“Blocky 未成为正式 resolver”的旧描述尚待同步。
路由器自身的更上游和 AD/DN42 条件转发明细未在本次补充，也不因此自动产生核查任务。
需要进一步查询时，先向维护者确认当前工作和范围，不因旧文档差异直接发起现场检查。
