---
title: SMTP relay 应用发信指南
lifecycle: unknown
evidence: documented
last_reviewed: 2026-10-04
last_verified: null
---

# SMTP relay

为集群应用提供统一出站邮件入口：应用通过集群内 SMTP 连接 relay，
relay 再使用 STARTTLS 与 XOAUTH2 向 Microsoft 365 提交邮件。
本页依据 homelab-infra `apps/smtp-relay/README.md` 与 Service/Deployment 配置整理，
本轮没有连接 relay、发送邮件或查询邮箱。

## 应用接入参数

| 参数 | 已记录值 |
|---|---|
| SMTP host | `smtp-relay.smtp-relay.svc.cluster.local` |
| SMTP port | `25` |
| 应用到 relay 的 TLS | 此内部链路按明文 SMTP 配置 |
| 应用到 relay 的认证 | 不提供用户名或密码 |
| From / envelope sender | `noreply@ddupan.top` |
| relay 的上游 | `smtp.office365.com:587`，STARTTLS + XOAUTH2 |

这里的无认证入口限于既定内部使用路径，不能直接把它暴露为外部发信入口。
其他发件身份需要对应的 Send As 授权，不能只在应用中随意改 From。
应用只需要 relay 参数，不需要读取或持有 Microsoft 365 refresh token。

## 发送一封接入测试邮件

下面在已能访问集群 Service 的应用环境中使用 Python 标准库。
将 `SMTP_TEST_RECIPIENT` 设置为自己控制的收件地址；执行会真实发送邮件，应先得到该次发信授权。
这份示例本轮未执行。

```python
import os
import smtplib
from email.message import EmailMessage

recipient = os.environ["SMTP_TEST_RECIPIENT"]
sender = "noreply@ddupan.top"
message = EmailMessage()
message["From"] = sender
message["To"] = recipient
message["Subject"] = "Homelab SMTP relay test"
message.set_content("SMTP relay integration test.")
with smtplib.SMTP("smtp-relay.smtp-relay.svc.cluster.local", 25, timeout=30) as smtp:
    refused = smtp.send_message(message, from_addr=sender, to_addrs=[recipient])
    if refused:
        raise SystemExit("收件人被拒绝，请检查 relay 状态")
```

客户端提交成功只表示 relay 接收，不保证最终送达。
维护者随后结合 relay 投递日志与收件箱确认完整链路；也检查垃圾邮件文件夹。
日志中的上游接收结果仍不能替代收件人侧确认。

## 失败时如何区分

- 连接超时或域名失败：检查集群 DNS、Service 与应用网络范围。
- relay 接收但不送达：检查投递队列、上游连接和认证，而不是给应用配置上游密码。
- `535 5.7.3`：源码提示检查 OAuth 身份是否为实际 sender，以及 token 是否需要重新初始化。
- `5.7.60`：检查 From、envelope sender 与 Microsoft 365 的发信授权是否匹配。

消费者接入不能通过重跑完整 Terraform、部署或 OAuth 初始化流程来试错。
refresh token 持久化在 `smtp-relay-tokens` PVC，SASL 层负责更新；
它是可变运行数据，不是可复制进 wiki 的配置。
源码的 device-code 流程使用 public client，维护说明明确 `CLIENT_SECRET` 留空；
不要照抄同一旧 README 中与之不一致的“创建 client secret”注释。

自 2026-10-04 起，`apps/smtp-relay` 由 Flux 管理，`smtp-relay-secret` 由 ESO 从 OpenBao
`kv/k8s/smtp-relay` 同步（[#195](https://git.ddupan.top/panxiao81/homelab-infra/pulls/195)）；
gitignored 的 `secret.yaml` 只在 OpenBao 不可用时手工 apply。改部署请提交 Git，直接 `kubectl apply` 会被 Flux 改回。

初始化、重新授权、DKIM 与恢复入口为 `apps/smtp-relay/README.md`。
其中 DKIM 等日期属于历史记录，本文不将其升级为新一次验证。
依赖为 Kubernetes/DNS、token PVC、Microsoft 365 邮箱与授权、上游网络及域名邮件配置。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#smtp-relay)。
