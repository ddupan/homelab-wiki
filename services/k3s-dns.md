---
title: k3s 集群 DNS 使用说明
lifecycle: unknown
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - homelab-infra `platform/k3s/coredns-custom.yaml`、`Corefile.desired`
  - https://git.ddupan.top/panxiao81/homelab-infra/commit/219acc4
watch:
  - homelab-infra:platform/k3s/
  - homelab-infra:infrastructure/dns/generate.py
  - homelab-infra:infrastructure/dns/records.yml
---

# k3s 集群 DNS

本页说明 Pod 的 DNS 解析路径，配置在 homelab-infra `platform/k3s/Corefile.desired` 与
`coredns-custom.yaml`。LAN 主机的解析路径（DHCP → Blocky）不同，见 [LAN DNS](lan-dns.md)。

## 应用如何使用

Pod 通常通过 Kubernetes DNS 解析 Service。跨 namespace 使用完整地址，例如
`smtp-relay.smtp-relay.svc.cluster.local`；同 namespace 的短名称按 Pod DNS 搜索域处理。
这类集群内部名称不是远程客户端的公共入口。（旧例 `shared-postgresql-rw.shared-db.svc` 属于已退役的 CNPG
共享集群，见 homelab-infra `archive/cnpg-shared-postgresql/RETIRED.md`。）

集群内访问 iam-login 时继续使用 `https://sso.ddupan.top` 等原有 URL，
避免把 OIDC issuer、证书名称改成 IP 来绕过解析问题。Gitea 已迁到 OCI，`git.ddupan.top` 是
Cloudflare 上的公网记录，Pod 走普通上游解析，CoreDNS 不再为它做分流（见 [Gitea](gitea.md)）。

受权排障时，可在已有且具备 `nslookup` 的应用容器中执行以下只读查询：

```bash
nslookup kubernetes.default.svc.cluster.local.
nslookup dc1.ad.ddupan.top.
nslookup sso.ddupan.top.
nslookup grafana.lab.ddupan.top.
```

末尾的点表示绝对域名，用于减少搜索域扩展对诊断的干扰。
四个查询分别覆盖集群 Service、AD 域、split-horizon 入口（应得 `192.168.10.127`）和 `lab.ddupan.top`。
DNS 成功只证明解析路径，不证明应用认证和业务请求成功。

## 分流规则

| 名称范围 | 处理方式 |
|---|---|
| `cluster.local` 与集群反向记录 | CoreDNS Kubernetes 插件处理 |
| `ad.ddupan.top` | 直接转发 Samba AD DNS `192.168.10.5` |
| `sso.ddupan.top`、`spire-oidc.ddupan.top` | A 记录返回 Envoy LAN 地址 `192.168.10.127`；AAAA 返回无数据（由 `infrastructure/dns/records.yml` 经 `generate.py` 生成） |
| `lab.ddupan.top` | 转发 Blocky `192.168.10.127`，由其后的 PowerDNS 权威解析（2026-10-04 前曾本地返回 NXDOMAIN） |
| `tail7e769.ts.net` | 本地返回 NXDOMAIN，阻止 Tailscale 搜索域排列请求挂在上游 |
| 其余请求 | 默认 Corefile 转发至 `/etc/resolv.conf` |

最后一项的上游由节点的 resolver 文件决定。
对被本地拒绝的后缀新增用途前，先审查这条规则，不要在外部 DNS 增加记录后就假定 Pod 能解析。
`lab.ddupan.top` 同时在节点搜索列表中，`ndots:5` 下短外部名会先试 `<name>.lab.ddupan.top`；
pdns 在本地快速应答且有缓存，因此这些排列无害。

## 缓存和修改入口

`Corefile.desired` 的默认 server block 配置 `cache 30` 与 `serve_stale 1h immediate`，
允许在该规则覆盖范围内暂用过期缓存条目；其他独立 server block 不自动继承这条缓存规则。
因此修改 DNS 记录后，缓存结果可能与权威记录暂时不同。
语义见 [CoreDNS cache](https://coredns.io/plugins/cache/)。

`coredns-custom.yaml` 声明 `kube-system/coredns-custom`，由 Corefile 的
`import /etc/coredns/custom/*.server` 加载，`reload` 插件使修改无需重启 CoreDNS 即生效。
两个文件都不在 Flux 目录中，需手工 apply；其中 split-horizon server blocks 由
`infrastructure/dns/generate.py` 生成。k3s 每次重启都会覆盖 CoreDNS 主 Corefile 中手工加的
`serve_stale`，重启后按 `Corefile.desired` 恢复。不要整份替换 CoreDNS 配置来修一个域名。

故障定位先区分集群 Service 解析、AD 转发、固定分流、默认上游和客户端搜索域。
依赖包括 CoreDNS、Kubernetes API、网络、Samba AD DNS、Blocky/PowerDNS 及默认上游；
split-horizon 名字的业务可达性还依赖 Envoy 和各自后端。
