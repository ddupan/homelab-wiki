---
title: Sandbox k3s 集群
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/sandbox-cluster/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/clusters/sandbox/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/sandbox-opensandbox/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/platform/sandbox-ci-runners/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/clusters/ayatori-prod/sandbox-k8s.yaml
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/8b90ee59956e3fb054a2b5f37f581bd80caccc96
watch:
  - homelab-infra:infrastructure/sandbox-cluster/
  - homelab-infra:clusters/sandbox/
  - homelab-infra:platform/sandbox-opensandbox/
  - homelab-infra:platform/sandbox-ci-runners/
  - homelab-infra:clusters/ayatori-prod/sandbox-k8s.yaml
  - homelab-infra:clusters/ayatori-prod/sandbox-postgresql.yaml
---

# Sandbox k3s 集群

## 它解决什么问题

与 laptop 上主 k3s 分开的双节点 k3s 集群，承载 OpenSandbox、CI 执行环境和 AI agent workload，
让不可信或重负载任务不和 homelab 主集群共用节点。它有自己的 External Secrets Operator、SPIRE agent、
监控和 Kata Containers（Cloud Hypervisor microVM）。

| 节点 | PVE / VMID | 地址 | 资源 |
|---|---|---|---|
| sandbox1 | pve1 / 148 | 10.60.0.11 | 4 vCPU / 6 GiB |
| sandbox2 | pve2 / 149 | 10.60.0.12 | 4 vCPU / 4 GiB |

两台都是 privileged LXC，位于 labnet `10.60.0.0/24`，经 VyOS 路由。

## 从哪里使用

- **写 workflow 的人**：不直接用这个集群。`runs-on` 选择对应 runner label，由
  [动态 runner](gitea-dynamic-runner.md) 在这里创建一次性执行环境（如 Kata VM 的 `ci-vm` Pool）。
- **K3s API**：`sandbox-k8s.lab.ddupan.top:6443`；**OpenSandbox API**：同名 `:8080`（API key 在 Bao
  `kv/k8s/opensandbox-api`）。两者都经 [Ayatori LoadBalancer](ayatori-loadbalancer.md) `sandbox/k8s` 暴露，
  该名是指向 LB Hostname 的 CNAME，证书 SAN 只含这个名字，不要用 VIP 或节点 IP。
- 集群管理员 kubeconfig 向维护者索取。

## 第一次使用

在 workflow 里用 VM label（标签名以[动态 runner](gitea-dynamic-runner.md)页为准），运行一个只打印 `uname -a`
的 job；预期 job 在 Kata guest 中执行，结束后环境被删除。

## 日常操作与限制

- 所有权：Ansible（`infrastructure/sandbox-cluster/`）管 LXC、OS 基线、外部 PostgreSQL、K3s、Flux bootstrap；
  Flux（`clusters/sandbox/`）管集群内组件：Kata、SPIRE agent/CSI、监控、ESO、OpenSandbox、CI Pool 与 dynamic runner。
  同一对象只有一个 owner。
- K3s datastore 是外部 PostgreSQL（两节点各一成员，Patroni 选主，DCS 用[共享 etcd](shared-etcd.md)），
  入口 `pg-sandbox.lab.ddupan.top`，同样经 Ayatori LB，按 `/primary` 健康检查跟随 leader。
- 身份：复用 homelab 的 SPIRE Server 和 `ddupan.top` trust domain，不建第二个 trust root；Kata guest
  必须使用 guest 内的 SPIRE agent。ESO 经独立的 `auth/kubernetes-sandbox` 登录 Bao。
- 监控只覆盖 Kubernetes 与 workload（kubelet/cAdvisor、kube-state-metrics）；**禁止在 LXC 内部署 node_exporter**
  （`/proc/stat` 是宿主视图）。
- `ci-vm` executor 规格固定 2 CPU / 3 GiB，是嵌套 kind 的容量下限。

## 出问题时

- 只读验收：`infrastructure/sandbox-cluster/ansible/verify.yml`（需要运行时数据库凭据，见源码 README）。
- OpenSandbox 不收敛：查 `flux-system/opensandbox` 与 `opensandbox-system/opensandbox` 是否 Ready；
  2026-11 曾因 commit pin 跨过上游 chart 目录重构而 11 天不收敛，现已改跟 release tag。
- K3s API 不通：先查 Ayatori LB `sandbox/k8s` 与 VyOS 的 BGP 路由，再查节点。

## 运维入口

- 源码：[infrastructure/sandbox-cluster/](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/sandbox-cluster)、
  [clusters/sandbox/](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/clusters/sandbox)、
  `platform/sandbox-*`。
- 部署：`ansible-playbook site.yml`（全量）、`k3s.yml`、`flux.yml`；SPIRE 跨集群 bootstrap 用 `spire-bootstrap.yml`。
- 秘密：数据库凭据 Bao `kv/infra/sandbox-postgresql`；etcd 客户端证书每日由 laptop 上的
  `homelab-sandbox-renew.timer` 续签。
- 备份恢复：Kata 数据随 Pod 删除；K3s datastore 没有成文的备份方案。

## 当前状态与证据

- 2026-09-17 声明集群（Ansible），之后按阶段经 Flux 引入监控、SPIRE、Kata、ESO、OpenSandbox。
- 2026-11-03 K3s API / OpenSandbox API 与 sandbox PostgreSQL 入口从 VyOS HAProxy 迁到 Ayatori LoadBalancer
  （[8b90ee5](https://git.ddupan.top/panxiao81/homelab-infra/commit/8b90ee59956e3fb054a2b5f37f581bd80caccc96)）。
- OpenSandbox 版本 `release-1.2.1`。
