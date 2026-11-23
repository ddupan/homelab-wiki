---
title: Artifact Keeper（CI 下载缓存）
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/artifact-keeper/values.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/artifact-keeper/repositories.sh
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/clusters/ayatori-prod/artifact-keeper.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/CLAUDE.md
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/a99bd81f1816fd253ce1d3dececffcf9f136aede
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/735cdcb061288d07a2e590a3224a33521d8f3aeb
  - 维护者 2026-11-18 说明（与 Nexus 的分工）
watch:
  - homelab-infra:apps/artifact-keeper/
  - homelab-infra:clusters/ayatori-prod/artifact-keeper.yaml
  - homelab-infra:CLAUDE.md
---

# Artifact Keeper（CI 下载缓存）

## 它解决什么问题

Artifact Keeper 是 CI 依赖下载的 pull-through 缓存：CI 拉 PyPI、npm、Go 模块、Ansible Galaxy、
Terraform provider 等时经它取，减少对不稳定 WAN 的依赖。只用作 remote（代理）仓库，不作为发布仓库。
它是 CI 的主要下载缓存：多数 CI 依赖流量已改走这里，少数尚未迁移的消费者仍在用
[Nexus](nexus.md)（维护者 2026-11-18 说明）。

## 从哪里使用

- 入口：`https://artifacts.lab.ddupan.top`（LAN 入口 `eg` 的 `https-lab` listener）。
- 匿名拉取：remote 仓库以 `visibility: public` 创建（`repositories.sh`）。
- 网页登录：iam-login OIDC（`sso.ddupan.top`），`platform-admins` 为管理员组；本地 admin 只作 break-glass。
- 管理 API token：Bao `kv/infra/artifact-keeper` 的 `api_token`。

已建的 remote 仓库（`repositories.sh`）：

| key | 上游 |
|---|---|
| `pypi-proxy` | pypi.org |
| `npm-proxy` | registry.npmjs.org |
| `go-proxy` | proxy.golang.org |
| `galaxy-proxy` | galaxy.ansible.com |
| `terraform-proxy` | registry.terraform.io（Provider Network Mirror） |
| `maven-central`、`gradle-plugins` | Maven Central、Gradle 插件门户 |
| `docker-hub` | Docker Hub（带账号，避免共享出口 IP 被限流） |
| `github-releases` | github.com release 附件 |

## 第一次使用

Gitea Actions workflow 里加 `ci-actions/setup-artifact-keeper` 步骤，它把 pip/uv、npm、Go、Galaxy、
Terraform 指向缓存（repo `CLAUDE.md` Tooling 节）。lockfile 里保留公共 registry 地址是标准写法：
npm 按 `.npmrc` 的 `registry=` 改写，uv 用 `UV_DEFAULT_INDEX`。

## 日常操作与限制

- 缓存淘汰：30 天未下载的条目删除（`remote-cache-idle` 策略）；上游已删除的旧版本随之丢失。
- 新建仓库只能跑 `repositories.sh`（已存在即跳过）；改已有仓库的 upstream 等属性在 UI 中做。
- 没有搜索索引、漏洞扫描（chart 自带的 OpenSearch/Trivy/DependencyTrack 全部关闭）。
- 连接池上限 10，避免直连挤占 pg-prod 的连接。

## 出问题时

- 启动即退出：常见是 OIDC 校验失败，确认 `AK_SSRF_ALLOW_PRIVATE_CIDRS` 仍放行 `sso.ddupan.top` 的 LAN 地址。
- 浏览器弹 Basic 认证框：OIDC 回调路径写错，正确的是 `/api/v1/auth/sso/oidc/callback`。

## 运维入口

- 源码：[apps/artifact-keeper/](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/apps/artifact-keeper)，
  Flux HelmRelease，镜像 1.11.0。
- 依赖：元数据在 [pg-prod](shared-postgresql.md)（Ayatori tenant，`clusters/ayatori-prod/artifact-keeper.yaml`），
  制品在 [SeaweedFS](seaweedfs.md) bucket `artifact-keeper`；登录依赖 [iam-login](iam-login.md)。
- 秘密：S3 key、OIDC client、初始管理员密码经 [ESO](external-secrets.md) 投射；JWT secret 由 ESO Password 生成器生成。
- 备份恢复：未单独建立；内容是可从上游重新拉取的缓存。

## 当前状态与证据

- 2026-10-16 部署（[a99bd81](https://git.ddupan.top/panxiao81/homelab-infra/commit/a99bd81f1816fd253ce1d3dececffcf9f136aede)）
  并接入 iam-login（[735cdcb](https://git.ddupan.top/panxiao81/homelab-infra/commit/735cdcb061288d07a2e590a3224a33521d8f3aeb)）；
  之后陆续加入 npm、Terraform、Docker Hub、GitHub release 仓库（截至 2026-11-09）。
- 维护者 2026-11-18 说明：多数 CI 依赖流量已走 artifact-keeper，剩余少数消费者仍用 Nexus。
