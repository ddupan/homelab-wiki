---
title: 使用指南来源追溯
last_reviewed: 2026-09-16
---

# 使用指南来源追溯

这份索引帮助读者打开使用指南所依赖的源码，并区分可复现版本与工作区材料。
2026-09-16 对照的是 homelab-infra 本地已有 `origin/main` 对应的
[提交 `5ba4411`](https://git.ddupan.top/panxiao81/homelab-infra/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5)。
本轮没有 fetch、查询服务或修改原仓库；它不是“此刻远端最新版本”的保证。

只对明确列出的来源文件比较 Git blob 与工作区文件哈希，未复制秘密内容或访问运行凭据。
下表是本次文件来源核对，不追认旧指南编写时的内容完全一致，也不验证部署结果。

| 标记 | 如何使用链接 |
|---|---|
| 内容一致 | 固定版本与本次工作区文件一致，可用来复现该文件内容 |
| 工作区有差异 | 链接只供比较已提交基线，不能证明工作区新增内容已合并 |
| 该提交未收录 | 不编造远端文件链接，仍按指南注明的工作区路径读取 |

共核对 62 个不同文件：内容一致 44，工作区有差异 12，该提交未收录 6。
某文件本地显示 untracked，不代表它一定不存在于别的分支；以这里指定提交的树为比较对象。
查更新资料可从 [homelab-infra](https://git.ddupan.top/panxiao81/homelab-infra) 进入，但不要把旧固定链接当实时状态。

维护者说明、独立项目 README、SPIRE ticket 和历史 PR 仍以各页直接链接为准。
本索引只补 homelab-infra 中近期使用指南的主要来源，不替代每页证据范围。

## gitea

[返回使用指南](services/gitea.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/gitea/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/gitea/README.md) |
| `platform/gitea-runner/README.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/gitea-runner/README.md) |

## grafana

[返回使用指南](services/grafana.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `platform/observability/README.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/observability/README.md) |
| `platform/observability/grafana/values.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/observability/grafana/values.yaml) |

## zot

[返回使用指南](services/zot.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/zot/README.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/zot/README.md) |

## seaweedfs

[返回使用指南](services/seaweedfs.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/seaweedfs/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/seaweedfs/README.md) |
| `apps/zot/README.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/zot/README.md) |

## openbao

[返回使用指南](services/openbao.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `infrastructure/openbao/README.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/openbao/README.md) |

## netbox

[返回使用指南](services/netbox.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/netbox/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/netbox/README.md) |
| `apps/netbox/terraform/topology.yml` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/netbox/terraform/topology.yml) |

## shared-postgresql

[返回使用指南](services/shared-postgresql.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/shared-postgresql/migration.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/shared-postgresql/migration.md) |
| `apps/shared-postgresql/cloudnativepg-cluster.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/shared-postgresql/cloudnativepg-cluster.yaml) |
| `apps/shared-postgresql/shared-postgresql-service.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/shared-postgresql/shared-postgresql-service.yaml) |

## litellm-gateway

[返回使用指南](services/litellm-gateway.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/litellm-gateway/docker-compose.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/litellm-gateway/docker-compose.yml) |
| `apps/litellm-gateway/config.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/litellm-gateway/config.yaml) |

## tailscale

[返回使用指南](services/tailscale.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/tailscale/subnet-routes.sh` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/tailscale/subnet-routes.sh) |

## ps3netsrv

[返回使用指南](services/ps3netsrv.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/ps3netsrv/docker-compose.yml` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/ps3netsrv/docker-compose.yml) |

## vlmcsd

[返回使用指南](services/vlmcsd.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/vlmcsd/compose.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/vlmcsd/compose.yaml) |

## external-secrets

[返回使用指南](services/external-secrets.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `platform/external-secrets/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/external-secrets/README.md) |
| `platform/external-secrets/clustersecretstore.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/external-secrets/clustersecretstore.yaml) |
| `platform/external-secrets/externalsecrets.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/external-secrets/externalsecrets.yaml) |
| `platform/external-secrets/kustomization.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/external-secrets/kustomization.yaml) |

## openebs

[返回使用指南](services/openebs.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `platform/openebs/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/openebs/README.md) |
| `platform/openebs/storageclasses.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/openebs/storageclasses.yaml) |

## k3s-dns

[返回使用指南](services/k3s-dns.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `platform/k3s/Corefile.desired` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/k3s/Corefile.desired) |
| `platform/k3s/coredns-custom.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/k3s/coredns-custom.yaml) |

## marker

[返回使用指南](services/marker.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/marker/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/marker/README.md) |
| `apps/marker/Dockerfile` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/marker/Dockerfile) |
| `apps/marker/deployment.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/marker/deployment.yaml) |
| `apps/marker/service.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/marker/service.yaml) |

## openviking

[返回使用指南](services/openviking.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/openviking/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/openviking/README.md) |
| `apps/openviking/docker-compose.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/openviking/docker-compose.yml) |

## smtp-relay

[返回使用指南](services/smtp-relay.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `apps/smtp-relay/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/smtp-relay/README.md) |
| `apps/smtp-relay/service.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/smtp-relay/service.yaml) |
| `apps/smtp-relay/deployment.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/smtp-relay/deployment.yaml) |

## samba-ad

[返回使用指南](services/samba-ad.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `infrastructure/samba-ad/README.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/samba-ad/README.md) |
| `infrastructure/samba-ad/ansible/join-windows.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/samba-ad/ansible/join-windows.yml) |
| `infrastructure/samba-ad/ansible/join-member.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/samba-ad/ansible/join-member.yml) |
| `infrastructure/samba-ad/ansible/roles/samba_member/tasks/main.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/samba-ad/ansible/roles/samba_member/tasks/main.yml) |

## oci

[返回使用指南](services/oci.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `infrastructure/oci/README.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/oci/README.md) |
| `infrastructure/oci/ansible/README.md` | 该提交未收录 | — |
| `infrastructure/oci/terraform/providers.tf` | 该提交未收录 | — |
| `infrastructure/oci/terraform/versions.tf` | 该提交未收录 | — |
| `infrastructure/oci/terraform/compute.tf` | 该提交未收录 | — |
| `infrastructure/oci/terraform/amd.tf` | 该提交未收录 | — |

## proxmox

[返回使用指南](services/proxmox.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `infrastructure/proxmox/README.md` | 该提交未收录 | — |
| `infrastructure/proxmox/README-ha.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/proxmox/README-ha.md) |
| `infrastructure/proxmox/ansible/auth.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/proxmox/ansible/auth.yml) |
| `infrastructure/proxmox/ansible/site.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/proxmox/ansible/site.yml) |
| `infrastructure/proxmox/ansible/ha.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/proxmox/ansible/ha.yml) |

## publish-service

[返回使用指南](guides/publish-service.md)

| 源码路径 | 与工作区比较 | 提交链接 |
|---|---|---|
| `platform/cert-manager/README.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/cert-manager/README.md) |
| `platform/cert-manager/certificate-wildcard-ad.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/cert-manager/certificate-wildcard-ad.yaml) |
| `platform/envoy-gateway/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/envoy-gateway/README.md) |
| `platform/envoy-gateway/gateway.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/platform/envoy-gateway/gateway.yaml) |
| `infrastructure/dns/README.md` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/dns/README.md) |
| `infrastructure/dns/records.yml` | 工作区有差异 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/dns/records.yml) |
| `infrastructure/samba-ad/ansible/provision-dc.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/samba-ad/ansible/provision-dc.yml) |
| `infrastructure/samba-ad/ansible/roles/samba_ad_dc/tasks/dns_records.yml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/infrastructure/samba-ad/ansible/roles/samba_ad_dc/tasks/dns_records.yml) |
| `apps/netbox/securitypolicy.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/netbox/securitypolicy.yaml) |
| `apps/netbox/networkpolicy.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/netbox/networkpolicy.yaml) |
| `apps/authelia/referencegrant-extauth.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/authelia/referencegrant-extauth.yaml) |
| `apps/gitea/httproute.yaml` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/apps/gitea/httproute.yaml) |
| `clusters/homelab/README.md` | 内容一致 | [固定版本](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/5ba441164661bdff24700595e0e6cd7ddb33eec5/clusters/homelab/README.md) |
