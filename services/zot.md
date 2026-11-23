---
title: zot 镜像与制品仓库使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-11-23
last_verified: 2026-09-25
sources:
  - homelab-infra `apps/zot/README.md`
watch:
  - homelab-infra:apps/zot/
---

# zot 镜像与制品仓库

zot 保存容器镜像与 OCI 制品，底层数据存放于 [SeaweedFS](seaweedfs.md)。
客户端使用 Registry API，不需要直接访问 S3 bucket。
zot 由 Flux 管理。

## 两个入口

| 入口 | 用途 | 认证 |
|---|---|---|
| `zot.lab.ddupan.top` | 内网拉取镜像或制品；浏览器 UI | 匿名只读；UI 用 iam-login 登录 |
| `zot-push.lab.ddupan.top` | 鉴权访问及已授权发布 | SPIRE JWT-SVID，issuer 为 `https://spire-oidc.ddupan.top`，audience 为 `zot`；写权限按 SPIFFE ID 和 repository 分配 |

旧名 `zot.ad.ddupan.top`、`zot-push.ad.ddupan.top` 仍由同一 HTTPRoute 服务，引用中的镜像内容与 digest 不变；
各发布方在自己的下一次发版时改用 lab 名，全部改完后才会移除 ad 名。
新配置一律用 lab 名。两个域名现在指向同一个 `zot` 实例（原 `zot-reader` 已不挂路由），匿名拉取经
`oci-token-server` 签发只读 token。

需要到 LAN 的路由与内网 DNS。例如推送 `zot-push.lab.ddupan.top/team/image:tag` 后，可从
`zot.lab.ddupan.top/team/image:tag` 拉取，无需再复制一份镜像。

`https://zot.lab.ddupan.top/` 是 zot 自带 UI，经 [iam-login](iam-login.md) 登录；`platform-admins` 组为
`adminPolicy`，其他已登录用户按各仓库 `defaultPolicy` 只读。zot 重启后需要重新登录。

## 第一次拉取

安装 crane 后，在可写的工作目录执行只读示例：

```bash
crane pull zot.lab.ddupan.top/verification/anonymous-spire:smoke image.tar --format oci
```

预期得到本地 `image.tar` OCI archive。该验证制品仅含测试内容，没有可执行入口，
用于验证拉取链路，不要把它当作能运行的业务镜像。
日常部署使用发布方提供的真实镜像路径和 tag/digest；匿名拉取不需要登录推送入口。

## 发布自己的镜像

发布前需要同时具备：

1. 执行环境能通过 Workload API 获取自己的 SPIFFE 身份。
2. workflow 获取 `aud=zot` 的短期 JWT-SVID。
3. zot 已为该 SPIFFE ID 授予目标 repository 所需的 `read/create/update` 权限。

2026-09-25 起，配置已为 Dynamic Runner 的 CI 发布身份和本地开发身份开放两个
`panxiao81/gitea-dynamic-runner-*` 镜像仓库的 `read/create/update`。
两类身份使用独立 policy：CI 保持 `read/create/update`，本地开发身份另外具有
`delete`。精确规则会覆盖通配规则，不能根据 `**` 推断某仓库权限；
本地维护权限修正已随 [PR #144](https://git.ddupan.top/panxiao81/homelab-infra/pulls/144) 上线。
其他仓库仍按各自授权判断。
下面是获授权后的使用模板，不能仅登录成功就假定可以推送。

假定 workflow 已将 JWT-SVID 放入当前进程的 `ZOT_JWT`，准备好自己的 `image.tar`，
并将示例目标替换为已授权的 repository/tag，在 Bash 中执行：

```bash
(
  set +x
  set -euo pipefail
  : "${ZOT_JWT:?workflow 必须先取得 aud=zot 的 JWT-SVID}"
  export DOCKER_CONFIG="$(mktemp -d)"
  trap 'rm -rf -- "$DOCKER_CONFIG"' EXIT
  printf '%s' "$ZOT_JWT" | crane auth login zot-push.lab.ddupan.top \
    --username zot --password-stdin
  crane push image.tar zot-push.lab.ddupan.top/team/image:tag
)
unset ZOT_JWT
```

临时配置目录退出时删除。登录、token 获取和刷新由 workflow 负责，
[Dynamic Runner](gitea-dynamic-runner.md) 提供环境和身份能力，不代办这些业务流程。
这里的 token 交换不会延长原 SVID 的有效期。

## 常见问题与数据边界

- 拉取域名不能推送：它只提供匿名读取，发布应使用推送域名。
- 401：检查 issuer（`https://spire-oidc.ddupan.top`）、audience、有效期，以及 workflow 是否实际取得了 JWT-SVID。
- 登录成功但推送被拒绝：检查具体 SPIFFE ID 的 repository policy；身份与写权限分开配置。
- S3 后端报错：检查 zot 到 SeaweedFS 的连接与受管凭据，不能用客户端的 JWT 代替后端 AK/SK。

zot 的持久数据在 SeaweedFS `zot` bucket 的 `registry/` 前缀；zot Pod 的临时目录不是备份。
恢复需要完整 bucket 数据、OpenBao 专用凭据与部署配置。独立异机/离线备份尚未建立，
不能将同一 SeaweedFS 的副本视为独立灾备；重装 zot 不得删除该 bucket。

部署、授权变更、凭据轮换及验收细节以 homelab-infra `apps/zot/README.md` 为准。

来源文件的固定版本见[来源追溯](../sources.md#zot)。

## GC 与 SHA tag 清理

2026-09-25 现场 ConfigMap 与源码配置一致：写入实例 `gc=true`，
`gcInterval=24h`、`gcDelay=24h`；reader 的 `gc=false`，不对共享存储重复清理（当时还是双实例）。
retention policy 只针对 `panxiao81/backstage`：仅保留 `latest`，历史 sha tag 与失去 tag 的 digest
在 24h 后回收；其余仓库由 `**` 兜底策略保留全部 tag，不会因版本较旧自动删除。新增按仓库的清理规则须放在兜底策略之前。
2026-09-25 只核验了 GC 配置，没有核验一轮 GC 完成或 SeaweedFS 物理空间回收。

2026-09-25 那次清理的边界（维护者给出）：保留最近两天及 infra 仓库引用的版本；额外保护
当前工作负载、历史 ReplicaSet 和 `latest`、`main`、版本 tag 指向的 digest。
不同 tag 可以引用同一 manifest，移除别名不意味着释放底层镜像层空间。
删除前应再次核对 tag → digest、OCI index 子 manifest 与引用，避免并发发布改变目标。
镜像 config 的 `created` 是构建时间，不是推送时间，不能单独证明最近两天没有推送。
当时结合覆盖 48 小时的 Pod 轮转日志中成功 manifest PUT 与 S3 manifest 的
`LastModified` 排除近期推送；读取存储元数据不代替通过 Registry API 删除。

当时匿名和鉴权 `_catalog` 都返回空列表，但已知 repository 的 `tags/list` 与
manifest 可读取，不能以 catalog 为空断言仓库无镜像或清理已覆盖全部仓库。
只通过 registry API 清理已确认的 tag，不直接删除 S3 对象。

权限修正已合并为 [`185a47e`](https://git.ddupan.top/panxiao81/homelab-infra/commit/185a47e2bb4877c5d4274633e366cad0e83cb2a0)，
Flux zot Kustomization 已应用该 revision，两个 HelmRelease Ready。
2026-09-25 清理后保留 tag、infra/运行/回滚引用的 19 个根 digest、57 个 manifest、
161 个 blob 读取检查通过。这里只确认清理与读取，不宣称 S3 或 SeaweedFS 物理空间已回收。
除 backstage 外没有自动 tag retention；其他仓库定期清理仍需动态核对 infra 与运行引用，
不能仅使用固定年龄规则。

参考：[zot v2.1.21 retention](https://zotregistry.dev/v2.1.21/articles/retention/)。
