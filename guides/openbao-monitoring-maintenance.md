---
title: OpenBao 监控接入维护 runbook
last_reviewed: 2026-09-25
---

# OpenBao 监控接入维护 runbook

用于本次 OpenBao 自身指标接入中央监控。2026-09-25 维护者要求现在开始准备维护，
先完成顺序和 runbook；本文为待执行方案，不代表已经开启停机窗口或完成变更。
建议从明确宣布开始计时预留 30 分钟，实际起止记录 UTC，并注明维护者当地时区。

维护者确认使用人工解封：解封材料保存在 Bao VM，经 GPG 加密，解密私钥由 YubiKey 持有。
文件确切位置、封装格式以及是否另有残留明文未核实；agent 不搜索或读取这些材料。
解密、PIN/触摸确认和提交 unseal share 由维护者在自己的终端完成。

## 目标、分工与影响

- 执行者：准备配置与采集声明、检查、备份核对、部署、观测和配置回滚。
- 维护者：确认 GPG 文件与 YubiKey 可用、人工解封；整个重启及回滚期间保持在线。
- 本次只涉及 telemetry、最小权限采集身份与必要采集/告警，不升级 Bao、不改 seal 类型、
  不重新初始化、不轮换解封密钥，也不恢复 Raft 数据。
- 停机或 sealed 期间，秘密读取、动态凭据签发/续租、PKI/ACME 和 Bao 登录不可用。
  已投射的 Kubernetes Secret 不会因 Bao sealed 自动消失，但 ESO 刷新会失败；
  不能保证所有依赖应用都无影响，窗口内避免启动依赖新凭据的部署和轮换。
- Telegram 使用现有挂载 token，预计仍可发通知；维护前核对，不能把“预计”当作保证。

## 顺序与交接点

| 顺序 | 负责方 | 操作和通过条件 |
|---|---|---|
| 1，停机前 | 执行者 | 核对版本、运行配置来源、seal 状态和受鉴权 metrics；判断是否真的需要重启 |
| 2，停机前 | 执行者 | 准备并审查 IaC 差异、采集身份及续期方式、监控 CR 与回滚配置；离线校验通过 |
| 3，停机前 | 维护者 | 在自己的终端确认 YubiKey 解密路径可用、所需 share 数量可满足，回复“人工解封已就绪” |
| 4，停机前 | 执行者 | 确认独立 VM 登录/控制台、快照与配置备份、依赖基线；所有恢复材料不依赖运行中的 Bao |
| 5，T+0 | 双方 | 明确宣布窗口开始，记录时间；只对预期告警设置 30 分钟到期的精确静默 |
| 6，T+0～5m | 执行者 | 应用已审查配置；若确需重启，只重启一次，确认进程启动及 sealed 状态后立即交接 |
| 7，T+5～10m | 维护者 | YubiKey 解密并人工 unseal，直到 initialized=true、sealed=false；不向 agent 发送 key |
| 8，T+10～20m | 执行者 | 验证 Bao 和依赖恢复，再上线/验证受鉴权采集、规则及凭据自动续期/重新登录 |
| 9，T+20～30m | 双方 | 满足验收则结束窗口；否则停止扩大变更，按下述回滚/故障分支处理 |

时间段是预算，不是自动执行信号。维护者没有完成解封准备时，不执行重启。
若受鉴权检查表明现有 telemetry 已满足需求，直接完成无需停机的采集接入，不为走流程重启。

## 1. 停机前检查

从能够验证 TLS 的客户端检查，无需登录或解封材料：

```bash
export BAO_ADDR=https://bao.ad.ddupan.top:8200
bao status -format=json
```

记录 initialized、sealed、seal 类型、threshold、版本和节点身份，不从旧初始化示例推断 threshold=1。
`bao status` 在 sealed 时通常返回退出码 2；不能把这个预期状态当作进程崩溃。
若已经异常 sealed 或 initialized=false，停止本次常规维护，先定位现有故障，绝不执行 init。

在 VM 上确认服务状态、实际二进制和配置路径，不输出配置中的秘密：

```bash
sudo systemctl is-active openbao
sudo systemctl show openbao -p MainPID -p ExecMainStatus
/usr/local/bin/bao version
```

仓库默认配置路径 `/etc/openbao/config.hcl`、数据路径 `/opt/openbao/data`；执行前核对现场。
保持一条已建立的 VM 管理会话，并确认断开后仍能通过独立控制台或既有维护身份恢复访问。
不要依赖 Bao 在停机期间签发新的 SSH 凭据。

受鉴权请求 `/v1/sys/metrics?format=prometheus`，只记录 HTTP 状态、格式和必要指标名。
此前匿名请求返回 403，只证明访问受限；模板未显式写 telemetry 也不等于运行时禁用了它。
鉴权材料只通过受控内存/文件引用传递，不放命令行、Git 或日志。

## 2. 配置与采集准备

如确需显式配置，候选最小变更为：

```hcl
telemetry {
  prometheus_retention_time = "5m"
  disable_hostname = true
}
```

采集间隔规划为 30 秒。以上是待审查片段，需按现场版本校验；已有 telemetry 配置应合并，
不要重复添加。保留 TLS、Raft、seal、认证与现有 listener 设置。
指标标签和前缀以实际返回为准，不能预先假设所有指标都以 bao_ 开头。

采集身份限定 `sys/metrics` GET 所需 read 能力，先验证权限和实际请求；不要复用 root token，
也不开放匿名 metrics。明确身份取得、自动续期/重新登录与重启恢复方式后，才认为采集准备完成。
优先复用现有机器身份机制；若需 agent/proxy，应在窗口前写好最小配置并验证访问边界，
不在停机后临时决定长期 token 或新增服务架构。

监控声明优先 ServiceMonitor/PodMonitor/PrometheusRule；外部 VM 的发现方式应与最终采集架构匹配。
HTTPS 使用正确域名/CA，不关闭校验；metrics path 为 `/v1/sys/metrics`，`format=prometheus`
放 query params，不能把问号串在 path 里。sealed 期间 metrics 不可用，因此还需独立 health/目标缺失检测，
不能仅靠 Bao 内部指标证明 sealed 状态可被发现。

本 runbook 编写时，最终采集身份、续期机制、配置 PR 与现场预检尚未完成，均为重启前置条件。
使用现场版本支持的配置校验方式，先检查对应命令 help；禁止启动第二个 server 验证同一 Raft 数据目录。
现有 Ansible 写配置会通知 restart，不能把正式 apply 当作无停机预演。

## 3. 回滚材料与维护静默

- 以 root-only 权限备份实际配置，记录原权限/属主和 checksum；备份留在独立可访问的管理位置。
  不把完整配置贴到聊天或 wiki。
- 使用已有快照流程核对最近成功快照；必要时在停机前生成一次并检查退出状态、文件大小、校验和和副本可访问性。
  现有来源为 `openbao-snapshot.service` / timer 与 `/usr/local/bin/bao-snapshot.sh`，先核对现场存在再运行。
  不打印 snapshot token；快照文件存在不等于恢复演练成功。
- 记录 ESO ClusterSecretStore 与 ExternalSecret 当前状态、refreshTime，以及代表性认证/PKI 流程的基线。
- 在 Grafana 选择外部 Alertmanager，仅对 `ClusterSecretStoreNotReady{name="openbao"}` 及已确认受影响的
  ExternalSecret 精确设置限时静默，记录 silence ID。不要静默全部 critical、Telegram 发送故障或无关服务。

## 4. 重启与人工解封

仅在前置条件全部满足且窗口已明确开始后，由执行者在 VM 执行：

```bash
sudo systemctl restart openbao
sudo systemctl is-active openbao
```

随后检查 `bao status`。服务 active 而 sealed=true 是人工解封流程的预期交接点，
此时停止自动操作，告诉维护者“Bao 已启动，等待人工 unseal”。

维护者在自己掌控、无录屏/日志采集的终端按既有 GPG 流程解密所需 share，随后使用隐藏输入提示：

```bash
export BAO_ADDR=https://bao.ad.ddupan.top:8200
bao operator unseal
bao status
```

按现场 threshold 提交足够的不同 share。不要使用 `xargs bao operator unseal`、命令替换或明文参数，
也不要把解密结果交给 agent。仓库旧初始化示例中的 xargs 方式不用于本次维护。
加密文件可能是 GPG 文件、base64 包装 share 或初始化 JSON；由维护者按真实格式处理，本文不猜文件路径或格式。
完成后只回报 sealed=false 与非敏感状态；清理自己产生的临时解密副本/剪贴板，不删除原始加密备份。

## 5. 验收与结束

必须逐项记录结果，不以 systemd active 代替可用性：

1. initialized=true、sealed=false，节点/集群身份未变化，TLS 校验正常；预期 active 节点健康接口成功。
2. 既有机器身份登录正常；代表性秘密消费/PKI 流程按既有权限验证，结果不输出秘密。
3. ClusterSecretStore/openbao Ready；窗口前健康的 ExternalSecret 恢复 Ready，并观察一次新的实际刷新。
   需要加速时选择一个受影响对象触发 reconcile，不把所有 ESO 对象批量强制刷新。
4. 受鉴权 metrics 返回有效 Prometheus 数据，匿名请求仍被拒绝；中央 target 连续至少三次 up，关键指标有当前样本。
5. 采集身份续期/重新登录机制验证通过；规则已加载且无评估错误，目标消失/鉴权失败有可识别告警。
6. 若做临时告警演练，标注维护测试并记录 firing/resolved；没有做真实故障演练时明确注明。
7. 取消本次 silence，记录窗口实际结束时间、配置 commit/PR、验证与未完成项，更新来源文档。

## 6. 停止与回滚分支

- 新配置校验失败：不应用、不重启，修正候选配置。
- 重启后进程无法启动：检查有限范围日志，恢复原配置及权限，再启动服务；维护者仍需准备 unseal。
- 进程已启动但 YubiKey/解密/份额不可用：停止反复重启，维护者处理解封流程。
  恢复旧配置不会自动解封；若接近窗口截止则按故障处置，不能宣布回滚已恢复。
- Bao 已恢复，仅采集鉴权/指标失败：优先撤回新增采集配置/身份变更，保持核心服务可用；
  不为修监控反复重启 Bao。记录监控尚未完成，安排后续修复。
- 必须恢复原服务配置时：恢复备份、重启、再次人工解封，并重复核心与依赖验收。
- 本次配置回滚不包含 Raft snapshot restore、清空数据目录、init、rekey 或 seal migration。

## 来源与证据边界

维护者 2026-09-25 确认 VM 保存 GPG 加密解封材料，YubiKey 解密且需人工 unseal。
本轮仅准备文档；没有读取解封材料、应用服务配置、设置静默或执行重启。
源码：[OpenBao 部署与恢复入口](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/openbao/README.md)，
配置模板与 restart handler 位于同目录 `ansible/roles/openbao/`。
命令依据：[人工 unseal](https://openbao.org/docs/2.6.x/commands/operator/unseal/)、
[telemetry 配置](https://openbao.org/docs/2.6.x/configuration/telemetry/)。
