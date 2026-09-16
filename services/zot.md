---
title: zot 镜像与制品仓库使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# zot 镜像与制品仓库

zot 保存容器镜像与 OCI 制品，底层数据存放于 [SeaweedFS](seaweedfs.md)。
客户端使用 Registry API，不需要直接访问 S3 bucket。

本页依据 homelab-infra 工作区 `apps/zot/README.md` 的 2026-09-16 记录整理。
源文档记录双入口已上线并验收、由 Flux 管理；本轮未查询现场或执行下面的示例。

## 两个入口

| 入口 | 用途 | 认证 |
|---|---|---|
| `zot.ad.ddupan.top` | 内网拉取镜像或制品 | 匿名只读 |
| `zot-push.ad.ddupan.top` | 鉴权访问及已授权发布 | SPIRE JWT-SVID，audience 为 `zot`；写权限按 SPIFFE ID 和 repository 分配 |

需要到 LAN 的路由与内网 DNS。两个入口对应相同制品数据，例如推送
`zot-push.ad.ddupan.top/team/image:tag` 后，可从
`zot.ad.ddupan.top/team/image:tag` 拉取，无需再复制一份镜像。

## 第一次拉取

安装 crane 后，在可写的工作目录执行源码文档提供的只读示例：

```bash
crane pull zot.ad.ddupan.top/verification/anonymous-spire:smoke image.tar --format oci
```

预期得到本地 `image.tar` OCI archive。该验证制品仅含测试内容，没有可执行入口，
用于验证拉取链路，不要把它当作能运行的业务镜像。
日常部署使用发布方提供的真实镜像路径和 tag/digest；匿名拉取不需要登录推送入口。

## 发布自己的镜像

发布前需要同时具备：

1. 执行环境能通过 Workload API 获取自己的 SPIFFE 身份。
2. workflow 获取 `aud=zot` 的短期 JWT-SVID。
3. zot 已为该 SPIFFE ID 授予目标 repository 所需的 `read/create/update` 权限。

根据所读源文档，当前持久配置没有常驻 publisher 或删除授权，曾用于验收的临时写权限
已经撤回。因此以下是获授权后的使用模板，不能仅登录成功就假定可以推送。

假定 workflow 已将 JWT-SVID 放入当前进程的 `ZOT_JWT`，准备好自己的 `image.tar`，
并将示例目标替换为已授权的 repository/tag，在 Bash 中执行：

```bash
(
  set +x
  set -euo pipefail
  : "${ZOT_JWT:?workflow 必须先取得 aud=zot 的 JWT-SVID}"
  export DOCKER_CONFIG="$(mktemp -d)"
  trap 'rm -rf -- "$DOCKER_CONFIG"' EXIT
  printf '%s' "$ZOT_JWT" | crane auth login zot-push.ad.ddupan.top \
    --username zot --password-stdin
  crane push image.tar zot-push.ad.ddupan.top/team/image:tag
)
unset ZOT_JWT
```

临时配置目录退出时删除。登录、token 获取和刷新由 workflow 负责，
[Dynamic Runner](gitea-dynamic-runner.md) 提供环境和身份能力，不代办这些业务流程。
这里的 token 交换不会延长原 SVID 的有效期。

## 常见问题与数据边界

- 拉取域名不能推送：它只提供匿名读取，发布应使用推送域名。
- 401：检查 issuer、audience、有效期，以及 workflow 是否实际取得了 JWT-SVID。
- 登录成功但推送被拒绝：检查具体 SPIFFE ID 的 repository policy；身份与写权限分开配置。
- S3 后端报错：检查 zot 到 SeaweedFS 的连接与受管凭据，不能用客户端的 JWT 代替后端 AK/SK。

zot 的持久数据在 SeaweedFS `zot` bucket 的 `registry/` 前缀；zot Pod 的临时目录不是备份。
恢复需要完整 bucket 数据、OpenBao 专用凭据与部署配置。源文档记录独立异机/离线备份尚未建立，
不能将同一 SeaweedFS 的副本视为独立灾备；重装 zot 不得删除该 bucket。

部署、授权变更、凭据轮换及验收细节以 homelab-infra `apps/zot/README.md` 为准。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#zot)。
