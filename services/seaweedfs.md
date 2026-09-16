---
title: SeaweedFS S3 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# SeaweedFS 对象存储

SeaweedFS 为应用提供 S3 兼容对象存储，zot Registry 是它的消费者之一。
普通应用使用自己的 bucket 和 S3 身份；容器镜像通过 [zot](zot.md) 发布与拉取。

本页依据 homelab-infra 工作区 `apps/seaweedfs/README.md` 和 `apps/zot/README.md` 整理，
客户端语法参考 AWS CLI 官方文档。本轮未查询现场或读写对象。

## 连接入口与身份

| 场景 | endpoint |
|---|---|
| LAN 客户端的 HTTPS S3 入口 | `https://s3.ad.ddupan.top` |
| Kubernetes 集群内 Service | `http://seaweedfs-s3.seaweedfs.svc.cluster.local:8333` |

首次接入先明确自己的 bucket、需要的 Read/Write/List 等权限及凭据获取方式。
当前所读配置使用静态 S3 AK/SK，由 OpenBao 管理；SeaweedFS OIDC/STS 尚未接入。
zot 前端的 SPIFFE 登录不代表通用 S3 客户端已经能用 SPIFFE 换取 S3 凭据。

应用使用专属身份，不复用 zot 或 Terraform 的存储凭据。
Kubernetes Secret 是 ESO 生成的消费副本，身份或凭据变更应修改受管来源，不能手工改副本。

## 用 AWS CLI 查看自己的对象

前提：已安装 AWS CLI，并由既有授权流程将本应用的凭据注入当前进程环境
（`AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY`），或配置受保护的专用 CLI profile。
不要把实际 AK/SK 复制到命令示例、仓库或日志中。

将下例 bucket 替换为自己的已授权 bucket，先只读列出少量对象：

```bash
aws --endpoint-url https://s3.ad.ddupan.top s3api list-objects-v2 \
  --bucket YOUR_APP_BUCKET --max-items 10 --no-cli-pager
```

预期返回对象信息或空 bucket 的结果。只具有指定 bucket 权限的身份，不必拥有列举所有 bucket 的权限；
因此不以全局 `aws s3 ls` 是否成功作为接入的唯一标准。
`--max-items` 控制返回条数，具体行为见
[AWS CLI list-objects-v2](https://docs.aws.amazon.com/cli/latest/reference/s3api/list-objects-v2.html)。

## 上传和下载一个测试文件

仅在自己的测试 bucket/prefix 以及具备写权限时操作。替换占位符，并使用尚未占用的 key：

```bash
aws --endpoint-url https://s3.ad.ddupan.top s3 cp ./hello.txt \
  s3://YOUR_APP_BUCKET/YOUR_UNUSED_TEST_KEY
aws --endpoint-url https://s3.ad.ddupan.top s3 cp \
  s3://YOUR_APP_BUCKET/YOUR_UNUSED_TEST_KEY ./hello.downloaded.txt
cmp ./hello.txt ./hello.downloaded.txt
```

本地先准备 `hello.txt`。预期上传与下载成功，`cmp` 无输出且退出码为 0。
这会在目标 bucket 留下测试对象，是否清理由该 bucket 的所有者决定。
语法参考 [AWS CLI cp](https://docs.aws.amazon.com/cli/latest/reference/s3/cp.html)。
上游 S3 客户端文档用于解释命令，不代表 SeaweedFS 实现了全部 AWS S3 功能。

## zot 数据与维护边界

zot 专用数据位于 `zot` bucket 的 `registry/` 前缀，由 Registry 管理 OCI layout。
不要把普通文件直接写入该前缀，也不要用 S3 客户端手工删除镜像内部对象。

zot 的 S3 身份只允许相应 bucket 的 Read/Write/List/Tagging，不能访问 `tfstate`。
其凭据唯一来源为 OpenBao `kv/k8s/zot-s3`，由 ESO 同步给 zot 和 SeaweedFS；
基础 S3 身份配置在 `kv/k8s/seaweedfs-s3`，两份配置的合成及轮换见源码 README。
轮换不仅是改一个值，还需协调服务端重新加载和消费者更新，避免两端配置不一致。

## 遇到问题先看哪里

- 域名或连接失败：确认当前使用的是 LAN endpoint 还是仅集群内可达的 Service。
- 访问被拒绝：核对使用的应用身份、bucket/key 与所需动作权限，不直接扩大为管理员权限。
- 签名或凭据错误：核对凭据来源、同步情况和客户端配置；不要打印 AK/SK 排障。
- Registry 不可用：区分 zot 的 SPIFFE 客户端认证与它到 S3 的后端认证。

部署与配置来源：homelab-infra `apps/seaweedfs/README.md`、`apps/zot/README.md`。
单一存储系统内的数据副本不等于独立备份；zot 源文档尚未记录已建立独立异机/离线备份。
其他应用的数据保留与恢复策略应由各自用途明确，不能从“已接入 S3”推断已经完成备份。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#seaweedfs)。
