---
title: SPIFFE/SPIRE 使用入口与阶段状态
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/issues/34
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/spire/RUNBOOK.md
---

# SPIFFE/SPIRE

SPIFFE 为 homelab 中跨基础设施、由我们自行集成的服务提供统一的机器身份入口，
相当于跨平台的 service account。SPIRE 负责证明运行中的 workload 身份并签发 SVID，
让 Kubernetes、普通 Linux 主机、VM 和 CI/AI Agent 能使用同一套身份体系。

## 核心设计与取舍

SPIFFE/SPIRE 取代了原计划中由 **workload-sts 承担统一 IAM 平台**的方案。
统一的是机器身份：应用信任 SPIFFE 身份，在验证后签发服务自己的 token，
并继续自行维护角色、policy 和资源权限。

```text
运行在不同基础设施上的 workload
  → SPIRE 证明身份，签发 SPIFFE SVID
  → 目标服务验证并信任该身份
  → 目标服务签发自己的 token
  → 按该服务维护的权限访问资源
```

例如 OpenBao 验证 JWT-SVID 后，按照自己的 role/policy 签发短期 Bao token。
能够直接验证 SVID 的服务也可以直接消费身份，授权仍由该服务决定。
人类登录继续使用 Samba AD 与 Authelia。

这一设计有两个主要优势：

- **跨基础设施获取身份。** 非 Kubernetes workload 可以通过适合其环境的节点和进程证明
  接入 SPIRE，无需依赖 Kubernetes ServiceAccount。Kubernetes ServiceAccount 只是
  Kubernetes 环境内的初始证明方式，不是整个 homelab 的身份根。
- **控制现有系统的改造量。** 优先利用目标服务已有的身份验证、token 交换和权限机制，
  增加对 SPIFFE 的信任与身份映射，保留各服务已有的授权模型。

设计定位由维护者于 2026-09-16 补充。workload-sts 项目已归档，停止开发且不部署现有 PoC，
仓库保留早期设计与验证历史。原方案也将最终资源权限留给下游服务；
此次替代主要将自建的机器身份入口与签发能力交给 SPIRE。
详细脉络和历史文档入口见 [workload-sts 设计历史](../architecture/workload-sts-history.md)。
非 Kubernetes 接入和各消费者的实施进度仍以 ticket 为准。

## 当前做到哪里

**基础设施与最小 OpenBao PoC 已完成，真实 workload 的推广接入仍在推进。**
`active` 仅描述已有基础设施，不表示所有消费者均已迁移。

维护者指定以 [homelab-infra #34](https://git.ddupan.top/panxiao81/homelab-infra/issues/34)
为主要状态依据。2026-09-16 查阅时 issue 为 open，最后更新时间为
2026-09-14 12:43:54 UTC；本页是该次查阅的阶段摘要，不替代 ticket 的动态进度。
本轮没有访问运行环境，以下完成结论均为 ticket 记录。

| 已完成阶段 | 记录依据 |
|---|---|
| SPIRE Server、Agent、CSI、OIDC Discovery Provider 上线；节点证明成功 | [9 月 13 日基础设施验收](https://git.ddupan.top/panxiao81/homelab-infra/issues/34#issuecomment-283)，对应 #51 |
| OIDC HTTPS、DNS、TLS、discovery/JWKS 验证；OpenBao JWT backend/role/policy 创建 | [9 月 14 日端到端验收](https://git.ddupan.top/panxiao81/homelab-infra/issues/34#issuecomment-301)，对应 #52、#53 |
| 测试 Pod 获得 aud=openbao 的 JWT-SVID，交换为仅含 spire-poc policy、TTL 300 秒的 Bao token；lookup-self/revoke-self 验证完成 | 同上；临时 workload 与 registration entries 已清理，最终 Terraform plan 为 No changes |
| 新 workload 接入、故障排查和恢复说明已合并 | [9 月 14 日文档记录](https://git.ddupan.top/panxiao81/homelab-infra/issues/34#issuecomment-308)，对应 #54 |

## 如何使用

这是一项面向程序的基础能力，没有供人登录的 SPIRE 业务门户。
下面以已经完成最小 PoC 的 **Kubernetes workload → OpenBao** 路径为例；
其他基础设施使用各自的初始证明方式，取得 SPIFFE 身份后沿用目标服务的信任与授权机制。
如果你的 Kubernetes CI job 或 AI Agent 需要访问 OpenBao，接入路径是：

1. 为 Kubernetes workload 定义专用 ServiceAccount 和稳定 SPIFFE ID。
2. 通过 ClusterSPIFFEID 声明哪些 Pod 能取得该身份，并挂载 CSI Workload API socket。
3. 在 OpenBao 为精确的 subject 和 audience 配置 role 与最小 policy。
4. 程序从 Workload API 获取 `aud=openbao` 的 JWT-SVID，再调用
   `auth/jwt-spire/login` 换取短期 Bao token。
5. 只执行该 policy 允许的操作；退出时尽力吊销 token，并清理进程内的临时凭据。

可直接沿用的配置模板、交换示例和排障步骤见
[权威 RUNBOOK](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/spire/RUNBOOK.md)
的第 4–8 节。这里不复制第二份操作脚本。接入需要新增身份和授权配置，不是挂载 socket 后
就能读取业务秘密；临时 PoC workload 已清理，不是可直接使用的常驻客户端。

运行配置使用的 Kubernetes 身份约定为
`spiffe://ddupan.top/ns/<namespace>/sa/<service-account>`。
ticket 目标章节列出的其他身份形式是设计示例，不应直接替换现有 subject。
OIDC issuer 为 `https://spire-oidc.ad.ddupan.top`，其 discovery/JWKS 用于机器验签。

## 仍在 ticket 中跟踪

截至本次查阅，后续范围包括真实 Gitea CI/AI Agent 的 OpenBao 接入、credential-exec、
SeaweedFS Web Identity/STS、非 Kubernetes 主机与临时 VM 的证明和回收、
Compute/DBaaS 消费身份，以及 HA、备份恢复和多 issuer 约定。
这些是 #34 的开放范围；单个消费者已有其他 PoC，不等于整项已完成。

最小 PoC 标为完成，但验收清单仍有三个未勾选项目：

- 错误 namespace、ServiceAccount 或 selector 无法获得该身份；
- SVID 自动轮换不影响后续登录；
- 删除 registration entry 后不能再取得新 SVID。

因此不能把“PoC 完成”概括成所有负向、轮换和撤销测试都已通过。
已有恢复说明也不等于恢复演练已完成。最新进度回到 #34 查询，不在本页维护另一套勾选清单。

## 必须遵守的边界

- SPIFFE ID 是身份，不自动授予资源权限；资源授权仍由目标服务执行。
- audience 按目标服务绑定，OpenBao role 精确限制 subject；不授予整个 trust domain 通用权限。
- 人类身份保持 Samba AD / Authelia，当前方案不依赖迁移 Keycloak。
- 不因能访问 Agent socket 就允许任意身份；不将短期凭据持久化到镜像、Secret、artifact 或日志。
- PostgreSQL registration state 与 signing-key PVC 必须分别考虑备份；恢复路径不能形成循环依赖。
- PoC 和推广期间保留现有认证回退路径，不能把目标架构当作已经完成的凭据迁移。

完整边界见 ticket 的架构决策与安全恢复章节，以及 RUNBOOK 第 3、9 节。
