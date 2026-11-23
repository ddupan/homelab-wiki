---
title: GCP（CI 云端池与账单）
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/gcp-ci/terraform/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/gcp-org/terraform/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/gcp-billing/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/dynamic-runner/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/observability/metrics/rules/cloud-cost.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/observability/metrics/exporters/cloud-cost.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/ce5976fcf2a198963f3e414ebedba8b1bf6a55c7
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/756b3ba3452fa8dd219a426169c21cbf0ccce76a
watch:
  - homelab-infra:infrastructure/gcp-ci/
  - homelab-infra:infrastructure/gcp-org/
  - homelab-infra:infrastructure/gcp-billing/
  - homelab-infra:platform/dynamic-runner/
  - homelab-infra:platform/observability/metrics/rules/cloud-cost.yaml
  - homelab-infra:platform/observability/metrics/exporters/cloud-cost.yaml
  - homelab-infra:.gitea/workflows/terraform.yml
---

# GCP（CI 云端池与账单）

## 它解决什么问题

GCP 提供 CI 的云端执行池：不需要 Docker、也不访问内网的 job 可以跑在 GKE Autopilot 的一次性 Pod 上，
减轻 laptop 与 sandbox 的负载。三个 Terraform root：

| root | 内容 | 运行方式 |
|---|---|---|
| `infrastructure/gcp-ci/terraform` | 项目 `ddupan-ci`、API、SPIRE 联邦、GKE Autopilot 集群、Actions cache-server（e2-micro）、cloud-scheduler 的 GCP 身份与集群内对象 | CI（`TF_ROOTS`），合并即 apply |
| `infrastructure/gcp-org/terraform` | 组织级授权（Org Policy 管理角色） | 只在本地，CI 无组织权限 |
| `infrastructure/gcp-billing/terraform` | 账单导出 BigQuery 数据集与只读身份 | 本地（不在 `TF_ROOTS`） |

## 从哪里使用

- workflow 写 `runs-on: [cloud]`（默认 2 vCPU / 4 GiB）或 `runs-on: [cloud-small]`（0.5 vCPU / 1 GiB），
  由 [动态 runner](gitea-dynamic-runner.md) 的 `cloud-scheduler` 为每个排队 job 注册一次性 runner 并在 GKE 创建 Pod，
  Pod 直连 Gitea。
- 只适合不需要 Docker、不访问内网的 job。云端 Actions cache 由 `gcp-ci` 的 cache-server 提供。
- 费用：Grafana 的“CI 云端执行”面板；账单告警经 Alertmanager 发到 Telegram。

## 第一次使用

把一个只做 lint 或单元测试的 job 改为 `runs-on: [cloud-small]`，提 PR 观察它被调度并完成。
试用账号的 GCE 配额（全局 12 vCPU）是实际并发上限，排队时间可能比 homelab 池长。

## 日常操作与限制

- **没有服务账号密钥**：CI 的 Terraform（`terraform-ci`）与 cloud-scheduler 都用 [SPIRE](spire.md) JWT-SVID
  （`aud=gcp`）经 Workload Identity Federation 换 GCP 身份。
- `gcp-ci` 第一次必须在本地用 `gcloud auth application-default login` apply（联邦身份尚不存在）；之后由 CI 管理。
- **赠金 2027-02-08 到期**，到期前需升级付费账号，否则资源被关停、只认 `cloud` 标签的 job 会一直排队。
  `CloudCreditExpiringSoon` 在剩 14 天时告警。
- 账单：`platform/observability/metrics/exporters/cloud-cost.yaml` 的 CronJob 每 3 小时从 BigQuery 导出读取，
  写进 VictoriaMetrics；GCP 账单币种为 JPY，月预算在该 CronJob 的 ConfigMap。告警：`CloudCostOverBudget`、
  `CloudCostForecastOverBudget`、`CloudCostCollectorStale`。账单有数小时到一天的延迟，防慢性超支，防不了突发。
- BigQuery 导出须在控制台手动开启（Standard 与 Detailed 都写入 `ddupan-ci` 的 `billing_export`），Terraform 不管理；
  中途关闭或更换数据集不会补历史。
- 停用云端池：从 dynamic-runner 的 `COMPONENTS` 去掉 `cloud-scheduler`，在 Gitea 删除剩余 runner。

## 出问题时

- `cloud` job 一直排队：查 cloud-scheduler 日志、GCE 配额、赠金是否到期，以及 Bao
  `kv/k8s/dynamic-runner` 的 `cloud_gitea_token` 是否存在。
- `CloudCostCollectorStale`：查 monitoring 命名空间 `cloud-cost` Job 日志与 ExternalSecret，并确认 BigQuery 导出仍在运行。

## 运维入口

- 源码：`infrastructure/gcp-ci/terraform`、`infrastructure/gcp-org/terraform`、`infrastructure/gcp-billing/`，
  本地经 `.gitea/scripts/tf.py` 运行；调度器见 `platform/dynamic-runner/README.md`。
- cache-server 的共享密钥会明文进 tfstate，靠 state bucket 的访问控制保护。
- 恢复：集群与项目可由 Terraform 重建；GKE 重建后需更新 `platform/dynamic-runner/gke-ci.yaml` 的 CA 与 Deployment 中的 API 地址。

## 当前状态与证据

- 2026-11-09 用 Terraform 创建 CI 项目并经 SPIRE 联邦接入 CI
  （[ce5976f](https://git.ddupan.top/panxiao81/homelab-infra/commit/ce5976fcf2a198963f3e414ebedba8b1bf6a55c7)），
  同日 OCI/GCP 账单接入告警（[756b3ba](https://git.ddupan.top/panxiao81/homelab-infra/commit/756b3ba3452fa8dd219a426169c21cbf0ccce76a)）。
- `gcp-ci` 在 `.gitea/workflows/terraform.yml` 的 `TF_ROOTS` 中，`gcp-billing` 不在。
