---
title: NetBox（已退役）
lifecycle: retired
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/9532e11f413d3557c456139c63ed9413527eeb05
  - homelab-infra `CLAUDE.md`、`infrastructure/network/README.md`、`infrastructure/network/ipam.yml`
watch:
  - homelab-infra:infrastructure/network/ipam.yml
  - homelab-infra:infrastructure/network/README.md
  - homelab-infra:infrastructure/dns/generate.py
---

# NetBox（已退役）

> **已于 2026-10-04 退役**（[9532e11](https://git.ddupan.top/panxiao81/homelab-infra/commit/9532e11f413d3557c456139c63ed9413527eeb05)
> “chore: 下线 NetBox”）。该 commit 删除了 `apps/netbox/` 整个目录（README、拓扑、生成脚本与清单），
> 并移除 Authelia 中的 NetBox 规则。`https://netbox.ad.ddupan.top`、`netbox-admins` 组与
> `apps/netbox/terraform/topology.yml` 均不再是有效入口。

## 退役原因

NetBox 是一份没人读的派生镜像，对单节点 laptop 又太重。
维护者明确要求**不要重新引入 UI 形式的网络事实来源**（source of truth）。

## 替代入口

| 需要的信息 | 现在去哪里 |
|---|---|
| 网段、地址池、DHCP 范围、VLAN、AS 号 | homelab-infra `infrastructure/network/ipam.yml`，规则见同目录 `README.md` |
| 某个地址是否已被占用 | DNS（`lab.ddupan.top`）：谁创建资源，谁注册名字，见 [LAN DNS](lan-dns.md) |
| 找下一个空闲地址 | `infrastructure/dns/generate.py --next-free <prefix>`，读现网 zone，需要 PowerDNS API key（Bao `kv/k8s/powerdns`） |
| 路由职责与 BGP 邻居 | `infrastructure/network/README.md`、[VyOS 路由器](vyos-router.md) |

`ipam.yml` 只放 DNS 表达不了的部分（地址池、保留段、AS）；已用的单个地址以 DNS 为准
（[075f2a2](https://git.ddupan.top/panxiao81/homelab-infra/commit/075f2a2)）。`generate.py` 会校验
`ipam.yml` 的网段彼此不重叠。

## 历史

2026-09 期间 NetBox 作为评估环境部署：以 Git 中的 `topology.yml` 为权威，NetBox 为只读派生镜像，
登录经 Authelia forward-auth 限制为 AD `netbox-admins` 组，另有面向 VyOS OSPF 与 Samba AD DNS 的配置生成试验。
这些路径随 9532e11 一并删除；OSPF 已于 2026-10-16 退役（见 [VyOS 路由器](vyos-router.md)），
Authelia 已于 2026-10-11 退役（见 [Authelia](authelia.md)）。原页面的浏览与修改步骤已不适用，不再保留。

旧版来源文件的固定版本见[来源追溯](../sources.md#netbox)。
