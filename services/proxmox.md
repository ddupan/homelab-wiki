---
title: Proxmox 日常管理入口
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# Proxmox

Proxmox 承载 VM/LXC 与相应主机、网络和存储资源。
本页依据 homelab-infra 工作区 `infrastructure/proxmox/README.md`、`README-ha.md`
及已有 DNS 名称整理使用入口，不检查集群成员、VM、HA 或存储现场状态。
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
