# 文档完善清单

本轮待核实事项已于 2026-09-16 收尾。以下是后续写作工作，不是未解决的状态核实任务，
也不代表所有相关项目都已部署或经过现场验收。需要补充事实时仍先向维护者对齐范围。

## 已补充使用指南

- [Gitea / Actions](services/gitea.md)：登录、建仓库、最小 CI、runner 选择和常见问题。
- [Grafana](services/grafana.md)：内存看板、指标查询、日志搜索和数据源用途。
- [zot](services/zot.md)：拉取、发布授权、workflow 身份职责与后端数据恢复边界。
- [SeaweedFS](services/seaweedfs.md)：S3 入口、专用凭据、列举与上传下载示例。
- [OpenBao](services/openbao.md)：人的登录、按权限取密及机器身份边界。
- [NetBox](services/netbox.md)：浏览设备与 IPAM，明确 Git 来源与评估用途。

- [共享 PostgreSQL](services/shared-postgresql.md)：应用接入、连接检查与共享实例维护边界。

- [LiteLLM](services/litellm-gateway.md)：模型请求、认证边界与独立数据库依赖。
- [Tailscale](services/tailscale.md)：客户端接入、子网路由和 operator Service 的区别。
- [ps3netsrv](services/ps3netsrv.md)、[vlmcsd](services/vlmcsd.md)：客户端使用与配置入口。

以上依据源码文档和上游说明整理，示例未在本轮执行，不作为现场验收记录。

## 后续使用说明

1. k3s：补 CoreDNS 定制说明；目录缺少根 README。
2. marker、openviking、smtp-relay、external-secrets、openebs 等：按服务总览逐步补齐消费示例。

codex-proxy 已按维护者“应该是退役的”的说明移至归档范围，不再补新接入指南。
本轮新增的四份使用指南已完成；其源码目录仍缺根 README，权威配置入口已在各页列出。

## 文档同步与来源链接

- 源码仓库中 Authelia OIDC、LAN DNS、SPIRE 的旧说明后续与知识库结论同步。
- 未提交工作区来源合并后，补充正式 commit/PR 链接。
