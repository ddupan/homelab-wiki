---
title: Samba AD 日常使用入口
lifecycle: active
evidence: documented
last_reviewed: 2026-11-23
last_verified: null
sources:
  - homelab-infra infrastructure/samba-ad/README.md、ansible/
  - homelab-infra infrastructure/chef/policies/samba-dc.rb
  - homelab-infra CLAUDE.md
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/738
  - 维护者 2026-11-18 说明：samba-ad play 开始时从 Bao 读秘密
watch:
  - homelab-infra:infrastructure/samba-ad/
  - homelab-infra:infrastructure/chef/policies/samba-dc.rb
  - homelab-infra:infrastructure/dns/records.yml
---

# Samba Active Directory

Samba AD 提供人的目录身份、Kerberos、LDAP、域 DNS 和组策略；
[iam-login](iam-login.md)（`sso.ddupan.top`）在此之上提供 Web 登录（以用户身份 LDAPS bind，
目录查询用只读账号 `svc-iam-login`；Authelia 已于 2026-10-11 退役），[SPIFFE](spire.md) 负责 workload 身份。
AD 组成员资格与每个服务最终授予的权限仍需分别配置。
AD 由 `infrastructure/samba-ad/` 的 Ansible 管理，以代码为准。LAN 主机的 DNS 路径见 [LAN DNS](lan-dns.md)。

## 域与管理入口

| 项目 | 值 |
|---|---|
| DNS domain | `ad.ddupan.top` |
| Kerberos realm | `AD.DDUPAN.TOP` |
| NetBIOS domain | `DDUPAN` |
| 域控 | `dc1.ad.ddupan.top` / `192.168.10.5` |
| 图形管理 | Windows 管理机上的 RSAT：AD Users & Computers、GPMC、DNS |

管理机地址与登录身份由维护者提供。日常 Web 登录从对应应用进入 iam-login，
无需登录域控，也不向普通应用交付 Domain Administrator 凭据。

## 入域之前与入域路径

入域设备需要准确时间、域控连通性和能找到 AD SRV 记录的 DNS 路径。
不要照抄源 README 通用示例中的 `10.10.10.10`、`ad.example.com` 或 `EXAMPLE`。
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

新增用户、组、权限或重置密码会改变目录状态，按现有 Ansible 声明或维护流程实施，
避免 UI 临时改动与下一次配置同步互相覆盖。密码通过受控交互或秘密管理提供，不写进命令示例。
应用权限排障先核对 AD 组（各应用统一授予 `platform-admins` 等组），再核对 iam-login 下发的 `groups` claim 与应用内映射。

## 故障与维护边界

入域失败先区分 DNS/SRV、时间、连通性与账号权限；已有成员认证异常再看信任关系及 winbind。
### Laptop 上的 Winbind RPC 子进程堆积

2026-09-14，`laptop` 的 `winbind.service` 下曾堆积 1677 个 `rpcd_lsad`。现场日志同时显示
SAMR/LSARPC pipe 断连，以及 AppArmor `samba-rpcd` profile 拒绝
`/run/samba/ncalrpc/np/samr` 和 `lsarpc` 的写访问。仅重启 winbind 会暂时释放内存，
但拒绝仍会触发新的 worker，因此不应把重启视为根治。

已在 `/etc/apparmor.d/local/samba-rpcd` 精确允许这两个 pipe 的 `rw` 权限，重载 profile
并重启 winbind。修复后 `wbinfo -t` 及域/BUILTIN 名称查询通过，短期复测没有新增拒绝；
该结论只适用于 laptop 的 Samba member，不应套用到 `dc1`。

复发时先采集 `free -h`、`pgrep -xc rpcd_lsad`、winbind cgroup 内存、内核 AppArmor
拒绝和 Samba 日志，再决定是否重启。不要关闭 AppArmor 或放宽整个目录；出现新路径时
应按审计日志逐项分析。此规则仍应纳入 `samba_member` Ansible role，避免主机重建后丢失。

`ad.ddupan.top` 的静态 RRset 声明在 `infrastructure/samba-ad/ansible/group_vars/all/dns.yml`
（`samba_ad_dns_records`，由 `provision-dc.yml --tags dns` 调和），只管理明确列出的 RRset，
不清理 Samba 自动维护的域控制器 locator、Kerberos 等记录。该列表只减不增：**新服务名称放 `lab.ddupan.top`**，
由创建它的代码登记；`infrastructure/dns/records.yml` 现在只放 split-horizon 名称。
新服务 DNS 接入见[发布新服务](../guides/publish-service.md)。

### dc1 的主机配置与秘密

- dc1 是 Cinc 节点：policy `samba-dc`（`infrastructure/chef/policies/samba-dc.rb`，只含 `homelab_base`），
  2026-11-04 起取代 samba-ad 的 `monitoring-dc.yml`（[1c2b046](https://git.ddupan.top/panxiao81/homelab-infra/commit/1c2b046)）。AD 本身仍由
  `infrastructure/samba-ad/` 的 Ansible 管理。
- 秘密：samba-ad 的 play 在开始时从 Bao 读取秘密（`VAULT_TOKEN`），不使用 ansible-vault；
  只有 `infrastructure/openbao/` 仍用 ansible-vault。

### 备份

`backup-dc.yml`（role `samba_ad_backup`）：`samba-backup.timer` 每天约 03:30 执行
`samba-tool domain backup offline`，本地 `/var/backups/samba/` 留最新 7 份；异地副本 GPG 加密给 YubiKey
（与 pg-prod dump、k3s 备份同一公钥）后上传 OCI 桶 `dc1-backup`，lifecycle 保留 7 天，dc1 只能新建对象
（[PR #738](https://git.ddupan.top/panxiao81/homelab-infra/pulls/738)，2026-11-18 合并）。解密需要 YubiKey，没有密码需保管；[E] 子钥 2027-04-07 到期，
轮换后需更新收件人公钥文件。`SambaBackupStale` 在上次成功超过 36 小时或指标缺失时告警。

第二域控与恢复方案见源码 README；恢复尚未演练过。
域控身份数据库与应用数据不同，不能通过重跑建域、清空数据库来排查普通登录失败。

来源文件的固定版本见[来源追溯](../sources.md#samba-ad)。

## 更新后 DNS 不响应与 Samba 启动失败

2026-09-30 更新后的重启窗口内，Samba 的 IPv6 bind 返回
`NT_STATUS_ADDRESS_NOT_ASSOCIATED`，Samba 整体退出；`Restart=no` 导致故障持续。网络与服务启动竞态是当前最有证据支持的解释。
[事故报告](../incidents/2026-09-30-dc-dns-openbao.md)保存时间线与证据边界。

排查先通过已知管理 IP 检查 `systemctl status samba-ad-dc`、服务 journal、
`ip -6 addr` 与 53 端口监听，区分地址未就绪、配置错误与数据库问题。
在确认地址恢复且没有持续错误、已获恢复授权后，启动 `samba-ad-dc`；
不默认重启 VM、禁用 IPv6 或重建域。

随后分别验证 DC DNS、关键服务的域名 HTTPS（保持 TLS 校验）、ClusterSecretStore、
ExternalSecret 和监控 Agent。下游可能仍在退避；可对明确受影响对象按 ESO 机制触发
`force-sync`，不修改 Secret 副本。采集 up 后还需复核告警清除。

当时仅恢复服务，没有安装自动重试或 DNS 冗余；后续按 [DNS 冗余目标](lan-dns.md)
推进。2026-09-30 的现场验证限于此次恢复，不是整个 AD 目录和登录链路的验收。

### 短期自恢复整改（2026-09-30 已确认，待实现）

维护者要求优先补 Samba 自恢复：当次地址恢复后单次手动启动成功，说明故障存在
通过重试恢复的条件；现有 `Restart=no` 缺少这层保护。
后续由 IaC 管理失败重试、间隔、启动限流与失败告警，并保留人工停止的维护语义。
重试预算须覆盖预期地址就绪窗口，超出预算时的处理必须明确。

验收同时覆盖暂态地址未就绪后自动恢复，以及持续错误时受控重试和告警；
仅验证 unit 配置正确或正常启动成功不够。本项与 DNS 冗余分别推进，
具体依据和关闭条件见[事故报告](../incidents/2026-09-30-dc-dns-openbao.md)。
