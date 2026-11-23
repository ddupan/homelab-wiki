---
title: SMTP relay 应用发信指南
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - homelab-infra `apps/smtp-relay/README.md`、Service/ExternalSecret 配置
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/735
watch:
  - homelab-infra:apps/smtp-relay/
  - homelab-infra:infrastructure/oci/terraform/smtp-relay-mail.tf
  - homelab-infra:infrastructure/oci/terraform/gitea-mail.tf
  - homelab-infra:infrastructure/proxmox/ansible/roles/pve_mail_relay/
  - homelab-infra:infrastructure/cloudflared/terraform/mail.tf
---

# SMTP relay

为 lab 内部的应用和 PVE 节点提供统一出站邮件入口：客户端不认证、明文提交到 relay 的 25 端口，
relay（`boky/postfix`）再以 SASL 用户名密码经强制 STARTTLS 转发到 OCI Email Delivery
（`smtp.email.ap-osaka-1.oci.oraclecloud.com:587`）。
自 2026-11-12 起使用 OCI（[PR #735](https://git.ddupan.top/panxiao81/homelab-infra/pulls/735)，
[47b0bb6](https://git.ddupan.top/panxiao81/homelab-infra/commit/47b0bb6)）；此前转发到 Microsoft 365，见[历史](#历史microsoft-365-上游2026-11-前)。

## 应用接入参数

| 参数 | 值 |
|---|---|
| SMTP host（集群内） | `smtp-relay.smtp-relay.svc.cluster.local` |
| SMTP host（LAN，仅 PVE 节点） | `192.168.10.127`（`service-lan.yaml`） |
| SMTP port | `25` |
| 客户端到 relay 的 TLS | 明文 SMTP |
| 客户端到 relay 的认证 | 不提供用户名或密码 |
| From / envelope sender | 只能是 `noreply@ddupan.top`（OCI 的已批准发件人） |
| relay 的上游 | `smtp.email.ap-osaka-1.oci.oraclecloud.com:587`，STARTTLS + SASL |

PVE 节点经 `infrastructure/proxmox/ansible/roles/pve_mail_relay` 配置 relayhost 与发件人改写。
OCI 免费额度每月 3000 封，与 Gitea 共用。应用不需要也不应持有上游 SMTP 凭据。

## 访问控制

relay 只检查发件人域名，对任何能连上端口的客户端放行，所以访问控制完全在网络层：

- `service.yaml`：ClusterIP，仅集群内可达。
- `service-lan.yaml`：`loadBalancerSourceRanges` 只放三台 PVE。klipper 会把 LAN 客户端 SNAT 成 `10.42.0.1`，
  Postfix 分不清来源，**这份源地址列表是唯一的门**，不要删除或放宽。

验证访问控制时要从被移出列表的 PVE 上实测被拒；在 k3s 本机测试走的是另一条 iptables 路径，会得出错误结论。
不能把这个无认证入口暴露为外部发信入口。

## 发送一封接入测试邮件

维护者可在 relay Pod 内发信并查看日志：

```bash
kubectl --context default -n smtp-relay exec deploy/smtp-relay -- sh -c \
  'printf "Subject: relay test\n\nhello\n" | sendmail -f noreply@ddupan.top you@example.com'
kubectl --context default -n smtp-relay logs deploy/smtp-relay --tail=40   # 找 status=sent
```

把 `you@example.com` 换成自己控制的收件地址；执行会真实发送邮件，应先得到该次发信授权。
日志中 `status=sent` 只表示上游接收，最终送达仍需在收件箱（含垃圾邮件文件夹）确认。

## 失败时如何区分

- 连接超时或域名失败：检查集群 DNS、Service 与客户端网络范围；PVE 节点还要确认自己在 `loadBalancerSourceRanges` 中。
- 发件人被拒：确认 From 与 envelope sender 都是 `noreply@ddupan.top`。
- relay 接收但不送达：查 relay 日志中的上游结果与认证错误，而不是给应用配置上游密码。
- 刚轮换上游凭据后仍认证失败：ESO 的 `refreshInterval` 为 1h，需手动 force-sync 并重启 Deployment（见下节）。

## 运维入口

- 部署：`apps/smtp-relay` 由 Flux 管理；直接 `kubectl apply` 会被 Flux 改回。
- 凭据：OCI 用户、SMTP 凭据、发件人和 DKIM 在 `infrastructure/oci/terraform`（`smtp-relay-mail.tf`、`gitea-mail.tf`）。
  SMTP 凭据只在创建时返回，apply 后由人写入 OpenBao `kv/k8s/smtp-relay`，ESO 同步为 `smtp-relay-secret`；
  写入后 annotate ExternalSecret 触发同步并 `rollout restart`，具体命令见源码 README“凭据”一节。不要把值写进 wiki。
- Bao 不可用时：由 `secret.example.yaml` 复制出 gitignored 的 `secret.yaml` 手工 apply。
- 送达：DKIM 选择器 `oci-kix-202611._domainkey`（d=ddupan.top），记录在 `infrastructure/cloudflared/terraform/mail.tf`；
  SPF 不含 OCI，DMARC 依靠 DKIM 对齐通过。

依赖为 Kubernetes/DNS、OpenBao/ESO、OCI Email Delivery 与上游网络、域名邮件记录。

## 当前状态与证据

relay 自 2026-11-12 起使用 OCI 上游（[PR #735](https://git.ddupan.top/panxiao81/homelab-infra/pulls/735)）；
切换后尚未做过端到端送达验证。


## 历史：Microsoft 365 上游（2026-11 前）

2026-11 前 relay 以 STARTTLS + XOAUTH2（sasl-xoauth2 加 Entra 应用）向 `smtp.office365.com:587` 提交，
refresh token 持久化在 `smtp-relay-tokens` PVC。ddupan.top 的 M365 开发者沙盒预计约 2027-01-23 被清退，
因此改为 OCI；XOAUTH2、device-code 初始化与 token PVC 已不再使用，相关操作说明不再适用。
自 2026-10-04 起该应用由 Flux 管理、凭据经 ESO 从 OpenBao 同步（[#195](https://git.ddupan.top/panxiao81/homelab-infra/pulls/195)），这一点沿用至今。
