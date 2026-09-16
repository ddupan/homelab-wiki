---
title: NetBox 使用指南
lifecycle: experimental
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# NetBox

NetBox 用于浏览网络设备、接口与 IP 地址关系，目前是已部署的评估环境。
权威拓扑保存在 homelab-infra 的 `apps/netbox/terraform/topology.yml`，NetBox 是它的派生镜像。
已有配置生成试验，不代表真实网络已由 NetBox 自动驱动。

本页依据工作区 `apps/netbox/README.md` 及相关设计记录整理；本轮没有登录或查询现场。

## 打开与登录

在能访问 LAN 的环境打开 [NetBox](https://netbox.ad.ddupan.top)，通过 Authelia 登录并完成二次认证。
源码记录入口访问限制为 AD 的 `netbox-admins` 组；有 AD 账号本身并不足以获得访问权限。

这里使用网关的 Authelia **forward-auth**，NetBox 接收经网关认证的用户与组信息。
NetBox 没有独立的 OIDC client；不要因 Authelia 是主 OIDC broker 就替它配置另一套 OIDC 登录。
正常使用从域名入口进入，不能绕过网关或自行构造 Remote-User 等身份头。

## 第一次浏览设备与地址

1. 在 Devices 列表中搜索要了解的设备，打开详情，查看角色、主要地址与 Interfaces。
2. 从接口查看关联的 IP 地址；有连接记录时，再沿关联对象查看另一端。
3. 在 IPAM 的 Prefixes 中搜索目标网段，例如源拓扑记录中的 `192.168.10.0/24`。
4. 查看该前缀下的地址记录，再打开地址详情，确认其关联接口和设备。

这条路径用于回答“这个地址记录给谁、接口属于哪台设备”等问题。
NetBox 中的地址状态来自资产记录，不会自动证明主机在线、地址当前无占用或 DHCP 已下发。
排查实时故障仍需相应运行证据；AI 查询现场前须按本库规则先与维护者对齐范围。
对象概念可参考 [NetBox IPAM 文档](https://netbox.readthedocs.io/en/stable/features/ipam/)。

## 发现记录需要修改时

先在 Git 中修改 `apps/netbox/terraform/topology.yml`，由维护者按该目录 README
审查 Terraform plan 并同步镜像；不要把 UI 编辑作为持久修改入口。
镜像中的手工改动可能与下次同步冲突；从拓扑文件移除对象也可能在 plan 中产生删除，需审查影响。

资产记录不保存 Wi-Fi 密码等秘密，凭据由 [OpenBao](openbao.md) 等既有秘密管理流程提供。
面向 VyOS OSPF 与 Samba AD DNS 的生成脚本属于评估成果，运行生成器与实际应用网络配置是不同步骤；
看到 NetBox 记录更新，不能宣称路由、DNS 或 DHCP 已同步。

## 遇到问题先看哪里

- 无法访问域名：检查 LAN DNS、路由及共享 Envoy 入口。
- 登录后被拒绝：核对 Authelia 访问规则及 AD 组；不要通过直接访问后端绕过认证。
- 记录缺失或不一致：对照 Git 拓扑和上一次同步记录，区分来源缺失与镜像尚未同步。
- 数据库或应用异常：转到部署 README，检查对应依赖和恢复流程。

部署、依赖、认证边界、拓扑同步与配置生成细节见 homelab-infra `apps/netbox/README.md`。
应用使用数据库与 Redis，登录链路依赖 LAN DNS、Envoy、Authelia 和 Samba AD。
本地管理员属于故障恢复入口，日常浏览不使用该路径。
