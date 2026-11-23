---
title: Gitea 与 Actions 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-11-23
last_verified: null
sources:
  - homelab-infra docs/gitea-oci-migration-plan.md
  - homelab-infra infrastructure/oci/ansible/roles/gitea/
  - homelab-infra apps/gitea-backup-drive/README.md
  - homelab-infra infrastructure/oci/README.md
  - homelab-infra platform/dynamic-runner/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/82322df5b6124c7278b289cc2c53771e0135dd17
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/368303573a0a74365e7d961451662d5e21161c68
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/bb24c76704a018df967bfe007539fde9c9b2a46e
watch:
  - homelab-infra:docs/gitea-oci-migration-plan.md
  - homelab-infra:infrastructure/oci/ansible/roles/gitea/
  - homelab-infra:infrastructure/oci/README.md
  - homelab-infra:apps/gitea-backup-drive/
  - homelab-infra:platform/dynamic-runner/README.md
  - homelab-infra:infrastructure/gcp-ci/terraform/
---

# Gitea 与 Actions

Gitea 托管 homelab 的代码、文档、issue 和 PR；Actions 执行仓库声明的 CI workflow。
入口为 <https://git.ddupan.top>，人类登录使用 Gitea 登录源 `sso`（即 [iam-login](iam-login.md)，
`sso.ddupan.top`）；[Authelia](authelia.md) 与 [Hydra](hydra.md) 均已退役。

**2026-11-05 起 Gitea 运行在 OCI A1（`oci_arm`，大阪）**，不再在 laptop 的 k3s 上：Docker Compose +
SQLite，由 homelab-infra `infrastructure/oci/ansible/` 的 role `gitea` 管理
（迁移方案与执行记录见 `docs/gitea-oci-migration-plan.md`）。公网入口是 A1 公网 IP 443，
`git.ddupan.top` 走 Cloudflare 代理（不经 lab 的 tunnel），lab 内也经公网名访问，已取消 split-horizon。
k3s 上的旧部署 `apps/gitea` 已于 2026-11-11 删除
（[3683035](https://git.ddupan.top/panxiao81/homelab-infra/commit/368303573a0a74365e7d961451662d5e21161c68)，
[PR #698](https://git.ddupan.top/panxiao81/homelab-infra/pulls/698)）。

## 登录并找到项目

1. 打开 Gitea，选择 `sso` 登录入口（<https://git.ddupan.top/user/oauth2/sso>）。
2. 在 iam-login 完成 AD 密码与 Passkey，返回 Gitea；应用权限由 Gitea 账号和仓库授权决定。
3. 打开目标仓库：Code 看源码，Issues 看动态工作，Pull Requests 看待合并改动，Actions 看 CI。

登录成功但看不到仓库时，先确认当前账号与仓库权限；OIDC 登录本身不会赋予所有项目的管理权。
已有账号应沿用原账号关联，遇到关联问题交由管理员处理，不另建同名账号规避。

iam-login 依赖 lab 里的 dc1，lab 不可用时无法经 `sso` 登录。迁移方案为此另加 Entra ID 登录源
（role 变量 `gitea_entra_source_name: entra`，2026-11-05 [c041bc8](https://git.ddupan.top/panxiao81/homelab-infra/commit/c041bc8) 启用），
只有在 Entra 应用中被分配的用户能登录；方案文档记录其登录验收尚未完成。最后兜底是 ssh 到 A1 用 `gitea admin` CLI。

## 历史：Hydra 与 Authelia 登录源

2026-09-25 曾新增 [Hydra 人类登录 PoC](hydra.md) 登录源，与旧 `authelia` 登录源并存。
2026-10-04 该源（ID 3）改名为 `sso` 并改指 iam-login，Hydra 于 2026-10-05 下线
（[82322df](https://git.ddupan.top/panxiao81/homelab-infra/commit/82322df5b6124c7278b289cc2c53771e0135dd17)）；
`authelia` 登录源随 Authelia 于 2026-10-11 删除
（[b3b4d8f](https://git.ddupan.top/panxiao81/homelab-infra/commit/b3b4d8fd1cb879e2e0b640e52b86c219268e0620)）。
登录源按**名称**匹配，改名会新建源并断开账号关联，需用 `gitea admin auth update-oauth` 原地修改。

## 创建与修改仓库

通过页面的 New Repository 创建仓库，选择所属用户或组织、名称及可见性。
仓库里的 Clone 按钮提供当前准确的 HTTPS/SSH 地址，复制该地址到 Git 客户端即可。
浏览器的 OIDC 会话不直接充当 Git 命令行凭据；客户端使用自己的凭据管理或已登记 SSH key。

日常修改先建分支、提交并推送，再开 PR 合并到 main。PR 应说明最终行为与验证结果，
不要把本机未提交的其他工作一并带入。基础设施仓库默认以中文维护 commit、PR 和文档。

## 第一个 CI workflow

在可信的测试仓库中启用 Repository Actions，再添加 `.gitea/workflows/hello.yaml`：

```yaml
name: Hello
on: [push]
jobs:
  hello:
    runs-on: [self-hosted]
    steps:
      - name: Check execution
        run: echo 'homelab CI is running'
```

推送该文件后，进入 Actions，打开本次运行和 hello job。
预期看到输出 `homelab CI is running` 且 job 成功；示例不需要检出源码或读取秘密。
若仓库设置没有 Actions 开关，先确认自己的管理权限。
workflow 路径、启用方式与事件规则见 [Gitea 官方入门](https://docs.gitea.com/usage/actions/quickstart/)。

`[self-hosted]` 是动态 Pod 池的 label（旧常驻 runner 已删除）。
若任务排队，除 runner 在线状态和 labels 外，也要考虑系统并发容量，不能把入队当作执行成功。

## 选择 runner

每个池只声明一个 label，`runs-on` 也只写这一个：

| `runs-on` | 执行环境 |
|---|---|
| `[self-hosted]` | 动态 Pod，池成员 `pod-sandbox`（sandbox 集群）；迁移期间另带别名 `pod` |
| `[self-hosted-large]` | 动态 Pod，池成员 `pod-laptop`（laptop k3s，`POD_CAPACITY=4`） |
| `[self-hosted-vm]` | OpenSandbox/Kata VM（`VM_CAPACITY=1`） |
| `[cloud]` / `[cloud-small]` | GKE Autopilot 一次性 Pod（`infrastructure/gcp-ci/terraform`）；默认 2 vCPU / 4 GiB，`cloud-small` 为 0.5 vCPU / 1 GiB |

容量是池的总容量，不按仓库分配。实现与后续变化见 [Dynamic Runner](gitea-dynamic-runner.md) 及其项目文档。
旧 `[self-hosted, pod]`、`[self-hosted, vm]` 写法属于迁移前接口；`pod` 别名只在迁移期间保留。

旧常驻 runner `platform/gitea-runner` 已于 2026-09-21 删除
（[bb24c76](https://git.ddupan.top/panxiao81/homelab-infra/commit/bb24c76704a018df967bfe007539fde9c9b2a46e)）。
动态 runner 提供环境及获取自身 SPIFFE 身份的能力；登录下游、请求 token 和凭据清理由 workflow 负责。

## 遇到问题先看哪里

- 没有触发：看 Actions 是否启用、文件是否位于正确路径、事件是否匹配此次推送。
- 一直排队：看仓库可用 runner、在线状态和 labels；动态 runner 的问题回到其项目文档。
- job 失败：打开具体 step 的日志，从第一个失败步骤排查，不只看最终退出码。
- Git 命令失败但网页能登录：分别检查 Git 使用的身份、凭据方式和仓库权限。

## 运维入口

- 部署：homelab-infra `infrastructure/oci/ansible/` 的 role `gitea`（`/srv/gitea`，Compose，rootless 镜像，
  SQLite WAL）。秘密在 OCI Vault（迁移方案说明不从 Bao 读，恢复根不能依赖 lab）。升级为 Renovate 改 tag →
  合并 → 手工运行 playbook，不交给 CI（runner 在 lab，又要连接正在重启的 Gitea）。
- 登录源存在 Gitea 数据库，不在 `app.ini`；role 只在缺失时添加，改名或改参数需手工 `gitea admin auth update-oauth`。
- 备份：A1 每天 `gitea dump`，以 instance principal 上传到 OCI 桶 `gitea-backup`（保留 2 天）；
  `apps/gitea-backup-drive` 的 CronJob 每 6 小时用 rclone crypt 加密拷到 Google Drive `homelab-backup/gitea/`（保留 30 天），
  Drive 上没有 2 天内的 dump 时拒绝清理并报 `GiteaBackupDriveStale`。
- 异地副本：服务端推送镜像到 GitHub 组织 `ddupan` 的私有仓库（`infrastructure/oci/README.md`，PAT 存 Bao
  `kv/infra/gitea-github-mirror`，最长 366 天需轮换）；镜像强推，不要在 GitHub 上提交。
- 旧 k3s 部署 `apps/gitea/README.md` 已删除，只能在 3683035 之前的版本查阅。

本页不复制 token、密码或部署命令。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#gitea)。
