---
title: 监控覆盖与补齐计划
last_reviewed: 2026-09-25
---

# 监控覆盖与补齐计划

结论：监控底座和 Telegram 通知已工作，但业务服务接入与告警覆盖明显不足。
“有 exporter”“有 PodMonitor”“数据库里曾出现过指标名”都不能代替当前采集成功和有效规则。
本页用于接续覆盖建设，服务使用入口仍见 [Grafana](../services/grafana.md)。

## 第一批补齐进展

2026-09-25 已上线 kube-state-metrics，并恢复 NATS PodMonitor 转换与采集。
新增集群状态 11 条、主机/ZFS 5 条、采集与通知 5 条规则，共 21 条；正式规则总数为 68。
新增资源按维护者要求优先使用 ServiceMonitor/PodMonitor/PrometheusRule。
具体阈值、降噪边界、声明转换关系与验收方法见 [基础监控与告警运维](monitoring-foundation.md)。

下面的规模、矩阵和盲点保留初轮盘点基线，不能再当作第一批实施后的现状。
第二批数据库/OpenBao/存储/备份、外部探测和集群外心跳尚未实施。

## 证据和范围

2026-09-25 17:26–17:31 UTC，只读检查当前集群工作负载、采集 CR、vmagent 实际 targets、
vmalert 已加载规则、VictoriaMetrics 即时查询、CNPG 监控/备份声明、证书资源和本机服务清单。
同时查阅服务 wiki、源码配置和运维文档。没有读取 Secret、修改集群或部署 exporter。
共享 etcd 正由维护者调整；其瞬时采集异常不作为本轮待修故障。

没有逐台登录 PVE、OCI、域控和其他 VM，也没有验证所有应用业务接口、备份文件或恢复能力。
“未接入”指未进入这套中央 VictoriaMetrics/Alertmanager，不排除服务另有本地日志、
健康检查或独立监控；例如 LiteLLM 源码中有独立 Prometheus Compose 配置，本次未验证运行状态。

源码基线为 [homelab-infra a43b7d3](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/a43b7d3c26f9724b9d5b2ad45058f2d1632741af/platform/observability)，
共享 etcd 采集/规则另以本次现场 CR 为准（来源工作区尚有未提交配置）。
审阅时主工作区落后于远端且有其他改动，不能拿本地旧 :8080 配置覆盖已合并修复。

## 初轮盘点规模（实施前）

- 69 个 Deployment/StatefulSet/DaemonSet 对象（44/13/12），不等同于服务数或全部实例数；CNPG 管理的数据库 Pod 不在此统计内。
- vmagent 有 17 个目标、15 个 job；其中 node-exporter 与 docker-hosts 重复采集同一个 :9100 地址，实际唯一 URL 为 16 个。
- 采集对象：3 VMNodeScrape、1 VMPodScrape、8 VMServiceScrape、3 VMStaticScrape。
- 有 1 个 NATS PodMonitor，但没有其转换后的 VMPodScrape 或实际 target；没有 ServiceMonitor、PrometheusRule、VMProbe。
- 5 个 VMRule，vmalert 实际加载 47 条告警：vm-health 12、vmagent 14、vmalert 8、vmsingle 7、shared-etcd 6。
- 严重性为 critical 16、warning 30、info 1；本次规则 API 未报告执行错误。41 条属于监控栈，6 条属于共享 etcd。
- Telegram 已接 warning/critical 和恢复通知；info 不推送。通知接入验收见服务页。

## 初轮覆盖矩阵（实施前）

“无专用告警”指没有该服务的业务/运行告警；共享进程或错误日志规则可能部分命中，不能视为完整覆盖。

| 对象 | 当前指标采集 | 当前告警覆盖 | 主要缺口 |
|---|---|---|---|
| VictoriaMetrics / vmagent / vmalert | 已采集 | 有基础规则 | 部分规则所依赖功能未启用；核对空结果与指标兼容性 |
| Alertmanager | 已采集 | 部分通用进程存活规则 | 缺 Telegram 发送失败、配置加载失败及集群外心跳 |
| VictoriaLogs / VictoriaTraces / OTel / VM Operator | 已采集 | 可能命中通用错误/进程规则 | 缺明确的存活、队列丢弃、容量与数据新鲜度覆盖；现有 ServiceDown 的 job 正则不完整覆盖这些名称 |
| Grafana | 未见专用目标 | 无专用告警 | 页面/登录可用性、数据源失败 |
| laptop node-exporter / process-exporter | 已采集；:9100 重复 | 无主机专用规则 | 内存、swap、磁盘空间/inode、ZFS 健康、IO、主机不可达、进程异常 |
| kubelet / Kubernetes cAdvisor | 已采集 | 无 Kubernetes 对象状态规则 | 只有资源指标，不能替代 Pod/Deployment/PVC 状态采集 |
| kube-state-metrics | 未部署，只有安装脚本 | 无 | NodeNotReady、CrashLoop/OOM、重启、不可用副本、PVC Pending、Job 失败 |
| Blocky | 已采集 | 无 DNS 专用规则 | DNS 实际解析探测、上游失败、响应延迟 |
| 共享 etcd | 三个成员已配置采集 | 6 条专用规则 | 维护中；后续补备份新鲜度、证书到期和目标缺失语义 |
| NATS | exporter 与 PodMonitor 已存在，未进入实际 targets | 无专用规则 | 先修通采集，再补 JetStream 存储、consumer pending/redelivery、连接与集群健康 |
| CNPG PostgreSQL | 现有 Cluster 的 enablePodMonitor=false，无专用 target | 无专用规则 | 连接数、复制/主从、事务、磁盘、备份/WAL 新鲜度；当前单实例 |
| OpenBao | 未接入中央采集 | 无专用规则 | sealed/可用性、请求错误、Raft、PKI 到期、快照成功及异机副本 |
| SPIRE / Authelia / Hydra | 未接入中央采集 | 无专用规则 | 身份签发/登录失败、证书续期、连接依赖、控制器就绪 |
| External Secrets | 未接入中央采集 | 无专用规则 | Secret 同步失败/过期、provider 访问失败 |
| cert-manager | 指标 Service 已有，未采集 | 无证书规则 | 证书临期、续签失败、Issuer 状态；本次 4 个 Certificate 均 Ready 不等于已有告警 |
| Envoy Gateway / Cloudflared | 未接入中央采集 | 无专用规则 | 入口 5xx/延迟、路由、上游、隧道可用性 |
| CoreDNS | 已暴露 :9153 指标，未采集 | 无专用规则 | DNS 请求失败/延迟、实际解析探测 |
| Flux | 未接入中央采集 | 无专用规则 | Kustomization/HelmRelease/GitRepository 同步失败、长时间未更新 |
| SeaweedFS | master/filer/volume 已有 :9327 指标 Service，未采集 | 无专用规则 | 容量、卷/副本健康、S3 可用性、持久化与备份 |
| OpenEBS / ZFS LocalPV | 控制器未专门采集；宿主 ZFS 指标已有 | 无存储专用规则 | PVC/卷挂载、池降级、容量、故障盘；SMART/IPMI 未接入 |
| Gitea / zot / Nexus / NetBox / Backstage | 未见应用专用目标 | 无专用规则 | HTTP 可用性、错误率、依赖；按实际使用优先级接入 |
| Dynamic Runner | 未接入中央采集 | 无专用规则 | 队列积压、调度失败、孤儿实例、执行基础设施不可用；与 NATS 联动 |
| SMTP relay / Tailscale | 未接入中央采集 | 无专用规则 | 邮件队列/投递失败、节点/路由可达性 |
| PVE / OCI / Samba AD / 其他 VM | 中央 targets 未覆盖 | 无专用规则 | 主机存活与资源、复制/时间同步、关键服务、站点网络、备份 |
| laptop Docker / Incus / libvirt / FRR / NFS/SMB 等 | 主机/进程资源只有部分可见性，无组件专用目标 | 无专用规则 | 虚机/容器生命周期、宿主服务失败、路由邻居/存储服务可用性；独立 Docker cAdvisor 未部署 |
| Marker / OpenViking / LiteLLM 等源码服务 | 未见中央 target；运行范围需由各项目确认 | 无中央专用规则 | 先明确现役范围，再接业务指标；不为归档或未部署服务添加空目标 |
| e5renew / research-auto | 有集群 workload，但未见专用目标 | 无中央专用规则 | 属外部消费者，业务规则由项目维护；平台提供通用 workload 健康覆盖 |

## 初轮发现的盲点（实施前）

### Kubernetes 对象状态

没有 kube-state-metrics workload，也没有其 targets。即时查询
`kube_deployment_status_replicas_available`、`kube_pod_container_status_restarts_total`、
`kube_node_status_condition`、`kube_persistentvolumeclaim_status_phase` 均无当前样本。
数据库历史指标名列表仍能找到 kube_*，因此不能仅凭 Grafana 自动补全认定已经接入。

盘点瞬间 Backstage 为 CrashLoopBackOff，SPIRE StatefulSet 的 sandbox controller 不就绪，
SPIRE server 主容器仍 Ready。它们可能由其他任务调整；本轮未诊断或操作，
只用于说明现有 47 条规则无法承担通用 workload 状态告警。以后需要人工对齐维护窗口。

### NATS 声明与运行不一致

NATS StatefulSet 有 :7777 prom-exporter，PodMonitor/nats 已存在，但实际没有 NATS target，
即时 nats_* 查询为空。VM Operator Pod 从 2026-07-10 运行，而 PodMonitor CRD 创建于
2026-09-16；启动时 CRD 发现/转换控制器启动是排查线索，尚不能据此认定根因。
应检查转换器启用状态、watch/RBAC 和启动日志，修复后验证生成对象、target 和实际样本三层。

### 备份不是“有 PVC 就够了”

现有 CNPG Cluster 没有 spec.backup，也没有 ScheduledBackup，status.lastSuccessfulBackup 为空。
这只证明 CNPG 管理的备份链路未声明，不排除未盘点的宿主脚本；需要另外明确备份方式。
OpenBao 源码已有本地 snapshot timer，但成功时间、异机传输和恢复验收没有中央指标/告警。
Samba AD 文档有备份操作示例，SeaweedFS/zot 文档也明确独立异机备份缺口；不能直接标记为已保护。

备份监控至少记录最近成功时间、结果、目标可达性和保留副本；恢复演练成功时间单独记录，
不能由“备份任务退出码 0”推断可恢复。定义实际备份流程后再定告警阈值。

### 监控自身和规则语义

- vmalert 的 AlertmanagerErrors 只覆盖 vmalert → Alertmanager，不覆盖 Alertmanager → Telegram；后者的失败计数已经有指标但没有对应规则。
- 当前 ServiceDown 只匹配部分 VictoriaMetrics job，缺通用 target down 与 expected-target absent 检查。
  `up == 0` 无法发现目标被移出发现集合；必须先定义关键目标清单，再做缺失检测。
- 没有 blackbox/VMProbe、probe_* 当前指标或 HTTP/DNS/TCP/TLS 外部探测。
  集群内指标正常不证明用户端入口、DNS、证书链与身份登录可用。
- 没有 Watchdog/集群外心跳接收。Alertmanager 或整个站点断电/断网时，内部告警不能保证通知到达。
- RecordingRulesError/RecordingRulesNoData、SeriesLimitHour/DayReached、StreamAggr* 等规则查不到依赖 series；
  当前没有 recording rules，部分可选功能可能未启用，不能把所有空结果判为坏规则。
  `vmagent_relabel_config_last_reload_successful` 当前也无样本，需逐条做功能/版本匹配。
- 主机 :9100 被 node-exporter 和 docker-hosts 两个 job 重复采集。后续统一所有权，清理前核对查询依赖，避免 sum 重复统计。
- 缺面向节点/服务依赖的抑制、维护静默流程和预期维护范围。优先减少无行动价值的重复通知，不直接导入全套规则。

## 建议实施顺序与验收

| 批次 | 实施内容 | 验收条件 |
|---|---|---|
| 1：补平台基本覆盖 | GitOps 部署 kube-state-metrics；Node/Pod/Deployment/PVC/Job 规则；复用 node-exporter 补主机/ZFS；修 NATS 转换；补 Telegram 发送失败规则 | 新目标 up 且有当前样本；规则有依赖数据；测试触发/恢复消息送达；维护对象能明确静默 |
| 2：保护关键依赖和数据 | CNPG、OpenBao、SeaweedFS、NATS 业务规则；cert-manager、ESO、Flux；备份方案与最后成功时间指标 | 每项有采集、针对性规则、runbook、凭据最小权限和故障演练结果；备份独立验收 |
| 3：验证用户可用性 | LAN DNS、入口 HTTPS、Gitea/认证/S3/镜像等关键路径探测；集群外 Watchdog 接收 | 从独立位置发现站点/监控中断，探测不用暴露管理员凭据或制造业务写入 |
| 4：扩展到其余基础设施和应用 | PVE/OCI/域控主机、Docker/Incus/libvirt/网络；按使用频率接入应用 | 按服务维护覆盖表，退役目标同步移除，采集开销和标签基数受控 |

第一批基础补齐已实施，验收边界见上方链接；下一步对齐第二批关键依赖与备份方案。开始具体实施前对齐各服务进行中的工作，
尤其是共享 etcd、数据库迁移与身份平台；本次盘点不授权自动修改这些项目。
