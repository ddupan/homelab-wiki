# workload-sts：早期设计与 SPIRE 替代决策

**项目已归档、停止开发，不应部署或继续扩展现有 PoC。** 仓库保留早期设计和技术验证历史。
维护者于 2026-09-16 确认归档；同日读取仓库元数据确认 `archived: true`，
并查阅首页与替代决策。没有查询运行环境。

当前方案见 [SPIFFE/SPIRE](../services/spire.md)。历史源码与设计保存在
[workload-sts 仓库](https://git.ddupan.top/panxiao81/workload-sts)。

## 原方案做什么

workload-sts 是原统一机器身份方案中的 OAuth 2.0 Security Token Service：
验证 Kubernetes ServiceAccount JWT 等上游证明，映射稳定 workload principal，
根据 audience、scope 等签发规则生成短期 JWT assertion，由 OpenBao 等下游服务
验证该 assertion，并自行映射权限、签发和管理服务自己的 token。

原方案也明确不提供人类用户目录，不管理下游资源权限和 VM/job 生命周期。
因此，“被替代的统一 IAM 平台”指机器身份入口与签发层的自建方案，
不能理解为早期方案曾要求集中管理所有服务权限。

项目停在 PoC 阶段，首页明确未提供可运行服务或稳定 API。
历史 issuer、协议字段和 API 规格不属于当前可用接口。

## 为什么改用 SPIRE

[2026-09-13 接受的替代决策](https://git.ddupan.top/panxiao81/workload-sts/src/branch/main/docs/superseded-by-spire.md)
明确将 workload attestation、身份签发与轮换、OIDC/JWKS federation 交给 SPIRE，
避免继续维护重复的签名、策略和身份映射基础设施。

当前路径为 workload → SPIRE Workload API → JWT-SVID → 目标服务验证身份，
再由目标服务维护授权及自身 token 生命周期。跨基础设施的身份获取不再以
Kubernetes ServiceAccount 为统一入口。

原计划中的 OAuth Token Exchange、内部 principal UUID、Transit JWT signing key、
自建 JWKS endpoint 和集中式 CEL 策略不继续作为当前方案需求。
未来若有目标服务不能原生处理的 token 转换或凭据签发需求，应按具体消费者重新评估
小型 broker；不能仅因未来可能用到 scope 就恢复旧项目。

## 历史文档入口

| 文档 | 阅读目的 |
|---|---|
| [README](https://git.ddupan.top/panxiao81/workload-sts/src/branch/main/README.md) | 原项目目标、边界和停止开发说明 |
| [替代决策](https://git.ddupan.top/panxiao81/workload-sts/src/branch/main/docs/superseded-by-spire.md) | 为什么停止、自建能力如何由 SPIRE 替代 |
| [architecture](https://git.ddupan.top/panxiao81/workload-sts/src/branch/main/docs/architecture.md) | 早期系统边界与数据流 |
| [specification](https://git.ddupan.top/panxiao81/workload-sts/src/branch/main/docs/specification.md) | 早期规范行为与待决策项 |
| [security](https://git.ddupan.top/panxiao81/workload-sts/src/branch/main/docs/security.md) | 当时的威胁模型与安全要求 |
| [poc](https://git.ddupan.top/panxiao81/workload-sts/src/branch/main/docs/poc.md) | 首轮库与签名技术验证结论 |

后四项按项目首页和目录收录为历史入口，本轮未逐篇复核。它们不代表当前实施计划；
判断当前设计先读替代决策和 SPIFFE 页面，动态进度再看 homelab-infra #34。
