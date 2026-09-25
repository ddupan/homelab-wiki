---
title: Grafana 与可观测性使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-25
last_verified: null
---

# Grafana 与可观测性

从 <https://grafana.ad.ddupan.top> 查看 homelab 的指标、日志和追踪。
使用 Authelia OIDC 登录；远程访问需要到 LAN 的路由及内网 DNS。

本页依据现有 observability README、Grafana 数据源配置、内存看板 JSON 和 exporter 说明整理，
部分来源仍在源码工作区、尚未提交。看板使用说明未逐项现场验证；
2026-09-25 的通知链路与采集故障验证范围见下文。

整体接入范围、已确认盲点和补齐顺序见 [监控覆盖与补齐计划](../guides/monitoring-coverage.md)。
第一批已接入的规则、阈值、静默和排障方法见 [基础监控与告警运维](../guides/monitoring-foundation.md)。

## 先看主机内存与 Swap

1. 打开 [Homelab 内存与 Swap](https://grafana.ad.ddupan.top/d/homelab-memory)。
2. 时间范围选择最近 1 小时，需要定位问题时改成问题发生的具体时段。
3. 先看“主机物理内存”“Swap 使用量”“Swap 换页速率”，再看程序/虚拟机 PSS 和 Pod working set。
4. 对比异常发生前后的曲线，记录时间与相关程序或 Pod，便于继续查日志。

看板来源为 `platform/observability/grafana/dashboards/homelab-memory.json`。
PSS、RSS、Pod working set 和 ZFS ARC 是不同统计口径，不应直接相加。
“没有数据”表示当前查询没有返回匹配样本，不等于数值为零。

## 自己查一条指标

进入 Explore，选择 **VictoriaMetrics** 数据源，时间范围设为最近 1 小时，
在 Code 模式输入以下看板已有的表达式，再执行查询：

```promql
node_memory_MemTotal_bytes{job="node-exporter"}
  - node_memory_MemAvailable_bytes{job="node-exporter"}
```

它计算主机已用内存，单位为字节。预期按采集目标返回曲线；有多个目标时，
查看返回标签后选择相应 instance，避免把多台机器当作一台解读。
该环境特意限定 `job="node-exporter"`，避免旧 docker-hosts 抓取同端口导致重复统计。

如需查看 Swap 换出活动，可使用看板已有查询：

```promql
rate(node_vmstat_pswpout{job="node-exporter"}[5m])
```

单位是 pages/s，不是 bytes/s。查询入口与编辑器行为见
[Grafana Prometheus 查询文档](https://grafana.com/docs/grafana/latest/datasources/prometheus/query-editor/)。

## 找一段日志

1. 进入 Explore，切换到 **VictoriaLogs** 数据源，设定最近 15 分钟。
2. 输入 `* | limit 20` 执行查询，展开一条结果，观察这套采集实际提供的字段。
3. 用真实出现的 namespace、Pod 或应用字段收窄范围；不要预先假定字段名。
4. 要找错误消息，可先输入 `error | limit 50`；有结果后按实际字段进一步筛选。

VictoriaLogs 使用 LogsQL。上述 limit 限制返回数量，不保证返回的是最新若干条。
关键字没有结果时可以放宽时间范围并回到第一步，区分“没有该关键字”与“没有采集数据”。
语法依据见 [VictoriaLogs 查询说明](https://docs.victoriametrics.com/victorialogs/querying/)。

## 三个数据源的分工

| 数据源 | 用途 |
|---|---|
| VictoriaMetrics | Prometheus 兼容指标查询，例如内存、CPU、采集健康 |
| VictoriaLogs | LogsQL 日志查询 |
| VictoriaTraces | Jaeger 兼容追踪查询；应用需要先接入追踪，不能仅凭数据源存在认为所有服务都有 trace |

数据源名称来自 `platform/observability/grafana/values.yaml`。

## Telegram 告警接入

2026-09-25 已通过 [homelab-infra PR #147](https://git.ddupan.top/panxiao81/homelab-infra/pulls/147)
合并并由 Flux 同步，替换原有全部 blackhole 的通知策略。配置来源为
[VMAlertmanager](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/c06c6f78572106586b9b55069dae654a35f4f6bf/platform/observability/metrics/vmalertmanager.yaml)
及同目录的 `alertmanager-external-secret.yaml`、`kustomization.yaml`。
已现场确认 Flux Ready、ExternalSecret SecretSynced、Alertmanager Pod Ready、
配置加载成功。通过 Alertmanager API 注入的临时测试告警已触发 Telegram 发送，
发送失败计数为 0，维护者已确认收到测试告警；测试在 60 秒后自动恢复。
恢复通知按 5 分钟组内间隔发出，发送总计数从 2 增至 3，失败计数仍为 0。
恢复消息的收件端确认未单独取得；总计数也包含一条既有 TooManyScrapeErrors 通知。
本次验证限于通知链路，不刷新整个 Grafana 服务的 `last_verified`。

- 接收频道：<https://t.me/ddupan_alerting>，数字 chat ID 为 `-1003956377923`。
- bot：`@ddupan_alerting_bot`。2026-09-25 通过 Telegram `getChat` / `getChatMember`
  确认频道 ID、管理员身份和发布消息权限；bot 直发的测试触发、恢复消息已由维护者确认收到。
- OpenBao：KV v2 mount `kv`、路径 `k8s/alertmanager`、字段 `telegram_bot_token`。
  ExternalSecret 使用 `ClusterSecretStore/openbao`，每小时同步到
  `monitoring/alertmanager-telegram` Secret 的同名字段。
- VMAlertmanager 挂载 Secret，使用 `bot_token_file` 读取，不在 Git 中保存 token。
- critical 首次分组等待 10 秒，未恢复每小时提醒；warning 等待 1 分钟，
  未恢复每 4 小时提醒。分组键为 `alertname, cluster, job, severity`，
  组内变更通知间隔 5 分钟；两类均发送恢复通知。info、缺失或其他 severity 暂不推送。
- 采用 Alertmanager 默认 Telegram 消息模板；同容器 CrashLoop 抑制重复重启通知，
  具体匹配范围见基础监控运维指南。

配置变更通过既有 Flux 流程发布，先确认 ExternalSecret Ready 和目标 Secret
投射成功，再确认 Alertmanager 加载配置及到 Telegram API 的出站网络。
首次启用可能推送当时已有的 warning/critical 告警；发送测试告警需要维护者同意，
并在频道确认故障与恢复消息均收到。静态检查不能代替这一步。

收不到通知时依次检查 ExternalSecret 状态、Alertmanager 配置加载与发送错误、
bot 的频道发布权限以及手机频道通知设置。轮换 token 后需等待或触发 ESO 同步，
并验证 Alertmanager 使用新 token；必要时重载或重启，不打印 Secret 内容。

## 采集失败的定位与处理

`TooManyScrapeErrors` 使用 vmagent 的采集失败计数判断最近 5 分钟是否出现错误，
持续 15 分钟后触发。告警中的 `instance` 是 vmagent 自己，并非失败目标地址；
先检查 vmagent `/api/v1/targets` 中非 up 目标的 `scrapeUrl` 与 `lastError`。
目标恢复后还要等待 5 分钟回看窗口消退，Telegram 恢复通知另受组内间隔影响。

- k3s 的 kubelet `/metrics` 还包含 apiserver/etcd 指标，实测约 16.1 MiB，
  超过 vmagent 默认 16 MiB 限制。`VMNodeScrape/kubelet` 单独设置
  `spec.max_scrape_size: "32MiB"`；其他采集任务保留默认值。
  再次超限时先统计指标族和响应大小，不直接无限增大全局限制。
- 独立 Docker cAdvisor 尚未部署，旧 `192.168.10.127:8080/metrics` 实际返回 nginx 404，
  已从 `VMStaticScrape/docker-hosts` 移除。该配置仍保留已有 :9100 主机目标，
  Kubernetes 容器指标继续由 `VMNodeScrape/cadvisor` 的 `/metrics/cadvisor` 提供。
  后续需要 Docker 容器指标时，先部署 exporter 并验证端口，再增加采集目标。

配置依据：[homelab-infra PR #148](https://git.ddupan.top/panxiao81/homelab-infra/pulls/148)，
2026-09-25 已合并并由 Flux 应用 `a43b7d3c26f9724b9d5b2ad45058f2d1632741af`。
现场确认 kubelet 恢复 up，旧 :8080 目标消失。此次验收期间另发现共享 etcd
`10.60.0.20:2381` 拒绝连接，因此不能将本次两项修复等同于全部采集目标健康或
`TooManyScrapeErrors` 已恢复；后续状态需重新检查 targets，etcd 的操作背景另行对齐。

## 出问题时与维护入口

- 域名打不开：先区分内网 DNS、到 LAN 的路由和浏览器证书错误。
- 登录后无权限：检查 Grafana 的账号/角色授权，Authelia 登录不等于管理员权限。
- 看板空白：检查时间范围、数据源和筛选条件，再区分缺少采集与查询失败。
- 指标与日志不一致：先对齐时间和目标实例，再判断是否为采集范围不同。

部署、采集与恢复入口为 homelab-infra `platform/observability/README.md`；
内存指标解释见 `platform/observability/metrics/exporters/README.md`。
看板配置由 Git/ConfigMap 管理，网页临时调整不作为持久配置的权威来源。
旧 Compose 栈与数据已[清理](victoriametrics-legacy.md)，不要再使用旧实例作为排障入口。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#grafana)。
