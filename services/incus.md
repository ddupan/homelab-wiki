---
title: laptop Incus
lifecycle: experimental
evidence: live-verified
last_reviewed: 2026-10-01
last_verified: 2026-09-25
sources:
  - 维护者于 2026-09-25 授权通过 Ansible 安装 Incus，保留 libvirt 与裸机 k8s
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/d45e0b94e80cb8a509df46a14cd7e89d5381b124
  - 2026-09-25 laptop 本地版本、服务、资源清单与 Ansible 幂等验证
---

# laptop Incus

用于后续 Linux 系统容器和新 Linux VM 的管理，已安装并开放 Web UI/Authelia OIDC，已准备 Ayatori 开发、生产基础容器，应用尚未部署。
既有 VM 留在 libvirt，k8s 留在裸机；不引入 Incus SDN/LB。
etcd 和共享 PostgreSQL 由各自服务管理，本次不迁移。

## 入口与第一次使用

Web 入口：<https://incus.ad.ddupan.top>，选择 **Login with SSO**，由 Authelia 登录。
仅允许 `panxiao81`，要求 MFA；该用户获得 Incus 完整管理权限，不绑定现有组。
后续统一迁移新 IdM，当前不建立永久组模型。

在 laptop 上通过本地 Unix socket 使用，需要 sudo 权限；也是网页登录不可用时的恢复入口：

```bash
sudo incus version
sudo incus list local:
sudo incus storage list local:
sudo incus network list local:
```

Ayatori 基础容器由源码 `infrastructure/incus/terraform/` 管理；网络连接既有非受管 `br0`。
HTTPS listener 为 `192.168.10.127:8443`；域名通过共享 Envoy 转发，后端证书显式验证。
没有新增宿主管理员组成员。

## 管理与恢复边界

- 软件源、公钥、固定包版本与本地服务由 `infrastructure/incus/ansible/site.yml` 管理。
- 使用 Zabbly stable APT 包，版本为 `1:7.5.1-ubuntu24.04-202609250207`；不使用 snap。
- 旧源文件按维护者要求删除后由 Ansible 重建。APT preferences 固定版本，升级需改 IaC。
- 安装 playbook 不执行 `incus admin init`；Terraform 单独管理 Ayatori 存储池和两个实例，不接管 libvirt、k3s、br0、路由或防火墙。
- 历史 `data/incus`（含 GNS3 与快照）已按维护者明确要求删除，不能恢复为旧服务；安装 playbook 不包含删除逻辑。
- 当前依赖宿主 Ubuntu 24.04 amd64、systemd、APT 与 Zabbly 源。未来虚拟机还依赖可用 KVM。
- Web/OIDC 另依赖 k3s、Envoy、Authelia；这些入口不可用时本地 `sudo incus` 仍可管理。
- `access.yml` 管理 Incus 配置、独立入口资源和 Authelia client；`dns.yml` 仅协调 Incus DNS。
- Authelia 更新基于 live Helm values 合并单个 client/policy，保留其他客户端；不要直接用滞后的本地 values 全量覆盖。
- 共享 Envoy 后端 TLS 允许 1.2–1.3，由 Flux 管理；不升级网关，不修改前端证书或其他路由。
- 重建安装使用源码 README 中的 Ansible 命令。实例和数据备份恢复尚未建立，需在承载持久数据前补齐。

## 故障入口

```bash
systemctl status incus.service incus.socket
sudo journalctl -u incus.service -n 80 --no-pager
apt-cache policy incus incus-base incus-client
```

版本解析失败时先核对源和索引；上游 stable 不保证永久保留旧构建，
不能把固定版本变量等同于离线重建保障。不要通过重置数据库或销毁 ZFS 来处理安装故障。

## 验证范围

2026-09-25：通过 Ansible 安装，客户端和服务端版本为 7.5.1；本地 API 可访问，
安装时无实例、无存储池、无受管网络。安装后重跑 `changed=0`，check/diff 无变更。
libvirtd、k3s 仍 active；既有 dc1、winadmin、bao1 VM 仍运行，libvirtd.conf 校验和未变，
宿主 bridge 名称集合未变。该安装阶段未验证实例，后续 LXC 验收见下节。

安装、接入与 DNS playbook 最终重跑均 `changed=0`。HTTPRoute 的 Accepted/ResolvedRefs
与 BackendTLSPolicy 的 Accepted 均为 True；Authelia/Gitea 首页仍返回 200。
入口验证：HTTPS UI 返回 200，匿名实例 API 返回 403；浏览器 SSO 正常跳转 Authelia，
PKCE S256、callback、audience 和设备授权发起已验证。维护者同日确认 `panxiao81` 完成 MFA 并返回 Incus 控制台。
未验证 Web 实例控制台或 Ayatori 应用数据路径。

共享网关补丁已通过 [PR #164](https://git.ddupan.top/panxiao81/homelab-infra/pulls/164)
合并并由 Flux 发布，revision `f5c8c09f961da3de5ca63c5775a9c50825c94752` Ready。
Incus/Authelia/DNS 来源配置已推送至 `feat/incus-ayatori-base`，
固定源码为 [d45e0b9](https://git.ddupan.top/panxiao81/homelab-infra/commit/d45e0b94e80cb8a509df46a14cd7e89d5381b124)，尚未合并 main；
本页随此次文档提交同步。

## Ayatori 基础环境

维护者于 2026-09-25 明确本次仅准备两个 LXC，不安装应用或 Kubernetes。
`ayatori-dev` 与 `ayatori-prod` 为 Ubuntu 24.04 非特权容器，各限额 2 CPU、2 GiB RAM、
20 GiB rootfs；存储池 `ayatori` 位于独立 ZFS dataset `data/incus-ayatori`。
网络使用既有 br0/DHCP 和固定 MAC；当前地址通过 `terraform output containers` 查询，
不作为已保留的固定地址。首次使用：`incus exec local:ayatori-dev -- bash`，或使用
`panxiao81` 公钥 SSH 登录；没有配置密码登录。

Terraform 经本机 Unix socket 管理，state 暂存源码 `terraform/terraform.tfstate`（Git 忽略）。
2026-09-25 部署时远端 state 凭据不可读，迁移远端 backend 与离机备份待后续完成。不得丢弃 state 后
直接重新 apply。源码提交见上文；资源与用户初始化细节见源码 README。

2026-09-25 验证：两个容器均 RUNNING，cloud-init 完成；DHCP 分别取得
`192.168.10.131`（dev）、`192.168.10.132`（prod）。实际公钥 SSH 和 sudo 成功，
DNS 解析与包下载可用，非特权 UID 映射、2 GiB cgroup 限额及 20 GiB rootfs 已核对。
Terraform plan 无变更，SSH Ansible 重跑 `changed=0`；宿主 k3s/libvirtd/Incus 仍 active。
