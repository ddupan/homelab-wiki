---
title: OpenBao 监控接入维护 runbook
last_reviewed: 2026-09-25
---

# OpenBao 监控接入维护 runbook

用于本次 OpenBao 自身指标接入中央监控。2026-09-25 维护者要求现在开始准备维护，
先完成顺序和 runbook；本文同时保留执行顺序与最终验收，实际完成范围见下方“本次执行状态”。
建议从明确宣布开始计时预留 30 分钟，实际起止记录 UTC，并注明维护者当地时区。

维护者确认使用人工解封：解封材料保存在 Bao VM，经 GPG 加密，解密私钥由 YubiKey 持有。
文件确切位置、封装格式以及是否另有残留明文未核实；agent 不搜索或读取这些材料。
解密、PIN/触摸确认和提交 unseal share 由维护者在自己的终端完成。

## 本次执行状态（2026-09-25）

维护者已确认 YubiKey 解密可用并明确同意进入重启/人工解封交接。
20:34:42 UTC 应用已校验 telemetry 配置并重启，随后维护者完成 unseal。
现场确认 initialized=true、sealed=false、health=200、受鉴权 Prometheus metrics=200，
cluster_id 与维护前一致，匿名 metrics 仍为 403。

停机前已更换失效的快照 token，修正每日续期命令为现场支持的 `bao token renew`（不带 -self）。
新快照 `openbao-20260925-203149.snap` 为 183334 bytes，VM 外副本保存在管理工作站
`/home/panxiao81/.local/state/openbao-maintenance/`，权限 0600，SHA-256 一致。
这是配置维护前的备份核验，不等于完成异机灾难恢复演练。
快照 service Result=success、timer active；文件只在写入成功后更名，失败不清理旧快照。

metrics policy/role 已按候选源配置应用：实际 vmagent-main SA 登录与 token 续期成功，
无权读取业务 Secret，测试 token 已撤销。随后已将 `vault_policy.metrics` 与
`vault_kubernetes_auth_backend_role.metrics` 导入现有 SeaweedFS S3 主远端 state，
仅针对这两项的 plan 均为 no-op；这不代表整个 Terraform 配置已经全量 zero-diff。
重启后 ClusterSecretStore 和 12 个 ExternalSecret Ready；monitoring/alertmanager-telegram
已定向刷新，refreshTime 更新为 20:39:33 UTC，状态 SecretSynced。
[PR #162](https://git.ddupan.top/panxiao81/homelab-infra/pulls/162) 已合并，Flux 应用
`834f65494195ba5e139e1fc6ee0221fd705b9656`，vmagent 新 Pod 3/3 Ready。
Bao Agent 日志确认自动登录成功、token 写入内存卷及首次自动续期成功；up{job="openbao"}=1，
已观察连续三次 up=1，当前指标可查询，单次抓取约 636 个样本，OpenBaoMetricsUnavailable 规则已加载，无评估错误。
本次未设置维护静默，无需清理 silence；没有撤销维护者自己的登录会话。
真实长周期重新登录、快照未来定时运行和独立灾难恢复演练不包含在本次验收内。

以下保留操作顺序和回滚方法；其中“待执行”描述须结合本节判断，不能重复重启。

## 内部健康和快照日常监控

2026-09-25 后续部署未重启 Bao（启动时间仍为 20:34:43 UTC）。真实快照任务
Result=success、退出码 0，新快照 194598 bytes；VM 指标报告 success=1、textfile scrape error=0。
Flux 已应用 `7137426e8f5c99ca1514c508501e07c2066dd769`；API 和 VM exporter 两类 target 均为 up，
快照结果与成功时间已进入 VictoriaMetrics。21:02:27 UTC 六条 OpenBao 规则均 inactive，
部署初期缺数据 pending 已解除；全栈 108 条规则无评估错误。Ansible 部署后 check mode 零变更。
本次通过 28 个告警语义场景及 4 个快照脚本测试，未通过制造真实故障验证 Telegram。

[PR #163](https://git.ddupan.top/panxiao81/homelab-infra/pulls/163) 补齐内部健康、健康 gauge 缺失、
快照失败、快照超时/无成功记录和快照采集失联五条规则；原有受鉴权采集不可用规则保留。
仍由 ServiceMonitor 和 PrometheusRule 声明。内部 active 判定面向当前单节点，扩容为多节点前需修改。

VM 使用 Ubuntu node_exporter，监听 `192.168.10.8:9100`；没有公共入口，当前 UFW 未启用，
LAN 地址绑定不是逐来源 ACL。采集标签为 `job=node-exporter,node=bao1`，复用主机内存和文件系统规则。
textfile 目录 `/var/lib/prometheus/node-exporter/` 只由 root 写入，指标不带 token 或快照内容。
独立 exporter 在 Bao sealed 或快照 token 失效时仍能报告快照结果。

每日任务失败会记录 result=0，保留旧的最后成功时间；只有完整快照原子更名后才更新成功时间并清理旧文件。
失败持续 5 分钟为 warning，距最后成功超过 36 小时或没有成功指标持续 15 分钟为 critical；
exporter 失联、textfile 解析错误、结果指标缺失持续 5 分钟为 warning。
本地快照成功不等于已复制到独立故障域，更不等于恢复演练通过。

部署和回滚使用独立的 `ansible/monitor-openbao.yml`，只处理 exporter、快照脚本和 timer；
不改 Bao 服务配置，不轮换 token，不需要再次人工解封。首次部署必须执行一次真实快照建立基线。
参数、验证命令与回滚边界见
[源码监控运维说明](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/openbao/MONITORING.md)。



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

配置见 [PR #162](https://git.ddupan.top/panxiao81/homelab-infra/pulls/162)，已合并部署，状态以本次执行记录为准。
使用绑定 monitoring/vmagent-main 的 Kubernetes auth metrics role，由 Bao Agent sidecar 自动登录/续期，
token 仅存 Pod 内存卷供 vmagent 只读消费。采集用 ServiceMonitor + 外部 Service/Endpoints；
现有 converter 的 Endpoints 发现保留，EndpointSlice 迁移另行处理。
role 权限、认证/首次续期与受鉴权 metrics 已验收；未来维护仍须重新核对现场，不只依靠历史记录。
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
本轮已进行只读预检及候选文件准备；没有读取解封材料、替换运行配置、设置静默或执行重启。

### 2026-09-25 停机前预检

- Bao API 与 VM 二进制均为 2.6.1，Shamir threshold/shares 为 1/1，initialized=true、sealed=false。
- 管理入口为 `ssh ansible@192.168.10.8`，sudo 可用。按维护者明确要求，将管理工作站
  panxiao81 的 authorized_keys 中两条受信任公钥追加到 VM 的 ansible 用户，保留原公钥，
  修改前已在该账号 `.ssh/` 备份 authorized_keys；此次是现场授权变更，尚未纳入 cloud-init/IaC。
- 运行配置未显式设置 telemetry。原配置与候选文件分别保存为 VM root-only 目录
  `/etc/openbao/maintenance-monitoring-20260925/config.before.hcl`、`config.candidate.hcl`。
  候选文件通过现场 `bao operator validate-config -config=...`；原运行配置未变。
  若后续其他任务改动运行配置，必须重新比较后再使用，不能覆盖新改动。
- 快照服务 9 月 23–25 日日志均为 403，9 月 25 日退出码 2；默认 `/var/backups/openbao`
  未发现 .snap。尚未证明存在其他有效副本，此项阻止进入重启。
- 源码快照使用 periodic token，但没有续期步骤。候选补丁增加每日续期、显式 rotate 开关、
  私有 partial 文件及成功后原子更名；403 的精确原因仍需检查 token 状态，不能直接断言已过期。
- 当前本地 Bao 管理员会话不可用；受鉴权 metrics、Terraform plan/apply、快照身份恢复待完成。
- 候选通过 Kustomize、规则检查、server dry-run、Terraform fmt；Agent 只在关闭的本机端口验证
  解析/启动，未做真实登录。快照模拟测试验证续期失败与写失败不删旧备份，成功才清理保留数量。

源码：[OpenBao 部署与恢复入口](https://git.ddupan.top/panxiao81/homelab-infra/src/branch/main/infrastructure/openbao/README.md)，
配置模板与 restart handler 位于同目录 `ansible/roles/openbao/`。
命令依据：[人工 unseal](https://openbao.org/docs/2.6.x/commands/operator/unseal/)、
[telemetry 配置](https://openbao.org/docs/2.6.x/configuration/telemetry/)。

### 人工解封准备确认

维护者已在插有 YubiKey 的 working PC 成功验证解密。VM 的 `/home/ansible/unseal.txt`
包含带 `Unseal Key 1:` 前缀的 base64 GPG 密文；正文不保存其内容。
实际解封由维护者在 working PC 解密后通过 HTTPS 提交，不能将密文直接当作 unseal key。
这次验证未执行解封或重启。

随后只读确认：快照 token 的 lookup-self 也返回 403，VM root 没有可用的 Bao CLI 会话。
需要维护者先登录管理会话，恢复快照身份并完成受鉴权预检后才能进入停机。
若在 VM 使用 OIDC CLI 登录，应从 working PC 建立
`ssh -t -L 8250:127.0.0.1:8250 ansible@192.168.10.8`，再在 VM 的 root shell 设置
`BAO_ADDR=https://bao.ad.ddupan.top:8200` 并运行 `bao login -method=oidc -no-print role=admin`。
登录网址在 working PC 浏览器打开，账号需符合现有 vault-admins 组约束；不把 token 发给 agent。
