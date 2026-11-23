---
title: 为新服务配置 LAN HTTPS 入口
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
sources:
  - homelab-infra platform/envoy-gateway/README.md、gateway.yaml
  - homelab-infra platform/cert-manager/certificate-wildcard-lab.yaml
  - homelab-infra platform/external-dns/README.md、infrastructure/dns/README.md
  - homelab-infra apps/seaweedfs/securitypolicy-admin.yaml、networkpolicy-admin.yaml
  - homelab-infra apps/iam-login/terraform/clients.tf、apps/iam-login/README.md
  - homelab-infra platform/observability/metrics/probes/probes.yaml、apps/homepage/、apps/poweradmin/httproute.yaml
  - homelab-infra clusters/homelab/README.md、CLAUDE.md
watch:
  - homelab-infra:platform/envoy-gateway/README.md
  - homelab-infra:platform/envoy-gateway/gateway.yaml
  - homelab-infra:platform/cert-manager/certificate-wildcard-lab.yaml
  - homelab-infra:platform/external-dns/README.md
  - homelab-infra:infrastructure/dns/README.md
  - homelab-infra:apps/seaweedfs/securitypolicy-admin.yaml
  - homelab-infra:apps/seaweedfs/networkpolicy-admin.yaml
  - homelab-infra:apps/iam-login/terraform/clients.tf
  - homelab-infra:apps/iam-login/README.md
  - homelab-infra:platform/observability/metrics/probes/probes.yaml
  - homelab-infra:apps/homepage/
  - homelab-infra:apps/poweradmin/httproute.yaml
  - homelab-infra:clusters/homelab/README.md
  - homelab-infra:infrastructure/cloudflared/terraform/README.md
---

# 为新服务配置 LAN HTTPS 入口

普通 LAN Web 服务使用 `your-app.lab.ddupan.top`，复用共享 Envoy Gateway 的 `https-lab` listener 和通配符证书，
DNS 记录由 external-dns 自动发布。本指南串联应用 Service、路由、DNS、认证、监控与 GitOps；示例不会自动创建任何对象。

## 接入前明确应用参数

准备应用 namespace、Service 名称与 **Service port**、域名、访问人群及认证方式。
先让应用及其 Service 在集群内可用；需要秘密或持久存储时，分别参考
[External Secrets](../services/external-secrets.md) 和 [OpenEBS](../services/openebs.md)。

本例约定 namespace 和 Service 均为 `your-app`，Service port 为 `8080`。
这些都是占位值，须替换为实际配置。HTTPRoute 不负责部署应用、创建 namespace 或授予应用权限。

## 1. 复用现有证书与 listener

共享入口为 `envoy-gateway-system/eg`（`platform/envoy-gateway/gateway.yaml`），地址 `192.168.10.127`。
新服务绑定 `https-lab` listener（hostname `*.lab.ddupan.top`），其证书 Secret
`envoy-gateway-system/wildcard-lab-ddupan-top-tls` 由 cert-manager 按
`platform/cert-manager/certificate-wildcard-lab.yaml` 管理。

| 域名场景 | 接入选择 |
|---|---|
| `your-app.lab.ddupan.top`（新服务） | 复用 `https-lab` listener 与 `*.lab` 通配符证书 |
| `*.ad.ddupan.top`（旧名） | `https` listener 只为迁移期旧名保留；**不要再新增 `ad.ddupan.top` 名字** |
| `sso.ddupan.top`、`spire-oidc.ddupan.top`、`spire-bundle.lab.ddupan.top` | 已有专用 listener `https-sso`、`https-spire-oidc`、`tls-spire-bundle`，不复用于新服务 |
| 更深的域名或其他域 | 单独设计证书 SAN 与匹配的 listener，不能套用本例 |

TLS 通配符只覆盖一层子域；证书名称和 listener hostname 是两个需要同时满足的条件。
一个 listener 只有一个 hostname，所以 `lab` 与 `ad` 两个通配符各有自己的 listener。
新 LAN 服务不需要复制私钥、创建第二个 Gateway 或重新安装 cert-manager。

现有通配符通过 `ClusterIssuer/letsencrypt` 与 Cloudflare DNS-01 签发，一张通配符只在 CT 日志中出现一次，
避免每个服务名进入公开日志。DNS-01 不要求业务端口对公网开放，详见
[cert-manager DNS-01](https://cert-manager.io/docs/configuration/acme/dns01/)。
`bao-acme` 是内部 CA 的另一个选择，客户端需信任内部 CA；它不是无需配套调整的通配符替代品。

## 2. 在应用 namespace 声明 HTTPRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: your-app
  namespace: your-app
  annotations:
    # 浏览器使用的服务才加；见第 5 步。
    gethomepage.dev/enabled: "true"
    gethomepage.dev/name: "Your App"
    gethomepage.dev/group: "平台"
    gethomepage.dev/description: "一句话用途"
    gethomepage.dev/href: "https://your-app.lab.ddupan.top/"
spec:
  parentRefs:
    - name: eg
      namespace: envoy-gateway-system
      sectionName: https-lab
  hostnames:
    - your-app.lab.ddupan.top
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: your-app
          port: 8080
```

现成的最小参考是 `apps/homepage/httproute.yaml`（只挂 `https-lab`）；带 homepage 注解的参考是
`apps/poweradmin/httproute.yaml`（迁移期同时挂 `https` 与 `https-lab`，新服务只需后者）。

本例后端 Service 与路由同 namespace；`8080` 必须是 Service 暴露的端口，不直接照搬容器端口。
跨 namespace 后端引用还需目标 namespace 的 ReferenceGrant，不能只增加一个 namespace 字段就认为授权完成。
共享 Gateway 的 `allowedRoutes` 允许其他 namespace 挂载路由，但这不等于应用已经得到用户认证保护。

需要 HTTP→HTTPS 跳转时，为同一 hostname 增加独立 HTTPRoute，绑定 `sectionName: http`，
使用 `RequestRedirect` 的 `scheme: https`、`port: 443` 和适当状态码，不配置业务 backend。
HTTPS 路由本身不会自动生成跳转。规则语义参考
[Gateway API 跳转指南](https://gateway-api.sigs.k8s.io/guides/user-guides/http-redirect-rewrite/)。
保留 HTTP listener 的 ACME 用途，不为单个应用替换整个 listener。

## 3. DNS：external-dns 自动发布

不需要手写 DNS 记录。HTTPRoute 挂在 `https-lab` 上、主机名位于 `lab.ddupan.top` 下时，external-dns
在约一分钟内把 A 记录（指向 Gateway `192.168.10.127`）写进 PowerDNS，并加 TXT 归属标记；
路由删除时它也会删除自己的记录（`platform/external-dns/README.md`）。

- **不要**再改 `infrastructure/dns/records.yml` 或跑 Samba Ansible 加 A 记录：`records.yml` 现只管
  split horizon，`ad.ddupan.top` 不再接收新名字（`infrastructure/dns/README.md`）。
- 主机名已被 Terraform（`infrastructure/dns/terraform/hosts.tf`）占用时，external-dns 跳过而不接管，需先理清归属。
- pdns provider 没有 dry-run；合并后看 external-dns 日志确认写入。

LAN（经 Blocky）、Pod（CoreDNS 转发 Blocky）与 tailnet（MagicDNS split DNS）都能解析 `lab.ddupan.top`；
路径不同，排障时分别检查，见 [LAN DNS](../services/lan-dns.md) 与 [k3s 集群 DNS](../services/k3s-dns.md)。

## 4. 按应用选择认证

Gateway **没有 forward-auth**：Authelia 及其 forward-auth 已于 2026-10-11 退役
（`platform/envoy-gateway/README.md`），不要寻找或复制旧的 Authelia ReferenceGrant、规则或 NetBox 策略。

| 应用类型 | 接入方式 |
|---|---|
| 自带登录、支持 OIDC 的 Web 应用 | 应用自己作为 [iam-login](../services/iam-login.md)（`sso.ddupan.top`）的 OIDC client 登录，并自行把 AD 组映射为应用角色 |
| 完全没有登录的应用（如管理 UI） | 在网关加 Envoy Gateway `SecurityPolicy`（对 iam-login 做 `oidc`，再按 `groups` claim 授权）+ 仅允许 Envoy 访问的 NetworkPolicy |
| API、Git、机器客户端 | 使用服务支持的认证协议，避免浏览器登录跳转截获协议请求 |
| 只是链接列表、无敏感内容 | 可不加登录，在路由文件注释原因（例：`apps/homepage/httproute.yaml`） |

OIDC client 在 homelab-infra `apps/iam-login/terraform/clients.tf` 声明（`homelab_oidc_client`），
由 Terraform CD 合并后 apply；client secret 只在创建与轮换时可得，由同一 root 写入 OpenBao 供应用读取
（`apps/iam-login/README.md`）。授权统一授予 AD 组 `platform-admins`，不再新建每个应用的管理员组。

**无登录应用的网关登录**：复制 `apps/seaweedfs/securitypolicy-admin.yaml` 与 `networkpolicy-admin.yaml`，
逐项替换 route 名、namespace、client ID、回调 URL、cookie 名、Pod selector 和端口。必须保留：

- `provider` 中显式写出的 `authorizationEndpoint` 与 `tokenEndpoint`。缺少它们时 Envoy Gateway 只拉一次
  discovery 且不重试，一次失败就会静默丢掉 OIDC filter：策略显示 `Accepted=False`，用户只看到
  “Jwt is missing”，没有登录跳转（2026-10-31 实际发生，见该文件注释与 homelab-infra `CLAUDE.md`）。
- `scopes` 含 `groups`，以及 `authorization.defaultAction: Deny` 加 `groups` claim 规则；只登录成功不够。
- NetworkPolicy：应用 HTTP 端口只接受 Envoy 数据面 Pod 的流量，否则集群内任何 Pod 都能绕过登录。

不使用 oauth2-proxy。SPIFFE workload 接入按[机器身份原则](../services/spire.md)设计，服务自行授权；
HTTPS 证书和 HTTPRoute 都不会自动替代业务认证。

## 5. 健康探测与首页卡片

两项都是 `platform/envoy-gateway/README.md`「Adding a service」中的必需步骤：

1. **blackbox 探测**：把服务的健康端点加到 `platform/observability/metrics/probes/probes.yaml` 的
   `lan-https`。端点必须不经跳转直接返回 `200`（受登录保护的首页通常不行）。没有它，路由或后端坏了无人发现，
   `LanEndpointDown` 也没有目标。可先用集群内 blackbox 试探：
   `kubectl -n monitoring port-forward svc/blackbox-exporter 9115` 后访问
   `localhost:9115/probe?module=http_2xx&target=https://<host>/<path>`，看 `probe_success`。
   **下线**服务时同时删除探测行，否则残留目标会告警。
2. **homepage 卡片**（浏览器会打开的服务）：在 HTTPRoute 上加 `gethomepage.dev/*` 注解，照抄
   `apps/poweradmin/httproute.yaml`。`href` 实际必填：缺少时 Homepage 从 `hostnames[0]` 与
   `rules[0].matches[0]` 推导 URL，多数旧路由会得到 `ad` 旧名，没有 `matches` 的路由还会让它崩溃
   （`apps/homepage/README.md`）。

## 6. 纳入部署入口并验收

将路由和配套策略加入应用 Kustomization 或 chart values，并确认应用由哪个 Flux Kustomization 管理。
只新建 YAML 文件不会使它自动部署。独立新应用还需 namespace 与集群 reconciliation 入口，
按 `clusters/homelab/README.md` 审查；不要为接入一个应用开启全局 prune。

先本地渲染并检查 diff，合并后由已有 GitOps 流程交付。上线后分层验证：

1. Flux 已同步目标 revision；后端 Service 有可用 endpoint。
2. Gateway listener 可用，HTTPRoute 对目标 parent 的 `Accepted`、`ResolvedRefs` 为 True；
   有 SecurityPolicy 时其状态也为 `Accepted=True`。
3. 从相应客户端解析新名称（PowerDNS 已有 external-dns 写入的记录），并检查证书名称与信任链。
4. 验证登录、应用权限及需要支持的 API/机器客户端，不能只检查首页 200。
5. blackbox 目标 `probe_success` 为 1。

若需分开验证入口与 DNS，可用以下诊断请求，域名仍保留在 TLS SNI 与 Host 中：

```bash
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' \
  --resolve your-app.lab.ddupan.top:443:192.168.10.127 \
  https://your-app.lab.ddupan.top/
```

该命令绕过客户端 DNS，不是 DNS 验收；不加 `-k` 绕过证书校验。
响应是否符合预期取决于应用，受保护页面可能返回登录跳转。

## LAN 入口与公网发布的边界

本指南只完成 LAN HTTPS 路径；`*.lab.ddupan.top` 只在 LAN/Tailscale 内解析。公开可信证书不意味着服务已开放公网。
公网发布还需单独审查 Cloudflare DNS、Tunnel 路由、访问控制与应用外部 URL，
入口为 `infrastructure/cloudflared/terraform/README.md`；不要从已有域名复制 Tunnel 设置就宣称完成发布。

## 已不适用的旧模板

旧版本中引用的 `apps/netbox/*`（2026-10-04 删除）与 `apps/authelia/*`（2026-10-11 随 Authelia 退役）已不存在；
Gitea 已迁到 OCI，不再经本 Gateway 发布。`apps/http-echo/httproute.yaml` 是已排除出 Kustomization 的历史 Contour 示例，
`archive/traefik/` 也不是当前接入模板；不要因文件存在就直接应用。
