# 外部消费者与知识库范围

> **2026-11-18 范围变更（维护者说明）**：e5renew、research-auto 现由 homelab-infra 经 Flux 部署
> （`apps/e5renew`、`apps/research-auto`），使用 pg-prod 租户与 External Secrets，因此纳入本知识库，
> **只记录部署与依赖**，应用自身的使用与开发文档仍由各自项目维护。
> 部署页见 [e5renew](e5renew.md)、[research-auto](research-auto.md)。下文为 2026-09-16 的原范围说明，保留作历史。

维护者于 2026-09-16 明确：以下项目托管在其 GitHub 上，是外部的单纯消费者，
与 homelab 没有直接项目关联，**不属于 homelab 基础设施**。

| 项目 | 项目仓库 | 在本知识库中的归属 |
|---|---|---|
| e5renew | [panxiao81/e5renew](https://github.com/panxiao81/e5renew) | 外部消费者，排除在基础设施盘点范围之外 |
| research-auto | [panxiao81/research-auto](https://github.com/panxiao81/research-auto) | 外部消费者，排除在基础设施盘点范围之外 |

历史运维记录中出现项目名称、容器或网络，不意味着它们由 homelab 基础设施仓库管理。
本知识库仅保留归属与仓库入口，不追踪其部署、开发进度或应用使用文档，也不将其列为
“缺少基础设施配置”的问题。相关应用知识由各自项目维护。

将来处理共享服务时，如确实涉及这些消费者，只记录与该基础设施变更有关的消费关系，
不把外部项目纳入基础设施生命周期管理。
