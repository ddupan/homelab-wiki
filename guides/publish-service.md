---
title: 为新服务配置 LAN HTTPS 入口
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# 为新服务配置 LAN HTTPS 入口

普通 LAN Web 服务使用 `your-app.ad.ddupan.top`，复用共享 Envoy Gateway 和通配符证书。
本指南串联应用 Service、路由、DNS、认证与 GitOps；示例不会自动创建任何对象。
本轮只读仓库与上游资料，未查询现场、签发证书或发布服务。

## 接入前明确应用参数

准备应用 namespace、Service 名称与 **Service port**、域名、访问人群及认证方式。
先让应用及其 Service 在集群内可用；需要秘密或持久存储时，分别参考
[External Secrets](../services/external-secrets.md) 和 [OpenEBS](../services/openebs.md)。

本例约定 namespace 和 Service 均为 `your-app`，Service port 为 `8080`。
这些都是占位值，须替换为实际配置。HTTPRoute 不负责部署应用、创建 namespace 或授予应用权限。

## 1. 复用现有证书与 listener

共享入口为 `envoy-gateway-system/eg`，普通 LAN 域名绑定 `https` listener。
其证书 Secret 为 `envoy-gateway-system/wildcard-ad-ddupan-top-tls`，由 cert-manager 管理。

| 域名场景 | 接入选择 |
|---|---|
| `your-app.ad.ddupan.top` | 复用 `https` listener 与通配符证书 |
| `auth.ddupan.top`、`git.ddupan.top` | 已有各自的 `https-auth`、`https-git` listener |
| 更深的域名或其他域 | 单独设计证书 SAN 与匹配的 listener，不能套用本例 |

TLS 通配符只覆盖一层子域。证书包含 `ad.ddupan.top` SAN 也不表示现有 listener 会接收这个 apex；
证书名称和 listener hostname 是两个需要同时满足的条件。
新 LAN 服务不需要复制私钥、创建第二个 Gateway 或重新安装 cert-manager。

现有通配符通过 `ClusterIssuer/letsencrypt` 与 Cloudflare DNS-01 签发。
DNS-01 不要求业务端口对公网开放；自检需保留现有公共递归 resolver 设置，避免内部 AD 视图看不到公开 TXT。
详见 [cert-manager DNS-01](https://cert-manager.io/docs/configuration/acme/dns01/)。
`bao-acme` 是内部 CA 的另一个选择，客户端需信任内部 CA；它不是无需配套调整的通配符替代品。

## 2. 在应用 namespace 声明 HTTPRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: your-app
  namespace: your-app
spec:
  parentRefs:
    - name: eg
      namespace: envoy-gateway-system
      sectionName: https
  hostnames:
    - your-app.ad.ddupan.top
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: your-app
          port: 8080
```

本例后端 Service 与路由同 namespace；`8080` 必须是 Service 暴露的端口，不直接照搬容器端口。
跨 namespace 后端引用还需目标 namespace 的 ReferenceGrant，不能只增加一个 namespace 字段就认为授权完成。
共享 Gateway 的 `allowedRoutes` 允许其他 namespace 挂载路由，但这不等于应用已经得到用户认证保护。

需要 HTTP→HTTPS 跳转时，为同一 hostname 增加独立 HTTPRoute，绑定 `sectionName: http`，
使用 `RequestRedirect` 的 `scheme: https`、`port: 443` 和适当状态码，不配置业务 backend。
HTTPS 路由本身不会自动生成跳转。规则语义参考
[Gateway API 跳转指南](https://gateway-api.sigs.k8s.io/guides/user-guides/http-redirect-rewrite/)。
保留 HTTP listener 的 ACME 用途，不为单个应用替换整个 listener。

## 3. 在受管 DNS 清单增加名称

工作区的声明入口为 `infrastructure/dns/records.yml`，在 `homelab_dns.samba.records`
现有列表中增加以下 RRset，不能用这个片段覆盖原列表：

```yaml
- zone: ad.ddupan.top
  name: your-app
  type: A
  values:
    - 192.168.10.127
```

该地址来自共享 Envoy Gateway 的现有记录。Samba Ansible 的 `provision-dc.yml` 已引用该清单，
DNS task 消费 `homelab_dns.samba.records`；旧 README 中增加 `samba_ad_extra_a_records` 的步骤不再作为本页入口。
相关 DNS 清单与任务存在工作区改动，正式合并来源仍需补全，不能认定任意远端 checkout 都已包含它们。

维护者先审查针对 DNS 的 Ansible check/diff，再按既有流程应用。受管 RRset 的 exact 语义可能移除同名同类型的其他值，
因此应检查完整记录集合；不要遍历清理 Samba 自动生成的 AD/Kerberos 记录。

[LAN DNS](../services/lan-dns.md) 与 [Pod DNS](../services/k3s-dns.md) 的路径不同，
新增名称后分别检查所需视图。LAN 已使用 Blocky，不采用旧 DNS README 中“尚未成为正式 resolver”的历史表述。

## 4. 按应用选择认证

| 应用类型 | 接入方式 |
|---|---|
| 已支持 OIDC 的 Web 应用 | 按应用文档接入 Authelia，配置 client、回调地址与应用内权限 |
| 信任反向代理身份头的应用 | 配套 Envoy SecurityPolicy、Authelia 规则及阻止绕过网关的网络策略 |
| API、Git、机器客户端 | 使用服务支持的认证协议，避免浏览器登录跳转截获协议请求 |

Gitea 使用原生登录/OIDC 和 Git token，因此其路由没有套用 NetBox 的 forward-auth。
SPIFFE workload 接入按[机器身份原则](../services/spire.md)设计，服务自行授权；
HTTPS 证书和 HTTPRoute 都不会自动替代业务认证。

forward-auth 的现有参考为 `apps/netbox/securitypolicy.yaml` 与 `networkpolicy.yaml`，另需协调：

- `apps/authelia/referencegrant-extauth.yaml`：目标 namespace 授权新的 SecurityPolicy 来源。
- `apps/authelia/values.yaml`：目标域名及访问群组规则。
- 应用配置：信任哪些身份头，以及如何映射用户权限。

复制前逐项替换 route 名、namespace、Pod selector 和端口。现有 Authelia Service port 是 `80`，
不是容器 `9091`；`headersToBackend` 位于 `extAuth.http`，并由可信结果覆盖客户端同名头。
保留 `failOpen: false`，同时限制直接访问后端的路径。NetworkPolicy 的 probe 例外与节点地址需按应用核对，
不能机械复制 NetBox 的节点白名单。

## 5. 纳入部署入口并验收

将路由和配套策略加入应用 Kustomization 或 chart values，并确认应用由哪个 Flux Kustomization 管理。
只新建 YAML 文件不会使它自动部署。独立新应用还需 namespace 与集群 reconciliation 入口，
按 `clusters/homelab/README.md` 审查；不要为接入一个应用开启全局 prune。

先本地渲染并检查 diff，合并后由已有 GitOps 流程交付。获得现场检查授权后，分层验证：

1. Flux 已同步目标 revision；后端 Service 有可用 endpoint。
2. Gateway listener 可用，HTTPRoute 对目标 parent 的 `Accepted`、`ResolvedRefs` 为 True。
3. 从相应客户端解析新名称，并检查证书名称与信任链。
4. 验证登录、应用权限及需要支持的 API/机器客户端，不能只检查首页 200。

若需分开验证入口与 DNS，可在已授权的客户端使用以下诊断请求，域名仍保留在 TLS SNI 与 Host 中：

```bash
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' \
  --resolve your-app.ad.ddupan.top:443:192.168.10.127 \
  https://your-app.ad.ddupan.top/
```

该命令绕过客户端 DNS，不是 DNS 验收；不加 `-k` 绕过证书校验。
响应是否符合预期取决于应用，受保护页面可能返回登录跳转。

## LAN 入口与公网发布的边界

本指南只完成 LAN HTTPS 路径。公开可信证书不意味着服务已开放公网。
公网发布还需单独审查 Cloudflare DNS、Tunnel 路由、访问控制与应用外部 URL，
入口为 `infrastructure/cloudflared/terraform/README.md`；不要从已有域名复制 Tunnel 设置就宣称完成发布。

## 来源与维护

homelab-infra：`platform/cert-manager/README.md`、`certificate-wildcard-ad.yaml`，
`platform/envoy-gateway/README.md`、`gateway.yaml`，`infrastructure/dns/`，
`infrastructure/samba-ad/ansible/`，`apps/netbox/`，`apps/authelia/referencegrant-extauth.yaml`，
`apps/gitea/httproute.yaml` 与 `clusters/homelab/README.md`。

`apps/http-echo/httproute.yaml` 是已排除出 Kustomization 的历史 Contour 示例，
`archive/traefik/` 也不是当前接入模板；不要因文件存在就直接应用。
上述源码 README 的旧描述尚待同步，本页按实际所读配置与维护者已经确认的结论整理。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#publish-service)。
