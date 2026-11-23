---
title: Ayatori LoadBalancer 主机
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/loadbalancer/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/chef/policies/loadbalancer-prod.rb
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/clusters/ayatori-prod/kustomization.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/clusters/ayatori-prod/sandbox-k8s.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/network/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/611ecaee4cd3fd7ce1378973360fb3bc10da70a1
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/8b90ee59956e3fb054a2b5f37f581bd80caccc96
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/0fb1c3c9a74caf22b0d27b1d75c248bbac062166
  - 维护者 2026-11-23 说明：pg-prod 已迁到 Ayatori LB
watch:
  - homelab-infra:infrastructure/loadbalancer/
  - homelab-infra:infrastructure/chef/policies/loadbalancer-prod.rb
  - homelab-infra:infrastructure/chef/policies/loadbalancer-dev.rb
  - homelab-infra:clusters/ayatori-prod/
  - homelab-infra:infrastructure/network/README.md
  - homelab-infra:infrastructure/dns/terraform/hosts.tf
---

# Ayatori LoadBalancer 主机

## 它解决什么问题

Ayatori LoadBalancer 的数据面：每台主机跑 HAProxy、Data Plane API 和 Ayatori LB agent。
Ayatori 控制面把 `LoadBalancer`/`Backend` 声明经 Data Plane API 写成 HAProxy 的 `lb_*` 配置；
是否宣告某个 VIP 由各主机的 agent 自行判断，agent 内嵌 GoBGP，把 VIP `/32` 宣告给
[vyos-rtr](vyos-router.md)。它取代了在 VyOS 上手写 HAProxy 服务与 VIP 的做法。

| 主机 | 环境 | PVE / VMID | 地址 |
|---|---|---|---|
| lb-prod-1 | prod | pve3 / 160 | 10.60.0.30 |
| lb-prod-2 | prod | pve1 / 161 | 10.60.0.31 |
| lb-dev-1 | dev | pve1 / 162 | 10.60.0.32 |
| lb-dev-2 | dev | pve2 / 163 | 10.60.0.33 |

VIP 池：Prod `10.62.0.0/24`（AS 65100）、Dev `10.62.1.0/24`（AS 65101）；同环境两台由 VyOS 做 ECMP。

## 从哪里使用

- 使用者不直接访问 LB 主机，而是在 Ayatori 声明 `LoadBalancer` 与 `Backend`；
  Prod 的声明放在 homelab-infra `clusters/ayatori-prod/`，由 Ayatori 控制面的 Flux 同步。用法见 [Ayatori](ayatori.md)。
- 客户端使用 DNS 名，不写死 VIP：VIP 由 Ayatori 分配，服务名是指向 LB Hostname 的 CNAME
  （例如 `sandbox-k8s.lab.ddupan.top` → `k8s.sandbox.lb.lab.ddupan.top`，见 `infrastructure/dns/terraform/hosts.tf`）。
- VIP 只经 VyOS 路由可达；LAN 主机经 IX 学到 `10.60.0.0/14` 汇总后到达。

## 第一次使用

参照现有声明 `clusters/ayatori-prod/sandbox-k8s.yaml`：一个 `Backend` 列出后端地址与端口，一个
`LoadBalancer` 把端口映射到 Backend；加入同目录 `kustomization.yaml` 的 `resources` 并合并到 main。
该目录只接受 Namespace、PostgreSQLTenant、PostgreSQLDatabase、LoadBalancer、Backend、LoadBalancerHost。

## 日常操作与限制

- 主机无状态：无特权 LXC（Debian 13，1 核 / 512 MiB），Cinc 重建主机配置，Ayatori 重新收敛 `lb_*`；
  不用 DRBD、不进 PVE HA，冗余靠两台主机加 BGP。
- `LoadBalancerHost` 由各主机的 lb-agent 自行注册（ADR-0022），不在 GitOps 目录声明
  （[0fb1c3c](https://git.ddupan.top/panxiao81/homelab-infra/commit/0fb1c3c9a74caf22b0d27b1d75c248bbac062166)）。
  agent 首次以节点身份加入控制面需运行 `infrastructure/chef/ansible/join.yml`（见 [Cinc](chef.md)）。
- 部署时才确定的值（AS、邻居、VIP 段、agent 版本、graceful restart 时间）在 `infrastructure/chef/policies/loadbalancer-{prod,dev}.rb`。
- Data Plane API 必须以 lab 名访问：证书经 ACME 签发，没有 IP SAN。
- 已迁到 LB 的入口包括 sandbox k3s API / OpenSandbox API 与 sandbox PostgreSQL（2026-11-03），以及生产 PostgreSQL
  `pg-prod`（`clusters/ayatori-prod/pg-prod.yaml`，见[共享 PostgreSQL](shared-postgresql.md)）。

## 出问题时

- agent 的 `/status` 与 `/metrics` 在 `<主机地址>:9641`；controller 读 `/status` 判断就绪。
- VIP 不可达：在 vyos-rtr 上看对应环境 peer-group 的 BGP 邻居与收到的 `/32`（见 [VyOS 路由器](vyos-router.md)）。
- agent 崩溃或被杀时，路由器保留该主机路径至多 30 s（graceful restart，ADR-0025）。

## 运维入口

- 主机：[infrastructure/loadbalancer/](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/loadbalancer)
  （`ansible/lxc.yml` 建 LXC 并注册 DNS），配置由 [Cinc](chef.md) `homelab_loadbalancer` cookbook 完成。
- 网络规则：[infrastructure/network/README.md](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/network/README.md)。
- 主机配置用 Chef `converge.py` 收敛（见 [Cinc](chef.md)）。

## 当前状态与证据

- LB policy 于 2026-11-03 升级到 lb-agent 取代 gobgpd
  （[611ecae](https://git.ddupan.top/panxiao81/homelab-infra/commit/611ecaee4cd3fd7ce1378973360fb3bc10da70a1)），
  同日 sandbox-k8s 声明 LoadBalancer（[8b90ee5](https://git.ddupan.top/panxiao81/homelab-infra/commit/8b90ee59956e3fb054a2b5f37f581bd80caccc96)）。
- VyOS 侧 2026-11-18 的现场检查（四台 LB 主机 BGP 均 Established）见 [VyOS 路由器](vyos-router.md#当前状态与证据)。
