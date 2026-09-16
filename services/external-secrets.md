---
title: External Secrets 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# External Secrets Operator

ESO 将 [OpenBao](openbao.md) 中的秘密投射为 Kubernetes Secret，供应用消费。
本页依据 homelab-infra 工作区 `platform/external-secrets/README.md`、
`clustersecretstore.yaml`、`externalsecrets.yaml` 与 `kustomization.yaml` 整理，未查询现场。
其中 `externalsecrets.yaml` 含未提交修改，不代表这些修改已部署。

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
