---
title: LAN DNS（Blocky、路由器与 Samba AD）
lifecycle: active
evidence: documented
last_reviewed: 2026-11-23
last_verified: null
sources:
  - 维护者于 2026-09-16 提供的现状说明
  - homelab-infra `apps/blocky/`、`platform/external-dns/README.md`、`apps/poweradmin/README.md`、`infrastructure/dns/README.md`、`infrastructure/network/ipam.yml`
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/f83c6e5
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/219acc4
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/163f58d
watch:
  - homelab-infra:apps/blocky/
  - homelab-infra:apps/poweradmin/
  - homelab-infra:platform/external-dns/
  - homelab-infra:infrastructure/dns/
  - homelab-infra:infrastructure/network/ipam.yml
  - homelab-infra:infrastructure/samba-ad/router-dns-nec-ix.md
---

# LAN DNS

LAN 以 Blocky 为主要 DNS 入口，路由器同时承担 Blocky 上游和客户端备用 DNS 的角色。
Samba AD 继续提供域 DNS 服务。
服务与主机的新名字放在内部 zone `lab.ddupan.top`，由 Blocky 后面的 PowerDNS 权威解析，
`ad.ddupan.top` 只剩 AD 自身记录和迁移中的旧名，见[下文](#labddupantop-与-powerdns)。

## 当前配置

主机 DNS 已尽量统一到 Blocky：所有通过 DHCP 获取 DNS 配置的主机，下发的是主 DNS Blocky、副 DNS 路由器。

| 组件 | 职责 | 地址 |
|---|---|---|
| Blocky | LAN 主 DNS；上游为路由器 | `192.168.10.127` |
| NEC 路由器 | 运行 DNS 服务，作为 Blocky 上游及 DHCP 客户端的备用 DNS | `192.168.10.1` |
| Samba AD | 域 DNS | `192.168.10.5` |

```text
DHCP 下发给客户端：
  主 DNS → Blocky
  副 DNS → 路由器

Blocky 的上游 → 路由器 DNS
Samba AD → 保留域 DNS 职责
```

路由器的“备用”是相对客户端主 DNS 而言；它同时是 Blocky 正常解析链路中的上游。
这张图不含 AD 域或 DN42 条件转发，它们并非全部交给路由器。

## 主机如何使用

主机通过 DHCP 自动获取 DNS 配置：主 DNS 为 Blocky，副 DNS 为路由器，无需手工设置。

## lab.ddupan.top 与 PowerDNS

PowerDNS 于 [f83c6e5](https://git.ddupan.top/panxiao81/homelab-infra/commit/f83c6e5)、external-dns 于
[219acc4](https://git.ddupan.top/panxiao81/homelab-infra/commit/219acc4) 引入（2026-10-04）。

- **权威服务器**：`apps/blocky/compose.yaml` 中的 `pdns` 容器与 Blocky 同一 compose stack，
  Blocky 用条件转发把 `lab.ddupan.top` 交给它（compose 网络内固定地址 `172.28.0.53`）。
  pdns 的 DNS 端口不对外发布，客户端只查 Blocky；HTTP API 在 `192.168.10.127:8053`，
  key 在 Bao `kv/k8s/powerdns`（`api_key`）。pdns 的 SQLite 是派生状态，可由 Terraform 与 external-dns 重建，不做备份。
- **单实例是有意的**：Blocky 与大多数名字指向的 Envoy 都在 laptop 上，第二个 pdns 需等有第二台常开机器
。
- **Pod 与 Tailscale**：k3s CoreDNS 把 `lab.ddupan.top` 转发给 Blocky `192.168.10.127`，见
  [k3s 集群 DNS](k3s-dns.md)；tailnet 客户端靠 MagicDNS split DNS `lab.ddupan.top -> 192.168.10.127`
  （admin console 手工配置）。

### 记录归谁写

记录跟着创建它所命名之物的代码走（[163f58d](https://git.ddupan.top/panxiao81/homelab-infra/commit/163f58d)），
不为“总览”重新集中到一个文件：

| 记录 | 写入方 | 位置 |
|---|---|---|
| zone 本身、没有任何代码创建的主机（裸机、手建 VM、VIP） | Terraform（CI，`TF_ROOTS`） | `infrastructure/dns/terraform/hosts.tf` |
| 有 owner 的资源 | owner 自己的 root | 例：incus Terraform 写 `ayatori-*`，etcd `lxc.yml` 写 `etcd-pve*` |
| HTTPRoute 主机名 | external-dns（`platform/external-dns/`） | 自动；只处理挂在 `https-lab` listener、域名在 `lab.ddupan.top` 下的路由 |
| 临时、手工名字 | 人工 | Poweradmin Web UI |

external-dns 给自己写的每条记录加 TXT 归属标记，路由删除时一并删除，从不动没有标记的记录；
与 Terraform 名字冲突时跳过而不接管。
在 Poweradmin 里改 Terraform 或 external-dns 拥有的记录会被下一次 apply/同步覆盖。

### Poweradmin（查看与临时记录）

Web UI 入口为 `https://dns.lab.ddupan.top`（旧名 `dns.ad.ddupan.top` 过渡期并存，`apps/poweradmin/httproute.yaml`），
仅 LAN/Tailscale 可达。登录为 AD LDAP，仅限 `platform-admins` 组的**直接**成员；
每个人首次使用前需由管理员先建本地 stub 用户并勾选 LDAP 认证。本地 `admin` 是 DC 故障时的 break-glass 登录。
Poweradmin 只经 PowerDNS HTTP API 读写，不碰 pdns 数据库；它跑在 k3s 中，集群故障只影响 UI，不影响解析。

### `records.yml` 现在只管 split horizon

`infrastructure/dns/records.yml` 原是 AD DNS 时代的统一清单，现在只剩 split-horizon 记录
（如 `sso.ddupan.top`、`spire-oidc.ddupan.top` 在 LAN/Pod 内指向 Envoy），由 `generate.py`
渲染进 Blocky `config.yml` 与 CoreDNS `coredns-custom.yaml`。新服务与新主机名**不再**加入
`records.yml` 或 AD。地址池已移到 `infrastructure/network/ipam.yml`。

## NEC IX DHCP 地址池

2026-09-14 将主 LAN 动态池从 `192.168.10.10–250` 收窄为
`192.168.10.128–250`，并为 Buffalo AP（`d4:2c:46:09:07:b0`）固定分配
`192.168.10.10`。`.251–.254` 保留，尚未分配；不能因为扫描无响应就将其用于新设备。
DHCP 下发网关 `192.168.10.1`、主 DNS `192.168.10.127`、备用 DNS
`192.168.10.1`，租期为 4 小时。

地址池修改会清空 NEC IX 当前租约表，但终端可能继续使用旧地址直到续租。
变更后 Kata LXC 实验节点已续租为 `.128`；迁移其他动态客户端前应先检查活动任务，
并在续租后分别验证主机网络和其内部 k3s 等服务。地址池及预留段的声明维护在
homelab-infra `infrastructure/network/ipam.yml` 的 `ranges`；NetBox 已于 2026-10-04 退役（见 [NetBox](netbox.md)）。
分配新静态地址用 `infrastructure/dns/generate.py --next-free <prefix>`，它读取现网 zone 作为已用集合。

回滚时不能直接恢复整份路由器配置；应先确认 `.10–.127` 没有静态占用，再在 DHCP
profile 中恢复原范围并移除 AP 固定绑定，保存后重新核对租约、DNS 和 `ipam.yml` 声明。

## 维护入口

以下路径相对于 homelab-infra，保留部署与操作细节的原有归属：

- `apps/blocky/README.md`：Blocky 与 PowerDNS 部署、分流和检查方法。
- `infrastructure/dns/README.md`：各视图的权威服务与所有权；`terraform/hosts.tf` 为无 owner 主机；
  `records.yml` 仅剩 split horizon。
- `platform/external-dns/README.md`、`apps/poweradmin/README.md`：HTTPRoute 自动记录与 Web UI。
- `infrastructure/network/README.md`、`ipam.yml`：地址池与 IPAM 规则。
- `infrastructure/samba-ad/README.md`：域 DNS 与 Samba 配置（AD 记录在 `ansible/group_vars/all/dns.yml`）。
- `infrastructure/samba-ad/router-dns-nec-ix.md`：路由器 DNS 记录。

路由器自身的更上游和 AD/DN42 条件转发明细见 `infrastructure/samba-ad/router-dns-nec-ix.md`。

## 关键服务 DNS 冗余目标（2026-09-30 已接受，进行中）

[9 月 30 日事故](../incidents/2026-09-30-dc-dns-openbao.md)确认单 DC DNS 停止会令
Bao 域名访问、ESO 和监控认证同时失败。维护者决定：完整 AD 高可用暂未建立时，
先让关键服务 DNS 容忍单 DC 故障。原有域权威与 RRset 所有权规则继续有效。

至少需要两个可独立提供受保护服务记录的 DNS 实例，覆盖不同宿主故障域，
备用启动不依赖先访问 AD/Bao 或故障中的 k3s。具体服务、分发及客户端切换方案待设计；
服务记录的声明入口是[上文](#labddupantop-与-powerdns)的 PowerDNS 各写入方。
两个 resolver 都转发到同一 DC 或仅依靠缓存，不满足这一目标。

验收必须包含 DC 停止、缓存过期、备用冷启动、任一 DNS 宿主故障，以及 LAN/Pod
实际解析与 Bao TLS/ESO/监控认证。独立 DNS 不保证 LDAP、Kerberos 或 AD 动态记录高可用；
这些边界应分别标明。详细故障证据和整改标准以事故报告为准。

本节是已接受的目标，尚未实现。2026-09-30 现场验证了 DC DNS 与 Bao 依赖链恢复。
