---
title: 证书、秘密同步与 GitOps 监控
last_reviewed: 2026-09-25
---

# 证书、秘密同步与 GitOps 监控

采集与规则由 observability Flux Kustomization 管理，以 ServiceMonitor、PodMonitor 和
PrometheusRule 声明；VM Operator 转换后交给 vmagent/vmalert。
通知和静默入口见 [Grafana](../services/grafana.md#从告警进入-grafana)。

## 采集与阈值

| 对象 | 采集 | 告警 |
|---|---|---|
| cert-manager controller | ServiceMonitor，:9402，job=cert-manager | Certificate Ready=True 的值为 0 持续 15m；到期不足 7 天且至少 1 天 warning 15m；不足 1 天（含已过期）critical 5m |
| ESO 三个组件 | PodMonitor，:8080，以各组件名称为 job | ExternalSecret Ready=True 值为 0 持续 10m；ClusterSecretStore 同条件 5m critical |
| Flux 四个 controller | PodMonitor，:8080，以 controller 名称为 job | 八个已接入 controller job 各自 down 或整个 job 消失 5m warning |
| Flux 六类对象 | KSM 自定义资源状态 gotk_resource_info | 非暂停对象未 Ready 持续 15m；根 Kustomization 状态指标消失 5m |

controller 存活规则共 8 条，状态与证书规则共 7 条。证书 warning 和 critical 范围互斥。
采集使用 honorLabels，证书和 Secret 的 namespace/name 是被观测对象，不能覆盖为 exporter 命名空间。
目前只采集 cert-manager controller；webhook/cainjector 继续依赖通用 workload 健康规则。

Flux 自定义指标覆盖 Kustomization、HelmRelease、GitRepository、HelmRepository、HelmChart、
OCIRepository。KSM 只增加这些资源与 CRD 发现所需的 list/watch，保留 Kubernetes collectors。
resource_namespace 保存对象命名空间。suspended=true 排除；默认省略 suspend 仍参与判断。
OCI 类型 HelmRepository 正常没有 Ready 条件，repository_type=oci 排除；OCIRepository 本身仍检测。
不以旧 gotk_reconcile_condition 指标编写规则，也不通过告警自动解除暂停或修改配置。

## 排障

- 证书：先查 Certificate conditions，再沿 CertificateRequest、Issuer、Order、Challenge 找原因。
  本规则只覆盖 cert-manager 管理的证书，不证明实际 HTTPS 入口已经加载新证书。
- Secret 同步：查 ExternalSecret/ClusterSecretStore conditions 与 ESO 日志，核对 provider 网络、身份和授权；
  不输出 Secret 内容。旧的成功副本可能仍可用，但不能据此认为后续轮换可靠。
- Flux：按 customresource_kind、resource_namespace、name 定位对象，查 conditions 与依赖。
  15m 用于容忍正常升级。主动维护使用暂停或有期限的静默，禁止永久屏蔽失败。
- 指标缺失：依次看原生监控 CR、转换对象、targets、即时查询和 KSM 的 RBAC/配置日志。
  up==0 不能发现已移除目标，因此各预期 job 另用 absent 检测；同 job 单副本以外的拓扑缺失仍有盲点。

实现：[PR #160](https://git.ddupan.top/panxiao81/homelab-infra/pulls/160)、
[OCI 例外 #161](https://git.ddupan.top/panxiao81/homelab-infra/pulls/161)。
上游依据：[Flux 自定义指标](https://fluxcd.io/flux/monitoring/custom-metrics/)。
19 个规则语义测试覆盖暂停、缺省 suspend、OCI 例外、证书级别切换及 ESO 状态零值等。
2026-09-25 现场已确认这 8 个 controller target up，4 个证书到期样本、12 个 Ready Secret 状态样本，
KSM 已输出 Flux 对象状态。未人为使生产证书过期或中断 Secret 同步；通知链路沿用此前端到端验收。

最终 Flux 应用版本为 `655ca567baa58767fcb6a0fd45c78c1044c2b95f`，KSM HelmRelease Ready。
