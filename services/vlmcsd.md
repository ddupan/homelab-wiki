---
title: vlmcsd 服务入口
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
watch:
  - homelab-infra:apps/vlmcsd/
---

# vlmcsd

homelab 中的 KMS 兼容服务，使用 `mikolatero/vlmcsd` 镜像，以 Docker Compose 运行在笔记本
（192.168.10.127）上。

## 入口与客户端使用

地址为 `kms.ad.ddupan.top:1688`（即 `192.168.10.127:1688`）。它是协议服务，不是网页，不需要登录。

AD 域内有 SRV 记录 `_vlmcs._tcp.ad.ddupan.top` 指向它，**加入域的 Windows 会自动发现**，
通常不需要手动指定服务器。

不在域内、或者自动发现不生效时，在管理员终端中手动指定：

```powershell
cscript.exe "$env:SystemRoot\System32\slmgr.vbs" /skms kms.ad.ddupan.top:1688
cscript.exe "$env:SystemRoot\System32\slmgr.vbs" /ato
cscript.exe "$env:SystemRoot\System32\slmgr.vbs" /dlv
```

第一步修改该客户端的 KMS 目标，第二步发起激活请求，第三步查看结果；
适用前提是客户端版本与其已有授权配置支持 KMS，不能将端口连通当成激活成功。
命令说明见[镜像项目使用说明](https://github.com/mikolatero/docker-vlmcsd)。
已有客户端无需为了接入此服务先卸载产品密钥；本页不复制那类重置步骤。

## 故障与依赖

连接失败先在笔记本上确认容器在运行（`docker ps | grep vlmcsd`），再核对 TCP `1688` 与网络规则；服务可达但请求失败时，
结合客户端详细状态和服务日志区分协议、版本及客户端配置问题。

依赖为 Docker 与客户端到宿主的网络。所读 Compose 未声明持久卷；
这只描述此服务配置，不代表客户端状态可以随意清除。
维护配置入口为 homelab-infra `apps/vlmcsd/compose.yaml`。
