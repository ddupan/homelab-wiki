---
title: Cinc（Chef）节点配置
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/chef/README.md
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/chef/policies
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/chef/ansible/inventory/hosts.yml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/.gitea/workflows/chef.yml
  - https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/CLAUDE.md
  - https://git.ddupan.top/panxiao81/homelab-infra/pulls/790
  - https://git.ddupan.top/panxiao81/homelab-cookbooks
watch:
  - homelab-infra:infrastructure/chef/
  - homelab-infra:.gitea/workflows/chef.yml
  - homelab-infra:platform/observability/metrics/scrapes/cinc-nodes.yaml
  - homelab-infra:platform/spire/spire-node-aliases.yaml
  - homelab-cookbooks:cookbooks/
---

# Cinc（Chef）节点配置

## 它解决什么问题

Cinc（Chef 的开源构建）负责一批 Linux 节点的主机配置：etcd、Ayatori 控制面与计算节点、
LoadBalancer 主机、Samba AD DC。**没有 Cinc Server**：每个节点有一份 policy 和提交到 Git 的 lock，
`converge.py` 经 SSH 推送并以 `cinc-client -z` 本地收敛。cookbook 代码在
[homelab-cookbooks](https://git.ddupan.top/panxiao81/homelab-cookbooks)，homelab-infra 只放部署声明。

## 从哪里使用

- 改节点配置：在 homelab-infra 提 PR 修改 `infrastructure/chef/policies/<policy>.rb` 与对应 lock。
  CI（`.gitea/workflows/chef.yml`）对受影响节点 why-run 并把汇总贴成 PR 评论；**合并即 apply**。
- 手动：`infrastructure/chef/converge.py`（需要 `uv`、docker，以及能 SSH 到节点的 key/agent 或 Bao 签发的证书）。
- 节点由 DNS 名（`lab.ddupan.top`）寻址，见 `ansible/inventory/hosts.yml`。

## 第一次使用

只读预览所有节点会发生什么变化：

```bash
cd infrastructure/chef
./converge.py --why-run
```

`--why-run` 不改动任何节点；汇总表列出每个节点将更新的 resource 数。对已收敛的节点应全部为 0。
apply 一台或一个 policy：`./converge.py -l etcd-pve1`、`./converge.py -l loadbalancer-prod`。

## 日常操作与限制

- 升级 cookbook：改 policy 里的 `cookbook '<name>', '= x.y.z'`，用 Cinc Workstation 容器执行
  `cinc update <policy>.rb` 重新生成 lock 后提交。cookbook 从 SeaweedFS 上的静态 supermarket
  （`default_source :supermarket, 'https://s3.lab.ddupan.top/chef-supermarket'`）按版本精确固定，
  发布方式见 homelab-cookbooks README。
  不要用 `cinc install`：已有 lock 时它不重新解析。
- 部署时才确定的值（如 LB 的 AS、VIP 段、agent 版本）写在 policy 里，不写进 cookbook。
- 客户端缺失或版本不符时，执行器自己下载 `.deb` 经 SSH 安装，节点无需外网；版本见
  `ansible/inventory/group_vars/all.yml` 的 `cinc_version`。
- 漂移检测：`homelab_base` 在每个节点装每日 why-run timer，结果触发 `CincDriftDetected` 告警。
- 新节点：加入 `ansible/inventory/hosts.yml`、`known_hosts`（CI 不做 TOFU）、
  `platform/observability/metrics/scrapes/cinc-nodes.yaml`，并在 `platform/spire/spire-node-aliases.yaml` 加 node alias。

### 一次性操作（不在 CI 中）

- **SPIRE enrollment**：节点首次 apply 后运行 `ansible/enroll.yml -l <host>`（需要 `BAO_TOKEN`，
  laptop 上 SPIFFE `local-development` 登录即可）；之后证书由节点每日自行续期。
- **Ayatori agent join**（compute、loadbalancer 节点）：`ansible/join.yml`，批准 CSR 即准入。

## 现有 policy 与节点

| policy | 节点 | 加入日期 |
|---|---|---|
| `etcd-pve1` / `etcd-pve2` / `etcd-pve3` | 对应 etcd LXC（[共享 etcd](shared-etcd.md)） | 2026-10-09 / 2026-10-09 / 2026-11-04 |
| `ayatori-dev` / `ayatori-prod` | Ayatori 控制面（[Ayatori](ayatori.md)） | 2026-11-03 |
| `samba-dc` | dc1（[Samba AD](samba-ad.md)） | 2026-11-04 |
| `compute-dev` | compute-dev-1..3（暂只有节点基线，Ayatori 计算后端 release 后再加 `homelab_compute`） | 2026-11-13 |
| `loadbalancer-prod` / `loadbalancer-dev` | lb-prod-1/2、lb-dev-1/2（[LB 主机](ayatori-loadbalancer.md)） | lb-agent 版 policy 2026-11-03 |

## 出问题时

- 汇总表里某节点失败：执行器以主机前缀输出日志，任一节点失败即非零退出。
- `CincDriftDetected`：在该节点上看最后一次 apply 的 policy（`/var/lib/homelab-cinc/policy`）的 why-run 结果，
  确认是手工改动还是 cookbook 变化，再决定 apply 还是修代码。
- “empty run list”成功但 0 更新：Cinc 依据 `$PWD` 找配置，执行器显式传 `-c` 并对此报错。

## 运维入口

- 源码：[infrastructure/chef/](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/chef)、
  [homelab-cookbooks](https://git.ddupan.top/panxiao81/homelab-cookbooks)。
- CI 的 SSH：每个 job 用 SPIFFE 身份（role `ci-converge`）向 [OpenBao](openbao.md) 签 30 分钟证书。
- 单元测试：`uv run --with pyyaml --with pytest python -m pytest infrastructure/chef/test_converge.py`。
- 节点无状态配置可由 policy 重建；节点数据的备份属于各服务。

## 当前状态与证据

- 首个节点 etcd-pve1 于 2026-10-09 加入；cookbook 于 2026-11-17 改从 Gitea registry 取
  （[#790](https://git.ddupan.top/panxiao81/homelab-infra/pulls/790)），之后又改为 SeaweedFS 静态 supermarket。
