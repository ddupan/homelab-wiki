---
title: External Secrets 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-11-23
last_verified: null
sources:
  - homelab-infra platform/external-secrets/README.md、clustersecretstore.yaml、kustomization.yaml
  - homelab-infra 中声明 ExternalSecret 的文件（2026-11-18 汇总，见「当前声明位置」）
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/1577042
watch:
  - homelab-infra:platform/external-secrets/
---

# External Secrets Operator

ESO 将 [OpenBao](openbao.md) 中的秘密投射为 Kubernetes Secret，供应用消费。
原集中文件 `externalsecrets.yaml` 已于 2026-11-03 删除，
各 ExternalSecret 移到使用方目录（[1577042](https://git.ddupan.top/panxiao81/homelab-infra/commit/1577042)）。
“历史：2026-10-04 迁移进度”一节为当日现场核对结果，不代表今天的状态。

## 应用如何获得秘密

现有 `ClusterSecretStore/openbao` 指向 `https://bao.lab.ddupan.top:8200` 的 KV v2 mount `kv`。
ESO 使用 `external-secrets` namespace 中同名 ServiceAccount 的短期 JWT，
通过 OpenBao 的 Kubernetes auth 与 `external-secrets` role 登录。
ESO 不使用 SPIFFE 身份登录。

接入前由维护者确认应用 namespace、OpenBao 路径、字段、目标 Secret 名称和授权范围。
先准备 OpenBao 中的真实值，再提交只含引用的 ExternalSecret；凭据本身不进 Git。
共享 ClusterSecretStore 不意味着任意 namespace 都应有权引用所有秘密，新增引用需要审查来源与消费者权限。

## 最小字段投射示例

以下是待按应用替换的模板：`your-app` namespace 须已存在，
OpenBao 的 `kv/k8s/your-app` 须已包含 `password` 字段且允许 ESO 读取。

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: your-app-credentials
  namespace: your-app
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: openbao
    kind: ClusterSecretStore
  target:
    name: your-app-credentials
    creationPolicy: Owner
  data:
    - secretKey: password
      remoteRef:
        key: k8s/your-app
        property: password
```

`remoteRef.key` 相对于 store 的 `kv` mount，不把 API 的 `data/` 层写进这个例子。
字段映射语义见 [ESO Vault provider](https://external-secrets.io/latest/provider/hashicorp-vault/)；
这里沿用现有 `vault` provider 配置，不因上游出现其他 provider 就修改认证实现。

应用在同一 namespace 的容器配置中引用生成结果，例如：

```yaml
env:
  - name: APP_PASSWORD
    valueFrom:
      secretKeyRef:
        name: your-app-credentials
        key: password
```

这是容器配置片段，需放入应用自己的 manifest，不能独立 apply。
采用环境变量消费时，Secret 刷新不会更新已启动进程的环境变量，轮换须配合应用重启或既有滚动流程。

## 同步与维护边界

受权检查时，先查看 ExternalSecret 的同步状态与事件，再确认目标 Secret 的名称和键是否满足应用引用；
不通过输出 Secret YAML 或解码真实值来证明接入成功。
引用缺失先检查 namespace、路径和字段；认证失败检查 store 的 ServiceAccount、OpenBao role/policy 与 TLS。

`creationPolicy: Owner` 使 ESO 管理目标 Secret 的所有权，删除 ExternalSecret 可能连带删除目标 Secret，
不能将它当作无影响的临时配置。不要手工覆盖 ESO 生成的副本。

`ClusterSecretStore/openbao` 自 2026-11-03 起由 `platform/external-secrets` 的 Kustomization（Flux）管理，
此前为手工 apply。各 ExternalSecret 放在使用方自己的目录里，随其 Kustomization 部署；
新增引用写在应用目录，合并后由 Flux 应用，把文件改好不等于 Flux 已经应用。
部署和接管细节回到 `platform/external-secrets/README.md`。
依赖包括 OpenBao、Kubernetes TokenReview、集群 DNS 与 ESO controller。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#external-secrets)。

## 当前声明位置

以下只记路径不记值。
`apps/*/database.yaml`、`platform/spire/database.yaml` 使用 namespace 级 `SecretStore` 读取 Ayatori 交付的数据库凭据，
其余均引用 `ClusterSecretStore/openbao`。

| 范围 | 声明位置 | OpenBao 路径（`kv/` 下） |
|---|---|---|
| 平台 | `platform/cert-manager`、`platform/external-dns`、`platform/flux-image-automation`、`platform/nats` | `k8s/cert-manager-cloudflare`、`k8s/powerdns`、`k8s/flux-image-automation`、`k8s/nats` |
| CI | `platform/dynamic-runner`、`platform/sandbox-dynamic-runner`、`platform/sandbox-opensandbox` | `k8s/dynamic-runner*`、`k8s/opensandbox-api`、`k8s/gitea-runner-cache-s3` |
| 观测 | `platform/observability/`（grafana SSO、alertmanager、cloud-cost、pve-exporter、otel-collector） | `k8s/grafana-sso`、`k8s/alertmanager`、`k8s/cloud-cost`、`k8s/pve-exporter`、`k8s/otel-collector` |
| 入口 | `infrastructure/cloudflared`、`apps/tailscale` | `k8s/cloudflared`、`k8s/tailscale-operator` |
| 身份 | `apps/iam-login` | `k8s/iam-login`、`k8s/iam-login-ldap` |
| 存储与制品 | `apps/seaweedfs`、`apps/zot`、`apps/artifact-keeper` | `k8s/seaweedfs-s3`、`k8s/seaweedfs-admin-sso`、`k8s/tfstate-backup*`、`k8s/zot-*`、`k8s/artifact-keeper-*` |
| 应用 | `apps/backstage`、`apps/ai-gateway`、`apps/smtp-relay`、`apps/poweradmin`、`apps/research-auto`、`apps/e5renew`、`apps/gitea-backup-drive` | 各自 `k8s/<app>`（含 `-sso` 等后缀） |

随服务退役已从 main 消失：Authelia（`k8s/authelia`、`k8s/authelia-oidc-jwks`，2026-10-11 [b3b4d8f](https://git.ddupan.top/panxiao81/homelab-infra/commit/b3b4d8fd1cb879e2e0b640e52b86c219268e0620)）、
Hydra 与 `gitea-hydra-oidc`（2026-10-05 [82322df](https://git.ddupan.top/panxiao81/homelab-infra/commit/82322df5b6124c7278b289cc2c53771e0135dd17)，清单存档于 `archive/hydra`）、
k3s 上的 Gitea 及 `gitea/gitea-db`（2026-11-11 [3683035](https://git.ddupan.top/panxiao81/homelab-infra/commit/368303573a0a74365e7d961451662d5e21161c68)；Gitea 已迁到 OCI，秘密在 OCI Vault）、
k3s 内 CNPG `shared-db/shared-postgresql-*`（2026-10-13 [29b5a4b](https://git.ddupan.top/panxiao81/homelab-infra/commit/29b5a4b)）。

## 历史：2026-10-04 迁移进度与待迁清单

目标：凭据只在 OpenBao 维护，Kubernetes Secret 由 ESO 投射，本地 gitignored 文件只作 break-glass。
2026-10-04 现场核对：17 个 ExternalSecret 均为 `SecretSynced`。下表只记录当时的路径与名称，不含任何值，
其中多项已随上节所列服务退役而删除。

### 当时已由 ESO 管理

| 目标 Secret | OpenBao 路径 | 当时声明位置 | 备注 |
|---|---|---|---|
| `authelia/authelia-secrets`、`authelia/authelia-oidc-jwks` | `k8s/authelia`、`k8s/authelia-oidc-jwks` | `platform/external-secrets/externalsecrets.yaml`（手工 apply） | 已随 Authelia 删除 |
| `gitea/gitea-db` | `k8s/gitea` | 同上 | 已随 k3s Gitea 删除 |
| `cloudflared/cloudflared-tunnel` | `k8s/cloudflared` | 同上 | 现在 `infrastructure/cloudflared/external-secret.yaml` |
| `seaweedfs/seaweedfs-s3-config` | `k8s/seaweedfs-s3` 等组装 | 同上 | 现在 `apps/seaweedfs/s3-config-external-secret.yaml` |
| `cert-manager/cloudflare-api-token` | `k8s/cert-manager-cloudflare` | `platform/cert-manager/external-secret.yaml`（Flux） | 2026-10-04 迁入，[#195](https://git.ddupan.top/panxiao81/homelab-infra/pulls/195) |
| `smtp-relay/smtp-relay-secret` | `k8s/smtp-relay` | `apps/smtp-relay/external-secret.yaml`（Flux） | 同上；smtp-relay 同时改由 Flux 管理 |
| `research-auto/research-auto-secret`、`research-auto-bootstrap-secret` | `k8s/research-auto`、`k8s/research-auto-bootstrap` | `apps/research-auto/external-secret.yaml`（Flux） | 2026-10-04 迁入，[#196](https://git.ddupan.top/panxiao81/homelab-infra/pulls/196) |
| backstage、dynamic-runner、hydra、gitea-hydra-oidc、nats、zot、alertmanager、flux 写凭据 | 各自 `k8s/<app>` | 各应用目录（Flux） | hydra、gitea-hydra-oidc 已删除 |

2026-10-04 的迁移方法：按现网原样写入（CAS=0，路径已存在则不写），读回按 key 比对哈希；
ExternalSecret 与现网 Secret 同名，ESO 直接接管；接管后再比对一次哈希。
⚠ 把手工 apply 的应用交给 Flux 时，**`kubectl diff` 为空不代表不会重启**：pod 模板上
`kubectl rollout restart` 留下的 `restartedAt` 注解不在 last-applied 中，Flux server-side apply 会删掉它并触发一次滚动。
smtp-relay 与 research-auto 均因此重启过一次。接管前应直接比对线上 `spec.template`。

### 有意不迁

| 对象 | 原因 |
|---|---|
| `gitea/gitea-oidc-secret`、`monitoring/grafana-oidc` | 只服务 Authelia；已随 Authelia 于 2026-10-11 退役（Grafana 现用 `k8s/grafana-sso`） |
| `spire-server/spire-external-kubeconfigs` | 由 sandbox-cluster Ansible 单独拥有并生成，Flux 与人工均不得写入 |
| `shared-db/shared-postgresql-*` | 旧 CNPG，已于 2026-10-13 退役，应用迁到[共享 PostgreSQL](shared-postgresql.md) |
| `apps/*/secret.yaml`、`.vault_pass` | break-glass 副本与恢复链根（`.vault_pass.gpg`），设计如此 |

Kanidm 已是历史：其遗留的 `gitea/gitea-kanidm-secret`、`default/kanidm-tls` 已于 2026-10-04 删除。

### 待迁移

**只存在于 laptop 的本地文件**（gitignored，不在 OpenBao，laptop 损坏即丢失）：

| 文件 | 内容类别 | 建议 |
|---|---|---|
| `apps/tailscale/helm.sh` | Tailscale operator OAuth | 已迁：main 上 `apps/tailscale/external-secret.yaml` 读 `k8s/tailscale-operator`（2026-11-03 起 Flux）；本地旧文件应删除，不再复用 |
| `apps/codex-proxy/.env` | 应用凭据 | 按服务迁入 OpenBao |
| `apps/litellm-gateway/.env`、`auth.json` | 网关与上游凭据 | 同上 |
| `apps/openviking/.env` | 应用凭据 | 同上 |
| `infrastructure/proxmox/pxe/secrets.env`、`answer/*.toml` | PVE 安装凭据 | 迁入 `infra/proxmox/pxe`，安装前由脚本取回 |
| `infrastructure/proxmox/vyos/credentials.yml` | VyOS 登录凭据 | 迁入 `infra/vyos` |
| `infrastructure/oci/terraform/terraform.tfvars.json` | OCI 实例 metadata（敏感变量） | 迁入 `infra/terraform/oci`，或由 `prepare-local-state.py` 从加密源备份再生 |
| `infrastructure/cloudflared/backup/` | 旧隧道凭据 JSON 与旧配置 | 隧道已改为 token 管理；确认失效后删除，不迁 |

**来源待确认的 Helm 生成 Secret**（2026-10-04 清单）：以下由 chart 渲染，但值可能来自本地 values 或命令参数，
需逐个确认是否只存在于本地：`e5renew/e5renew-secret`、`tailscale/operator-oauth`（即上面的 `helm.sh`）、
`monitoring/grafana`、`rustfs/rustfs-secret`、`seaweedfs/seaweedfs-db-secret`、`openebs/openebs-minio`。

**Ansible Vault**：`infrastructure/samba-ad` 的 vault 可按计划迁到 `community.hashi_vault` 查找（现状见 [Samba AD](samba-ad.md)）；
`infrastructure/openbao` 必须保留 ansible-vault（它取得 OpenBao 自身 TLS 证书所需的凭据，不能反向依赖 OpenBao）。

**仓库历史中的哈希与旧值**：`apps/authelia/values.yaml` 中 gitea/grafana/openbao client 的 pbkdf2 哈希，
以及已关闭 PR #178 中 backstage client 的哈希，随 Authelia 下线失效，维护者决定不轮换；
`infrastructure/proxmox/vyos/backups/config.boot` 含 vyos 用户的 `encrypted-password`，尚未处理。

Terraform state 已于 2026-10-04 收敛到远端 backend（S3 或 OCI）；本地只剩 incus 的
`*.pre-s3-20261004` 迁移前副本（归 Ayatori 范围维护者处理）与 OCI 的 GPG 加密源备份。
