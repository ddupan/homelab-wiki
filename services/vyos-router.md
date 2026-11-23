---
title: VyOS 路由器（vyos-rtr）
lifecycle: active
evidence: live-verified
last_reviewed: 2026-11-23
last_verified: 2026-11-18
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/819
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/822
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/830
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/proxmox/ansible/roles/vyos_router
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/network/README.md
  - 2026-11-18 现场：vyos.yml 与 oci site.yml 实际应用 changed=0；BGP、wg42 与 laptop 路由只读检查
  - 维护者 2026-11-23 说明：pg-prod 已迁到 Ayatori LB；OCI 与家中网络经 WireGuard 和 Tailscale 两条路径互通
watch:
  - homelab-infra:infrastructure/proxmox/ansible/vyos.yml
  - homelab-infra:infrastructure/proxmox/ansible/roles/vyos_router/
  - homelab-infra:infrastructure/proxmox/ansible/vyos-monitoring.yml
  - homelab-infra:infrastructure/proxmox/README-monitoring.md
  - homelab-infra:infrastructure/network/
  - homelab-infra:infrastructure/oci/ansible/
  - homelab-infra:platform/observability/metrics/rules/vyos.yaml
  - homelab-infra:clusters/ayatori-prod/pg-prod.yaml
---

# VyOS 路由器（vyos-rtr）

## 它解决什么问题

`vyos-rtr`（PVE VM 100，`192.168.10.2`）是 LAN 之外所有内部网段的路由器：

- PVE SDN 两个 VNet 的网关与 DHCP：labnet `10.60.0.0/24`（网关 `10.60.0.1`）、retronet `10.61.0.0/24`（网关 `10.61.0.1`）。
- 与 NEC IX 跑 eBGP，只通告汇总：SDN 与 VIP 池 `10.60.0.0/14`、OCI `10.0.0.0/24`、DN42 `172.20.0.0/14`；不从 IX 收任何前缀，默认路由是指向 IX 的静态路由。
- Ayatori LoadBalancer 主机的 BGP 邻居：按环境收 VIP `/32`（Prod `10.62.0.0/24`、Dev `10.62.1.0/24`），同环境多台做 ECMP。
- 经 WireGuard `wg42` 与 OCI AMD 跑 iBGP（AS4242421811），是家中到 OCI 与 DN42 的出口；LAN 到 DN42 的 IPv4 做定向 SNAT。
  家中与 OCI 之间另有 Tailscale 作为第二条互通路径。
- 在三个 LAN 上通过 RA 下发 DN42 ULA（SLAAC + `fd00::/8` RIO，不通告默认路由），并在 `192.168.10.2:53` 提供 DN42 条件转发。

## 从哪里使用

- 普通主机不需要直接使用它：SDN 上的主机经 DHCP 获得网关；LAN 主机经 IX 学到的路由到达 SDN，
  下一跳仍是 `192.168.10.2`（IX 不改写第三方下一跳）。
- 管理入口：SSH `vyos@192.168.10.2`，仅 LAN。agent 使用 OpenBao SSH CA 签发的 5 分钟证书，principal `vyos`；
  不持有长期密钥。
- 配置入口：homelab-infra `infrastructure/proxmox/ansible/vyos.yml`（`vyos_router` 角色），需要 `vyos.vyos >= 6.2.0`。

## 第一次使用

只读确认路由是否正常：

```bash
ssh vyos@192.168.10.2 "vtysh -c 'show bgp summary'"
```

预期：NEC IX（`192.168.10.1`）、四台 LB 主机（`10.60.0.30`–`.33`）和 OCI AMD（`fe80::1811:2`，IPv4/IPv6 两个 AFI）都有
Up/Down 时长，而不是 `Active`/`Connect`。在 laptop 上 `ip route get 10.60.0.1` 应显示 `via 192.168.10.2`。

## 日常操作与限制

改配置只改 `vyos_router` 的变量或模板，然后：

```bash
cd infrastructure/proxmox/ansible
ansible-playbook vyos.yml --check --diff   # 先读清楚输出里的每一行 delete
ansible-playbook vyos.yml
ansible-playbook vyos.yml                  # 第二次应 changed=0
```

- **只有一个写入方。** 2026-11-18 起这台机器的 CLI 配置只由 `vyos_router` 写入；OCI 侧只读 wg42 公钥。
  不要新增第二个写入方：它在受管路径下写的内容会在下次运行时被删除。
- **受管路径下模板就是全部事实。** 角色把运行配置裁到 `vyos_owned_paths`，以 `vyos_config match: enforce`
  应用：模板删掉一行，路由器上就删掉；改多值节点（`name-server`、`wins-server`）会替换旧值而不是追加。
  受管路径以外的配置不受影响。
- **不能纳管机器自己生成的内容。** wg42 的 `private-key` 在路由器本机生成、不进模板，因此被排除在受管路径之外；
  纳管它会删掉私钥并断开隧道。`system login`、接口 `hw-id` 同理。
- **自带回滚。** enforce 默认 commit-confirm：变更切断会话时 10 分钟后自动回滚。它拒绝生成
  `delete service ssh …`，这部分漂移需要手工处理。
- **AMD 公钥是变量。** OCI AMD 轮换 WireGuard 密钥后，要同步更新 `vyos_oci_amd_public_key`。
- **VyOS 只有季度 Stream 发布**，升级可能改变 CLI 语法；升级前先跑 `--check` 确认模板仍被接受。

## 出问题时

1. `vtysh -c 'show bgp summary'`：哪个邻居掉了。IX 掉了 = LAN 到 SDN、VIP、OCI、DN42 全部不通；
   AMD 掉了只影响 OCI/DN42；LB 掉了只影响对应环境的 VIP。
2. OCI 方向：在 AMD 上 `sudo wg show wg-oci latest-handshakes`，握手应在 2 分钟内。
3. laptop 上 `ip route show proto bgp`：应有 `10.60.0.0/14`、`10.0.0.0/24`、`172.20.0.0/14` 经 `192.168.10.2`。
4. 告警：`VyosBgpPeerDown`、`VyosInterfaceDown`、`VyosCriticalServiceDown`（frr、kea 等关键 unit），
   见 homelab-infra `platform/observability/metrics/rules/vyos.yaml` 与 `infrastructure/proxmox/README-monitoring.md`。
5. 配置被改坏：`show system commit` / `rollback N`（需路由器可达）；`vyos.yml` 每次运行前会把变更前的
   `config.boot` 拉回控制机 `infrastructure/proxmox/vyos/backups/`（不进 Git）。

## 运维入口

- 配置：`infrastructure/proxmox/ansible/vyos.yml`（`vyos_router`：`defaults/main.yml` 是数据，`templates/vyos.conf.j2` 是渲染）。
- 机器上的文件而非 CLI 配置：`vyos-monitoring.yml`（unit 状态指标）。
- OCI 一端：`infrastructure/oci/ansible/site.yml`，其中 `vyos-wg-pubkey.yml` 只读路由器公钥。
- **重建顺序**：先跑 proxmox 的 `vyos.yml`（wg42 私钥在路由器本机首次生成），再跑 oci 的 `site.yml`。
- HA：`vm:100` 是集群里唯一的 HA 资源，提供崩溃后重启（约 1–3 分钟中断），不是无中断切换；见[Proxmox](proxmox.md)。
- 网络规划与地址：`infrastructure/network/README.md`、`ipam.yml`。

替换方案：`infrastructure/network/router.md` 的下一代路由器设计与 `infrastructure/router-nixos/` 于 2026-11-18
经维护者决定降级为备选。主要理由（`set` 行删不掉旧值）已由 enforce 解决；只有 VyOS 本身不可用时
（Stream 升级改了语法而模板跟不上、或停止发布）才重新评估。

## 当前状态与证据

2026-11-18 现场（随 [#819](https://git.ddupan.top/panxiao81/homelab-infra/commit/cb5ce8868160221161aee1680db95972a68beae2)、
[#822](https://git.ddupan.top/panxiao81/homelab-infra/commit/69a1bd530747fb6a54039243c4568b1e2e7bb94f)、
[#830](https://git.ddupan.top/panxiao81/homelab-infra/commit/5deca7056ffef9008df05ffe848a2c90d00cdf2f) 合并后执行）：

- `vyos.yml` 实际应用两次、oci `site.yml` 三次，均 `changed=0`（oci_amd、oci_arm、vyos_rtr），合并前后配置一致。
- `--check` 模拟从 LAN 列表去掉 retronet：同一次运行删除对应的 NAT、BGP network、prefix-list 规则与 DNS `allow-from`，
  没有触及受管路径以外的内容。
- BGP 全部 Established：IX 2w5d，四台 LB 约 6 天，AMD IPv4/IPv6 约 10 小时（早于当次操作）；AMD 侧 RoutedBits 外部会话 2w6d。
  wg42 最近握手 59 秒。laptop 的三条 BGP 路由下一跳均为 `192.168.10.2`。

待清理：生产 PostgreSQL 入口 `pg-prod` 已从本机的 homelab-pg-proxy（`192.168.10.2:5432`）迁到 Ayatori LoadBalancer
（`clusters/ayatori-prod/pg-prod.yaml`），路由器上残留的 homelab-pg-proxy（由 `shared-postgresql/ansible/proxy.yml` 部署）
及其 unit 监控项尚未移除，见[共享 PostgreSQL](shared-postgresql.md)。
