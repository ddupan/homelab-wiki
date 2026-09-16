---
title: Samba AD 日常使用入口
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# Samba Active Directory

Samba AD 提供人的目录身份、Kerberos、LDAP、域 DNS 和组策略；
[Authelia](authelia.md) 在此之上提供 Web 登录，[SPIFFE](spire.md) 负责 workload 身份。
AD 组成员资格与每个服务最终授予的权限仍需分别配置。

本页根据 homelab-infra 工作区 `infrastructure/samba-ad/README.md` 整理。
已核对 Ansible 的域变量、`join-windows.yml`、`join-member.yml` 与 member role 任务。
这些来源含未提交修改；没有查询域成员、用户或现场配置。
DNS 的已确认口径见 [LAN DNS](lan-dns.md)，不重新盘点主机。

维护者于 2026-09-16 明确：本组件优先 IaC，以代码为准。Ansible/Terraform 的声明及任务
是配置依据，README 负责解释；代码存在不等于本轮已验证部署结果。

## 域与管理入口

| 项目 | 已有资料中的值 |
|---|---|
| DNS domain | `ad.ddupan.top` |
| Kerberos realm | `AD.DDUPAN.TOP` |
| NetBIOS domain | `DDUPAN` |
| 域控 | `dc1.ad.ddupan.top` / `192.168.10.5` |
| 图形管理 | Windows 管理机上的 RSAT：AD Users & Computers、GPMC、DNS |

管理机地址与登录身份由维护者提供。日常 Web 登录从对应应用进入 Authelia，
无需登录域控，也不向普通应用交付 Domain Administrator 凭据。

## 入域之前与入域路径

入域设备需要准确时间、域控连通性和能找到 AD SRV 记录的 DNS 路径。
不能直接照抄源 README 通用示例中的 `10.10.10.10`、`ad.example.com` 或 `EXAMPLE`。
也不要为入域统一改写所有 LAN 主机 DNS；按该设备的域解析需求配置，保留既有 LAN 设计。

Windows 管理机按 `infrastructure/samba-ad/ansible/` 的 inventory 与 `join-windows.yml`
管理，先核对目标主机、WinRM 与所用账号，再由维护者执行入域流程。
README 的手工命令用于解释角色行为，不是重新建域的日常操作步骤。

Linux 的 `join-member.yml` 面向 Samba member fileserver：它配置 winbind、NSS、SMB 与域解析，
明确不安装 `libpam-winbind`。因此文件服务器入域成功不等于已经启用 Linux 系统域账号登录。
修改前阅读角色对现有 `smb.conf`、共享与 UID/GID 映射的处理，不能将普通客户端套成文件服务器。

## 第一次查看用户与组

在已获管理授权的域控会话中，可使用以下只读命令；`YOUR_GROUP` 替换为目标组：

```bash
sudo samba-tool user list
sudo samba-tool group listmembers YOUR_GROUP
```

也可在 RSAT 的 AD Users & Computers 中查找用户，打开其组成员关系。
命令语义见 [Samba samba-tool 手册](https://www.samba.org/samba/docs/current/man-html/samba-tool.8.html)。
输出含账号信息，按任务范围使用，不把完整人员目录复制进公开 wiki。
本轮没有执行这些命令。

新增用户、组、权限或重置密码会改变目录状态，按现有 Ansible 声明或维护流程实施，
避免 UI 临时改动与下一次配置同步互相覆盖。密码通过受控交互或秘密管理提供，不写进命令示例。
应用权限排障先核对 AD 组，再核对 Authelia 策略与应用内映射。

## 故障与维护边界

入域失败先区分 DNS/SRV、时间、连通性与账号权限；已有成员认证异常再看信任关系及 winbind。
`runbook-winbind-rpcd.md` 保存 laptop 文件服务器的相关排障记录，不将该问题直接套用所有成员。

静态 DNS 声明入口为 `infrastructure/dns/records.yml`，只管理明确列出的 RRset，
不清理 Samba 自动维护的域控制器 locator、Kerberos 等记录。
新服务 DNS 接入见[发布新服务](../guides/publish-service.md)。

域备份、第二域控和恢复方案回到源码 README；有备份命令不代表已建立定时异机备份或演练过恢复。
域控身份数据库与应用数据不同，不能通过重跑建域、清空数据库来排查普通登录失败。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#samba-ad)。
