---
title: External Secrets 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-10-04
last_verified: null
---

# External Secrets Operator

ESO 将 [OpenBao](openbao.md) 中的秘密投射为 Kubernetes Secret，供应用消费。
本页依据 homelab-infra 工作区 `platform/external-secrets/README.md`、
`clustersecretstore.yaml`、`externalsecrets.yaml` 与 `kustomization.yaml` 整理。
两个文件均已提交 main（`externalsecrets.yaml` 最后修改于 `68c6099`）；“迁移进度”一节为 2026-10-04 现场核对结果。

## 应用如何获得秘密

现有 `ClusterSecretStore/openbao` 指向 `https://bao.ad.ddupan.top:8200` 的 KV v2 mount `kv`。
ESO 使用 `external-secrets` namespace 中同名 ServiceAccount 的短期 JWT，
通过 OpenBao 的 Kubernetes auth 与 `external-secrets` role 登录。
这是已记录的认证方式，不能因 SPIFFE 是整体身份设计就宣称 ESO 已迁移到 SPIFFE。

接入前由维护者确认应用 namespace、OpenBao 路径、字段、目标 Secret 名称和授权范围。
先准备 OpenBao 中的真实值，再提交只含引用的 ExternalSecret；凭据本身不进 Git。
共享 ClusterSecretStore 不意味着任意 namespace 都应有权引用所有秘密，新增引用需要审查来源与消费者权限。

## 最小字段投射示例

以下是待按应用替换的模板：`your-app` namespace 须已存在，
OpenBao 的 `kv/k8s/your-app` 须已包含 `password` 字段且允许 ESO 读取。
本轮仅展示模板，没有创建这些对象。

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

源码 README 明确区分 Helm release 接管与 secret delivery 对象接管，当前目录 Kustomization
只列 Helm 相关资源，没有列入 `clustersecretstore.yaml` 和 `externalsecrets.yaml`。
新增引用先确定由哪个 GitOps/部署入口管理；把文件改好不等于 Flux 已经应用。
部署和接管细节回到 `platform/external-secrets/README.md`。
依赖包括 OpenBao、Kubernetes TokenReview、集群 DNS 与 ESO controller。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#external-secrets)。

## 迁移进度与待迁清单（2026-10-04）

目标：凭据只在 OpenBao 维护，Kubernetes Secret 由 ESO 投射，本地 gitignored 文件只作 break-glass。
2026-10-04 现场核对：17 个 ExternalSecret 均为 `SecretSynced`。下表只记录路径与名称，不含任何值。

### 已由 ESO 管理

| 目标 Secret | OpenBao 路径 | 声明位置 | 备注 |
|---|---|---|---|
| `authelia/authelia-secrets`、`authelia/authelia-oidc-jwks` | `k8s/authelia`、`k8s/authelia-oidc-jwks` | `platform/external-secrets/externalsecrets.yaml` | 该文件**手工 apply**，未列入 Flux |
| `gitea/gitea-db` | `k8s/gitea` | 同上 | 同上 |
| `cloudflared/cloudflared-tunnel` | `k8s/cloudflared` | 同上 | 同上 |
| `seaweedfs/seaweedfs-s3-config` | `k8s/seaweedfs-s3` 等组装 | 同上 | 同上 |
| `cert-manager/cloudflare-api-token` | `k8s/cert-manager-cloudflare` | `platform/cert-manager/external-secret.yaml`（Flux） | 2026-10-04 迁入，[#195](https://git.ddupan.top/panxiao81/homelab-infra/pulls/195) |
| `smtp-relay/smtp-relay-secret` | `k8s/smtp-relay` | `apps/smtp-relay/external-secret.yaml`（Flux） | 同上；`CLIENT_SECRET` 按设计为空；smtp-relay 同时改由 Flux 管理 |
| `research-auto/research-auto-secret`、`research-auto-bootstrap-secret` | `k8s/research-auto`、`k8s/research-auto-bootstrap` | `apps/research-auto/external-secret.yaml`（Flux） | 2026-10-04 迁入，[#196](https://git.ddupan.top/panxiao81/homelab-infra/pulls/196)；部署声明从应用仓库移入 homelab-infra |
| backstage、dynamic-runner、hydra、gitea-hydra-oidc、nats、zot、alertmanager、flux 写凭据 | 各自 `k8s/<app>` | 各应用目录（Flux） | — |

2026-10-04 的迁移方法：按现网原样写入（CAS=0，路径已存在则不写），读回按 key 比对哈希；
ExternalSecret 与现网 Secret 同名，ESO 直接接管；接管后再比对一次哈希。
⚠ 把手工 apply 的应用交给 Flux 时，**`kubectl diff` 为空不代表不会重启**：pod 模板上
`kubectl rollout restart` 留下的 `restartedAt` 注解不在 last-applied 中，Flux server-side apply 会删掉它并触发一次滚动。
smtp-relay 与 research-auto 均因此重启过一次。接管前应直接比对线上 `spec.template`。

### 有意不迁

| 对象 | 原因 |
|---|---|
| `gitea/gitea-oidc-secret`、`monitoring/grafana-oidc` | 只服务 Authelia；Authelia 将由新的 IdM 取代，随之下线 |
| `spire-server/spire-external-kubeconfigs` | 由 sandbox-cluster Ansible 单独拥有并生成，Flux 与人工均不得写入 |
| `shared-db/shared-postgresql-*` | 旧 CNPG，随应用迁移到[共享 PostgreSQL](shared-postgresql.md)一并处理 |
| `apps/*/secret.yaml`、`.vault_pass` | break-glass 副本与恢复链根（`.vault_pass.gpg`），设计如此 |

Kanidm 已是历史：其遗留的 `gitea/gitea-kanidm-secret`、`default/kanidm-tls` 已于 2026-10-04 删除。

### 待迁移

**只存在于 laptop 的本地文件**（gitignored，不在 OpenBao，laptop 损坏即丢失）：

| 文件 | 内容类别 | 建议 |
|---|---|---|
| `apps/tailscale/helm.sh` | Tailscale operator OAuth | 迁入 `k8s/tailscale`，operator Secret 改由 ESO 提供 |
| `apps/codex-proxy/.env` | 应用凭据 | 按服务迁入 OpenBao |
| `apps/litellm-gateway/.env`、`auth.json` | 网关与上游凭据 | 同上 |
| `apps/openviking/.env` | 应用凭据 | 同上 |
| `infrastructure/proxmox/pxe/secrets.env`、`answer/*.toml` | PVE 安装凭据 | 迁入 `infra/proxmox/pxe`，安装前由脚本取回 |
| `infrastructure/proxmox/vyos/credentials.yml` | VyOS 登录凭据 | 迁入 `infra/vyos` |
| `infrastructure/oci/terraform/terraform.tfvars.json` | OCI 实例 metadata（敏感变量） | 迁入 `infra/terraform/oci`，或由 `prepare-local-state.py` 从加密源备份再生 |
| `infrastructure/cloudflared/backup/` | 旧隧道凭据 JSON 与旧配置 | 隧道已改为 token 管理；确认失效后删除，不迁 |

**来源待确认的 Helm 生成 Secret**：以下由 chart 渲染，但值可能来自本地 values 或命令参数，
需逐个确认是否只存在于本地：`e5renew/e5renew-secret`、`tailscale/operator-oauth`（即上面的 `helm.sh`）、
`monitoring/grafana`、`rustfs/rustfs-secret`、`seaweedfs/seaweedfs-db-secret`、`openebs/openebs-minio`。

**Ansible Vault**：`infrastructure/samba-ad` 的 vault 可按计划迁到 `community.hashi_vault` 查找；
`infrastructure/openbao` 必须保留 ansible-vault（它取得 OpenBao 自身 TLS 证书所需的凭据，不能反向依赖 OpenBao）。

**仓库历史中的哈希与旧值**：`apps/authelia/values.yaml` 中 gitea/grafana/openbao client 的 pbkdf2 哈希，
以及已关闭 PR #178 中 backstage client 的哈希，随 Authelia 下线失效，维护者决定不轮换；
`infrastructure/proxmox/vyos/backups/config.boot` 含 vyos 用户的 `encrypted-password`，尚未处理。

Terraform state 已于 2026-10-04 收敛到远端 backend（S3 或 OCI）；本地只剩 incus 的
`*.pre-s3-20261004` 迁移前副本（归 Ayatori 范围维护者处理）与 OCI 的 GPG 加密源备份。

