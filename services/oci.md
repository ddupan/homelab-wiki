---
title: OCI 登录与维护入口
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# OCI 云上基础设施

OCI 部分由独立 Terraform root 管理云 API 资源，实例内的软件与网络配置由 Ansible 管理。
本页仅提取 homelab-infra 工作区 `infrastructure/oci/README.md` 与 `ansible/README.md`
中已有的使用路径，不查询云资源、SSH、WireGuard 或 BGP 状态。
已核对 Terraform 的 OCI backend、provider profile 与两台实例的 `prevent_destroy` 声明。
README 有工作区修改，Ansible/Terraform 目录包含尚未提交内容；正式版本来源仍需补全。

维护者于 2026-09-16 明确：本组件优先 IaC，以代码为准。Ansible/Terraform 的声明及任务
是配置依据，README 负责解释；代码存在不等于本轮已验证部署结果。

## 第一次登录

源码记录大阪区域 `ap-osaka-1`，提供两个 DNS 登录入口：

```bash
ssh ubuntu@oci-arm.ddupan.top
ssh ubuntu@oci-amd.ddupan.top
```

选择自己获准访问的实例，用既有 SSH agent/key 登录；不复制私钥或禁用 host-key 校验。
以上名称对应直连公网 A 记录，不能当成 Cloudflare HTTP 代理入口。
实际权限、主机密钥与登录成功情况本轮未验证；首次使用从维护者取得可信主机信息。

DNS 记录的声明源为 `infrastructure/dns/records.yml`。
源 README 记录 DNS 尚未纳入 OCI Terraform state，公网 IP 变更时需协调更新记录，
不能认为修改实例就自动完成 DNS 同步。

## 访问家中网络与 DN42

站点网络细节统一查阅 `infrastructure/oci/ansible/README.md`，其中包含 VyOS、OCI AMD、
WireGuard、BGP 和 DN42 的地址、过滤与检查步骤。本页不维护第二份邻居或路由实时清单。

使用已有网络的应用无需自行创建 WireGuard peer 或修改 BGP。
遇到私网不可达，先区分 DNS、目标服务、路由、隧道与过滤；隧道握手成功不代表业务前缀已安装。
内部家中/OCI 业务前缀不得通告给外部 DN42 邻居，不能为临时接通扩大所有前缀的 export 规则。
Docker 地址池还须避开 DN42 `172.20.0.0/14`，相关记录见 `infrastructure/docker/README.md`。

## 管理变更走哪个入口

| 修改内容 | 原有管理入口 |
|---|---|
| 实例、VCN、NSG、云路由等 API 对象 | `infrastructure/oci/terraform/` |
| 主机/路由器软件、隧道及 BGP 配置 | `infrastructure/oci/ansible/` |
| DNS 名称 | `infrastructure/dns/records.yml` 与所属 DNS 后端 |

Terraform 使用 OCI Object Storage 的既有远端 state，认证依赖本机 OCI profile。
新 checkout 按源 README 准备受限 metadata 输入后才能 plan，不能复制 wiki 中不存在的“通用 tfvars”。
恢复目录的 state 副本不作为日常 backend，也不能上传覆盖远端对象。

维护者审查 plan 或 Ansible check/diff 后再实施对应变更；plan/state/metadata 可能包含秘密，不进 Git 或公开文档。
保留实例 `prevent_destroy`，遇到替换计划先查原因，不能为了让 apply 通过直接移除保护。
所读 README 的历史配额与免费机型检查不是持续费用保证，新增资源时另行核对。

## 恢复与依赖

实例登录依赖 DNS、公网路径、SSH 授权与主机；站点访问另依赖家中路由器、云端网络规则和路由协议。
云 API 状态正常与客户机内部服务正常是不同层面的证据。

恢复设计和接管历史见 `infrastructure/oci/README.md`，网络维护及私钥边界见 `ansible/README.md`。
不把旧 state 恢复步骤、迁移收尾 playbook 或历史验证命令当作每次登录前要执行的初始化。
