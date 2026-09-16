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
- [External Secrets](services/external-secrets.md)、[OpenEBS](services/openebs.md)：应用秘密与 PVC 消费示例。
- [k3s DNS](services/k3s-dns.md)：Pod 解析路径、配置意图与排障入口。
- [Marker](services/marker.md)、[OpenViking](services/openviking.md)：转换与导入、等待、检索、读取示例。
- [SMTP relay](services/smtp-relay.md)：应用配置、测试邮件与投递边界。
- [发布新服务](guides/publish-service.md)：LAN DNS、证书、Envoy 路由、认证与 GitOps 的完整路径。

- [Samba AD](services/samba-ad.md)、[OCI](services/oci.md)、[Proxmox](services/proxmox.md)：已有资料中的日常管理路径，动态状态未重查。

以上依据源码文档和上游说明整理，示例未在本轮执行，不作为现场验收记录。

## 后续使用说明

本轮列出的使用指南已补齐。后续以实际接入任务补充细节，不自动启动全量现场检查。
Samba AD、OCI、Proxmox 已按维护者指定采用 IaC 优先、以代码为准，并核对关键配置入口；未查询现场。

codex-proxy 已按维护者“应该是退役的”的说明移至归档范围，不再补新接入指南。
LiteLLM、Tailscale、ps3netsrv、vlmcsd 与 k3s 的 wiki 指南已补；源码目录仍缺根 README，配置入口已在各页列出。

## 文档同步与来源链接

- 源码仓库中 Authelia OIDC、LAN DNS、SPIRE 的旧说明后续与知识库结论同步。
- cert-manager / Envoy Gateway README 的 DNS 修改入口仍写旧变量，待同步为受管 records.yml 流程。
- Proxmox README 的早期身份方案与 runner bootstrap 描述待与当前 SPIFFE 原则对齐；Samba README 的通用示例域名/地址待清理。
- 未提交工作区来源合并后，补充正式 commit/PR 链接。
