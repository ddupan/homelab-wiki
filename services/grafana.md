---
title: Grafana 与可观测性使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# Grafana 与可观测性

从 <https://grafana.ad.ddupan.top> 查看 homelab 的指标、日志和追踪。
使用 Authelia OIDC 登录；远程访问需要到 LAN 的路由及内网 DNS。

本页依据现有 observability README、Grafana 数据源配置、内存看板 JSON 和 exporter 说明整理，
部分来源仍在源码工作区、尚未提交。本轮未打开网页或执行查询；以下结果描述是使用预期。

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

## 出问题时与维护入口

- 域名打不开：先区分内网 DNS、到 LAN 的路由和浏览器证书错误。
- 登录后无权限：检查 Grafana 的账号/角色授权，Authelia 登录不等于管理员权限。
- 看板空白：检查时间范围、数据源和筛选条件，再区分缺少采集与查询失败。
- 指标与日志不一致：先对齐时间和目标实例，再判断是否为采集范围不同。

部署、采集与恢复入口为 homelab-infra `platform/observability/README.md`；
内存指标解释见 `platform/observability/metrics/exporters/README.md`。
看板配置由 Git/ConfigMap 管理，网页临时调整不作为持久配置的权威来源。
旧 Compose 栈与数据已[清理](victoriametrics-legacy.md)，不要再使用旧实例作为排障入口。
