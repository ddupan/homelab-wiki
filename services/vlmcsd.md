---
title: vlmcsd 服务入口
lifecycle: unknown
evidence: configuration
last_reviewed: 2026-09-16
last_verified: null
---

# vlmcsd

homelab 中的 KMS 兼容服务，配置使用 `mikolatero/vlmcsd` 镜像。
维护者于 2026-09-16 表示没有需补充的动态事项；本页依据
`apps/vlmcsd/compose.yaml` 整理，未检查运行状态或客户端。

## 入口与客户端使用

Compose 将宿主 TCP `1688` 映射到容器 `1688`。实际宿主地址和客户端使用范围未在该文件中记录，
接入时由维护者提供；它是协议服务，不是网页，也没有仓库中已记录的 OIDC 登录步骤。

已有 Windows KMS 客户端需要指定服务器时，在管理员终端中将 `YOUR_KMS_HOST` 替换为已提供的地址：

```powershell
cscript.exe "$env:SystemRoot\System32\slmgr.vbs" /skms YOUR_KMS_HOST:1688
cscript.exe "$env:SystemRoot\System32\slmgr.vbs" /ato
cscript.exe "$env:SystemRoot\System32\slmgr.vbs" /dlv
```

第一步修改该客户端的 KMS 目标，第二步发起激活请求，第三步查看结果；
适用前提是客户端版本与其已有授权配置支持 KMS，不能将端口连通当成激活成功。
命令依据[镜像项目使用说明](https://github.com/mikolatero/docker-vlmcsd)，本轮未执行。
已有客户端无需为了接入此服务先卸载产品密钥；本页不复制那类重置步骤。

## 故障与依赖

连接失败先核对宿主地址、TCP `1688` 与网络规则；服务可达但请求失败时，
结合客户端详细状态和服务日志区分协议、版本及客户端配置问题。
具体客户端清单、DNS 自动发现记录和宿主位置未从所读 Compose 得到，不能自行补成现状。

依赖为 Docker 与客户端到宿主的网络。所读 Compose 未声明持久卷；
这只描述此服务配置，不代表客户端状态可以随意清除。
维护配置入口为 homelab-infra `apps/vlmcsd/compose.yaml`。
