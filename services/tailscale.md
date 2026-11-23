---
title: Tailscale 远程访问指南
lifecycle: unknown
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
watch:
  - homelab-infra:apps/tailscale/
---

# Tailscale

Tailscale 提供远程访问 homelab 的网络路径。维护者于 2026-09-16 表示没有需补充的动态事项；
本页根据 `apps/tailscale/subnet-routes.sh` 和共享 PostgreSQL Service 配置整理。
未读取含 OAuth 值的安装脚本，也未查询 tailnet、路由批准状态或现场连通性。

## 两种访问路径

| 路径 | 来源记录的用途 |
|---|---|
| laptop 子网路由 | 访问 LAN 与两个 SDN 网段中的原有地址 |
| Kubernetes operator 暴露 Service | 为特定 Service 提供 tailnet 入口，例如共享 PostgreSQL |

子网脚本将 laptop（LAN 地址 `192.168.10.127`）记录为唯一子网路由器，声明以下完整路由集合：

- `192.168.10.0/24`：homelab LAN。
- `10.60.0.0/24`：SDN labnet。
- `10.61.0.0/24`：SDN retronet。

operator 管理的 Service 入口不能直接视为新的通用子网路由器。
子网路由可达也不等于拥有所有目标服务的应用权限。

## 第一次从远程客户端访问

1. 在自己的客户端登录维护者指定的 tailnet，完成该设备所需的批准流程。
2. 确认客户端接受子网路由。Linux 客户端需要时可执行下面的设置；它改变本机路由接受配置。
3. 打开已有权限的 LAN 服务，例如 [Grafana](grafana.md)。域名还须通过适当的 DNS 配置解析。

```bash
sudo tailscale set --accept-routes=true
```

客户端行为见 [Tailscale 子网路由文档](https://tailscale.com/docs/features/subnet-routers)。
服务登录仍按该服务自己的流程进行。
如果访问 operator 暴露的 Service，使用维护者提供的 tailnet 地址；
不要把 Kubernetes `.svc.cluster.local` 名称当成远程客户端已经可解析的名称。

## 路由、DNS 与权限分别检查

“客户端已登录”“路由已广播”“路由已批准”“访问规则允许”和“目标服务可用”是不同条件。
LAN 的 [Blocky / 路由器 DNS 设计](lan-dns.md) 不自动证明远程客户端已获得相同解析配置。
IP 可达而域名失败时，先查看远程客户端 DNS 路径，不直接改 LAN DNS。

脚本广播的 `10.60.0.0/14` 是 laptop 经 BGP 学到的路由：laptop 与 NEC IX 建邻居，IX 转发
[VyOS](vyos-router.md) 的汇总，下一跳保持 `192.168.10.2`（OSPF 已于 2026-10-16 退役）。
即使 Tailscale 仍广播该前缀，laptop 上 BGP 路由缺失也会导致转发失败；用 `ip route show proto bgp` 核对。
新增路由还需 tailnet 批准及访问规则配合，单看广播配置不足以验收。

`apps/tailscale/subnet-routes.sh` 是维护端脚本，`--advertise-routes` 替换完整集合；
普通客户端接入无需执行它。新增网段时按完整声明审查，避免意外移除既有路由。
现有脚本提供批准信息的查看方法；执行现场检查前仍需按本库规则对齐范围。

依赖为 Tailscale 控制与数据路径、laptop 转发及目标网络；SDN 另依赖 [VyOS](vyos-router.md) 与 IX 之间的 BGP，
operator Service 另依赖 Kubernetes 和 operator。
本页没有记录 tailnet OAuth、设备密钥或凭据内容。
