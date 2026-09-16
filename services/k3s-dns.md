---
title: k3s 集群 DNS 使用说明
lifecycle: unknown
evidence: configuration
last_reviewed: 2026-09-16
last_verified: null
---

# k3s 集群 DNS

本页说明 Pod 的 DNS 使用路径，依据 homelab-infra `platform/k3s/Corefile.desired` 与
`coredns-custom.yaml`。这些文件是配置意图与历史故障处理记录，未现场确认是否与运行配置完全一致。
LAN 主机通过 DHCP 使用 Blocky/路由器的现状见 [LAN DNS](lan-dns.md)，不能据此推导所有 Pod 的转发链。

## 应用如何使用

Pod 通常通过 Kubernetes DNS 解析 Service。跨 namespace 使用完整地址，例如
`shared-postgresql-rw.shared-db.svc.cluster.local`；同 namespace 的短名称按 Pod DNS 搜索域处理。
这类集群内部名称不是远程客户端的公共入口。

集群内访问 Authelia 或 Gitea 时继续使用 `auth.ddupan.top`、`git.ddupan.top` 的原有 URL，
避免把 OIDC issuer、证书名称或 Git remote 改成 IP 来绕过解析问题。

受权排障时，可在已有且具备 `nslookup` 的应用容器中执行以下只读查询：

```bash
nslookup kubernetes.default.svc.cluster.local.
nslookup dc1.ad.ddupan.top.
nslookup auth.ddupan.top.
nslookup git.ddupan.top.
```

末尾的点表示绝对域名，用于减少搜索域扩展对诊断的干扰。
四个查询分别覆盖集群 Service、AD 域和两个分流入口；本轮没有执行，也没有为此创建调试 Pod。
DNS 成功只证明解析路径，不证明应用认证和业务请求成功。

## 文件中声明的分流

| 名称范围 | 配置意图 |
|---|---|
| `cluster.local` 与集群反向记录 | CoreDNS Kubernetes 插件处理 |
| `ad.ddupan.top` | 直接转发 Samba AD DNS `192.168.10.5` |
| `auth.ddupan.top`、`git.ddupan.top` | A 记录返回 Envoy LAN 地址 `192.168.10.127`；AAAA 返回无数据 |
| `lab.ddupan.top`、`tail7e769.ts.net` | 本地返回 NXDOMAIN，阻止历史搜索域排列请求继续转发 |
| 其余请求 | 默认 Corefile 转发至 `/etc/resolv.conf` |

最后一项的实际上游由运行环境的 resolver 文件决定。本轮没有读取现场文件，
不能将源码注释中的历史路由器上游描述当成今天所有节点的 resolver 配置。
对被本地拒绝的后缀新增用途前，应审查这一历史规则，而不是直接在外部 DNS 增加记录后假定 Pod 能解析。

## 缓存和修改入口

`Corefile.desired` 的默认 server block 配置 `cache 30` 与 `serve_stale 1h immediate`，
允许在该规则覆盖范围内暂用过期缓存条目；其他独立 server block 不自动继承这条缓存规则。
因此修改 DNS 记录后，缓存结果可能与权威记录暂时不同。
语义见 [CoreDNS cache](https://coredns.io/plugins/cache/)。

`coredns-custom.yaml` 声明 `kube-system/coredns-custom`，由 Corefile 的 custom import 使用。
`Corefile.desired` 的文件名本身不证明它已由 Flux 管理或已经应用。
变更前先确认该对象的管理入口，再审查影响范围；不要整份替换 CoreDNS 配置来修一个域名。

故障定位先区分集群 Service 解析、AD 转发、固定分流、默认上游和客户端搜索域。
依赖包括 CoreDNS、Kubernetes API、网络、Samba AD DNS 及默认上游；
Authelia/Gitea 的业务可达性还依赖 Envoy 和各自后端。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#k3s-dns)。
