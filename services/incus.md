---
title: laptop Incus
lifecycle: experimental
evidence: live-verified
last_reviewed: 2026-10-04
last_verified: 2026-10-01
sources:
  - 维护者于 2026-09-25 授权通过 Ansible 安装 Incus，保留 libvirt 与裸机 k8s
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/d45e0b94e80cb8a509df46a14cd7e89d5381b124
  - 2026-09-25 laptop 本地版本、服务、资源清单与 Ansible 幂等验证
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/176
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/31f455d51daf25f6ff04b2b5d7a5f16e280c5145
  - 维护者于 2026-10-01 要求网络与 SSH 改由 cloud-init 声明、镜像不固定指纹，并授权重建两个空容器
  - 2026-10-01 容器重建后的 cloud-init、sshd、SSH 登录、DNS 与 Terraform plan 现场验证
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/194
  - 2026-10-04 state 迁移至 S3 后的 state list 与 plan 现场验证
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/199
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/200
  - 2026-10-04 嵌套 Incus 的 PKI 模式验证、laptop CA 信任开启与 PR #200 CI plan 现场验证
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
- `access.yml` 管理 Incus 配置、独立入口资源和 Authelia client；`dns.yml` 仅协调 `incus`、`ayatori-dev`、`ayatori-prod` 三条 AD A 记录。
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
Incus/Authelia/DNS 来源配置在 `feat/incus-ayatori-base`，经
[PR #176](https://git.ddupan.top/panxiao81/homelab-infra/pulls/176) 提交审阅，截至
[31f455d](https://git.ddupan.top/panxiao81/homelab-infra/commit/31f455d51daf25f6ff04b2b5d7a5f16e280c5145)
尚未合并 main。

## CI 访问（pki-incus 短期证书）

目标是让 CI 用 Terraform 管理整个 Incus（不只 Ayatori），且 Bao 中不存静态管理员证书。
Bao 新增独立根 CA `pki-incus`（[PR #199](https://git.ddupan.top/panxiao81/homelab-infra/pulls/199)，
2026-10-04 已由 CI apply）：私钥不出 Bao，role `ci-terraform` 只签 30 分钟客户端证书且不入存储。
它不挂在内部 CA 下，否则内部 CA 签发的任何证书都会成为 Incus 管理员。

laptop Incus 已由 `access.yml` 下发 `/var/lib/incus/server.ca` 并开启
`core.trust_ca_certificates=true`：该 CA 签发、未过期的客户端证书直接获完整权限，不入信任列表，
过期即失效。这等同 laptop root。服务器证书仍为 Incus 自签，网关校验与 Web UI/OIDC 不受影响。

CI 侧（[PR #200](https://git.ddupan.top/panxiao81/homelab-infra/pulls/200)，**待合并**）：`tf.py`
每次调用现签证书，写入 tmpfs 临时目录，经 `https://192.168.10.127:8443` 访问并以仓库中的
`server.crt` 固定校验服务器；incus 加入 `TF_ROOTS`，合并后 main 即 Incus 的期望状态，手工改动会被回滚。
laptop 本地仍可经 Unix socket 运行。

2026-10-04 验证：嵌套 Incus 7.5.1 中 CA 签发证书 trusted 且可调用 API，自签与过期证书 untrusted，
放置 `server.ca` 后服务器证书不变。laptop 执行 `access.yml` 后重跑 `changed=0`；incusd 重启
（`KillMode=process`）而两容器启动时间不变；服务器证书指纹不变，Web UI 200，认证方式仍为 tls+oidc。
PR #200 的 CI plan 经 HTTPS + 短期证书访问 Incus，结果无变更。

## Ayatori 基础环境

维护者于 2026-09-25 明确本次仅准备两个 LXC，不安装应用或 Kubernetes。
`ayatori-dev` 与 `ayatori-prod` 为 Ubuntu 24.04 非特权容器，各限额 2 CPU、2 GiB RAM、
20 GiB rootfs；存储池 `ayatori` 位于独立 ZFS dataset `data/incus-ayatori`。
网络接入既有 br0，固定 MAC，静态地址 `192.168.10.11`（`ayatori-dev.ad.ddupan.top`）与
`192.168.10.12`（`ayatori-prod.ad.ddupan.top`），位于 NEC IX DHCP 池（`.128–.250`）之外；
地址只在源码 `infrastructure/dns/records.yml` 声明一次，Terraform 与 AD DNS 同源读取。

容器初始化全部由 Terraform 写入的 cloud-init 完成，不再有容器侧 Ansible：
`network-config` 配静态地址、网关 `.1`、resolver `.127`/`.1`；user-data 创建 `panxiao81`
（公钥、免密 sudo）、安装 openssh-server，装包后再写 `sshd_config.d` drop-in 关闭密码与 root 登录。
不使用 `ssh_pwauth`，它会在装包前写出残缺的 `sshd_config`，丢失 `UsePAM yes`。
镜像跟随 `images:ubuntu/24.04/cloud` 最新构建，只在创建时使用；不固定指纹，因为上游会下架旧构建。

⚠ 镜像模板只在创建/复制时渲染 cloud-init seed。修改已有实例的 cloud-init 配置不会生效，
重启或 `cloud-init clean` 都不行；改地址或初始化内容须重建实例。

首次使用：`incus exec local:ayatori-dev -- bash`，或 `ssh panxiao81@ayatori-dev.ad.ddupan.top`。

Terraform 经本机 Unix socket 管理；state 于 2026-10-04 迁至 S3 `tfstate` bucket 的
`incus/terraform.tfstate`（原生 lockfile，[PR #194](https://git.ddupan.top/panxiao81/homelab-infra/pulls/194)），
经 `infrastructure/incus/run.py` 从 Bao 取受限身份运行。迁移后 S3 上 plan 无变更；laptop 原本地
state 改名为 `*.pre-s3-20261004` 留作回退。CI 接管见下节。
容器离机备份仍待补齐。源码提交见上文；资源与用户初始化细节见源码 README。

2026-09-25 验证：两个容器均 RUNNING，cloud-init 完成；DHCP 分别取得
`192.168.10.131`（dev）、`192.168.10.132`（prod）。实际公钥 SSH 和 sudo 成功，
DNS 解析与包下载可用，非特权 UID 映射、2 GiB cgroup 限额及 20 GiB rootfs 已核对。
Terraform plan 无变更，SSH Ansible 重跑 `changed=0`；宿主 k3s/libvirtd/Incus 仍 active。

2026-10-01 重建：按维护者授权以 `-replace` 重建两个空容器（先后两次，分别落地网络与 SSH 声明）。
重建前用临时容器核实 seed 只在 create/copy 渲染，并验证 cloud-init SSH 方案。重建后两容器
cloud-init 无错误，地址为 `.11`/`.12`，网关与 resolver 符合声明；`sshd -T` 为 `usepam yes`、
`passwordauthentication no`、`permitrootlogin no`；公钥 SSH 与 `sudo -n` 成功，密码与 root 登录被拒。
AD DNS 两条 A 记录经 DC 与 Blocky 解析正确，`dns.yml` 重跑 `changed=0`；Terraform plan 无变更。
上述 2026-09-25 的 DHCP 地址已废弃。
