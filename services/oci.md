---
title: OCI 登录与维护入口
lifecycle: active
evidence: documented
last_reviewed: 2026-11-23
last_verified: null
sources:
  - homelab-infra `infrastructure/oci/README.md`、`infrastructure/oci/ansible/README.md`、`.gitea/workflows/terraform.yml`
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/314eee9
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/c5b4427
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/ac9a6bd92678cb1cd91b865efcc7187ce67879ed
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/579cb7b
  - 维护者 2026-11-23 说明：OCI 与家中网络经 WireGuard 和 Tailscale 两条路径互通
watch:
  - homelab-infra:infrastructure/oci/
  - homelab-infra:.gitea/workflows/terraform.yml
  - homelab-infra:.gitea/scripts/tf.py
  - homelab-infra:infrastructure/proxmox/ansible/vyos.yml
  - homelab-infra:infrastructure/proxmox/ansible/roles/vyos_router/
---

# OCI 云上基础设施

OCI 部分由独立 Terraform root 管理云 API 资源，实例内的软件与网络配置由 Ansible 管理，以代码为准。

两台实例的用途：

| 实例 | 用途 |
|---|---|
| `oci-arm`（A1，`homelab-vm`） | 运行 [Gitea](gitea.md)（2026-11-05 起，Docker Compose + SQLite，`ansible/gitea.yml`，role `gitea`）及外部观察者 `watcher.yml` |
| `oci-amd`（E2.1.Micro，`homelab-amd`） | 与 VyOS 的 WireGuard `wg42` 隧道、iBGP 与 DN42 边界 |

此外本 root 还管理 OCI Email Delivery：Gitea 发信（`gitea-mail.tf`）和 lab
[smtp-relay](smtp-relay.md) 的独立 SMTP 用户（`smtp-relay-mail.tf`，[c5b4427](https://git.ddupan.top/panxiao81/homelab-infra/commit/c5b4427)），
两者共用发件人 `noreply@ddupan.top` 与每月免费额度。

## 第一次登录

实例位于大阪区域 `ap-osaka-1`，有两个 DNS 登录入口：

```bash
ssh ubuntu@oci-arm.ddupan.top
ssh ubuntu@oci-amd.ddupan.top
```

选择自己获准访问的实例，用既有 SSH agent/key 登录；不复制私钥或禁用 host-key 校验。
以上名称对应直连公网 A 记录，不是 Cloudflare HTTP 代理入口。
首次使用从维护者取得可信主机密钥信息。

`oci-arm`、`oci-amd` 两条 A 记录在 Cloudflare **手工维护**（关闭代理，TTL 300），
不在任何 Terraform state 中，也不在 `infrastructure/dns/records.yml`。
公网 IP 变更时需手工同步记录，修改实例不会自动更新 DNS。

## 访问家中网络与 DN42

OCI 与家中网络有两条互通路径：VyOS `wg42` ↔ OCI AMD 的 WireGuard 隧道（承载 iBGP），以及 Tailscale。
站点网络细节统一查阅 `infrastructure/oci/ansible/README.md`，其中包含 VyOS、OCI AMD、
WireGuard、BGP 和 DN42 的地址、过滤与检查步骤。本页不维护第二份邻居或路由清单。

自 2026-11-18（[579cb7b](https://git.ddupan.top/panxiao81/homelab-infra/commit/579cb7b)）起，wg42 隧道的
**VyOS 一端**（wg42、iBGP、DN42 NAT/RA/DNS）只由 `infrastructure/proxmox/ansible/vyos.yml`
（`vyos_router` 角色）写入，见 [VyOS 路由器](vyos-router.md)。`infrastructure/oci` 对路由器只读：
`vyos-wg-pubkey.yml` 读取 VyOS 的 wg42 公钥交给 AMD 的 `wireguard_bgp` 角色。wg42 私钥在 proxmox 一侧首次生成，
重建时须先跑 proxmox 那边。

使用已有网络的应用无需自行创建 WireGuard peer 或修改 BGP。
遇到私网不可达，先区分 DNS、目标服务、路由、隧道与过滤；隧道握手成功不代表业务前缀已安装。
内部家中/OCI 业务前缀不得通告给外部 DN42 邻居，不能为临时接通扩大所有前缀的 export 规则。
Docker 地址池还须避开 DN42 `172.20.0.0/14`，相关记录见 `infrastructure/docker/README.md`。

## 管理变更走哪个入口

| 修改内容 | 管理入口 |
|---|---|
| 实例、VCN、NSG、云路由等 API 对象 | `infrastructure/oci/terraform/` |
| OCI 实例内软件（Gitea、watcher、AMD 的隧道与 BGP） | `infrastructure/oci/ansible/` |
| VyOS 一端的 wg42/iBGP | `infrastructure/proxmox/ansible/`（`vyos_router`） |
| `oci-*` 公网 DNS 名称 | Cloudflare 控制台手工维护 |

Terraform 使用 OCI Object Storage 的既有远端 state。该 root 已列入 CI 的 `TF_ROOTS`
（`.gitea/workflows/terraform.yml`，[314eee9](https://git.ddupan.top/panxiao81/homelab-infra/commit/314eee9)）：
PR 上 plan，合并到 main 即 apply，main 是期望状态。CI 没有 API key，`.gitea/scripts/tf.py` 用 SPIRE JWT-SVID
（`aud=oci`）换 1 小时 UPST，以 `terraform-ci` 服务用户运行（`terraform/spire-federation.tf`），并从 Bao
`kv/infra/oci-token-exchange`、`kv/infra/terraform/oci` 取得交换凭据与实例 metadata。
本机 OCI CLI `DEFAULT` profile 只用于 bootstrap 或 CI 不可用时的本地手动运行；新 checkout 本地运行前需按
`infrastructure/oci/README.md` 准备受限 metadata 输入。
恢复目录的 state 副本不作为日常 backend，也不能上传覆盖远端对象。

**oci-arm 的 Ansible 秘密**（Gitea、watcher）由主机以 instance principal 从 **OCI Vault**
（`ansible-gitea`、`ansible-outside-watcher`）读取，role `oci_secrets`；刻意不读 Bao，也不再需要
ansible-vault 与 `.vault_pass`（[ac9a6bd](https://git.ddupan.top/panxiao81/homelab-infra/commit/ac9a6bd92678cb1cd91b865efcc7187ce67879ed)，
2026-11-18）。新主机首次部署需不带 `--check` 跑一次，因为 check 模式下尚未安装 oci-cli。

维护者审查 plan 或 Ansible check/diff 后再实施对应变更；plan/state/metadata 可能包含秘密，不进 Git 或公开文档。
保留实例 `prevent_destroy`，遇到替换计划先查原因，不能为了让 apply 通过直接移除保护。
README 中的历史配额与免费机型检查不是持续费用保证，新增资源时另行核对。

## 恢复与依赖

实例登录依赖 DNS、公网路径、SSH 授权与主机；站点访问另依赖家中路由器、云端网络规则和路由协议。
云 API 状态正常与客户机内部服务正常是不同层面的证据。

恢复设计和接管历史见 `infrastructure/oci/README.md`，网络维护及私钥边界见 `ansible/README.md`。
不把旧 state 恢复步骤、迁移收尾 playbook 或历史验证命令当作每次登录前要执行的初始化。
