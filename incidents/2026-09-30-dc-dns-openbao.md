---
title: 2026-09-30 DC DNS 单点故障引发 OpenBao 访问与秘密同步中断
last_reviewed: 2026-09-30
---

# 2026-09-30 DC DNS 单点故障引发 OpenBao 访问与秘密同步中断

状态：服务已恢复，最终告警已清空；DNS 冗余与预防性整改尚未实施。
时间统一使用 UTC。依据为本次排障会话的命令回执、DC journal/APT 历史、ESO 与 Bao Agent
日志、vmagent targets 和 Alertmanager API；源码配置作为声明依据，不替代现场事实。

## 结论

**DNS 单点故障放大为多服务故障。AD 尚无高可用，关键服务的 DNS 可用性必须先得到独立保障。**

DC 在自动更新后的服务重启窗口内启动 Samba，CLDAP/KDC 绑定 IPv6 地址失败，
`samba-ad-dc` 随后退出。DNS 与 Samba 同时停止，且 `Restart=no` 使服务没有自动重试。
`bao.ad.ddupan.top` 解析失败后，ESO 无法登录 Bao，监控 Agent 也无法重新取得采集凭据。
因此出现 Secret 同步、ClusterSecretStore 和 Bao 指标不可用的连锁告警。

Bao 主机与进程在检查时健康：直连 LAN 地址、保留域名和 TLS 校验，健康接口返回
HTTP 200、`sealed=false`、`standby=false`。本次没有重启、解封或修改 Bao。
这证明检查时 Bao 本身可用，不代表已经逐请求证明整个故障窗口内从未发生其他异常。

2026-09-30 维护者确认整改方向：**不以完整 AD 高可用为前置条件，先消除关键服务
DNS 对单 DC 的依赖。** 这是已接受的目标；具体产品、部署位置和记录分发方案仍待设计，
本报告不将它写成已部署的能力。

## 影响与恢复证据

| 对象 | 已观察到的影响 | 恢复证据 |
| --- | --- | --- |
| DC `192.168.10.5` | Samba failed，53 端口查询超时；现场仅见 SSH 等少量监听 | 启动后 active，直接 DNS 查询 Bao 返回 `192.168.10.8` |
| Bao 域名访问 | laptop 解析超时；Pod 经 `10.43.0.10:53` 查询报 `server misbehaving` | 约 07:28:13 域名 HTTPS 健康检查 200，TLS 校验通过 |
| ESO `ClusterSecretStore/openbao` | `InvalidProviderConfig`、`unable to create client` | 07:28:15 `Ready=True`、`store validated` |
| 12 个 ExternalSecret | 07:28 的状态快照全部为 False，不能据此认定它们同时开始失败 | 07:31:35 状态快照全部 Ready=True |
| Bao 指标采集 | Agent DNS 登录失败；采集目标直接访问 IP 返回 403 | 07:31:44 Agent 登录、写入 token sink 并续期成功；07:32:00 target 为 up、lastError 为空 |
| 告警 | OpenBaoMetricsUnavailable、ClusterSecretStoreNotReady、多个 ExternalSecretNotReady、TooManyScrapeErrors | 07:32 仍有两条采集告警；08:16:42 Alertmanager 活跃告警列表为空 |

12 个对象为：`authelia/authelia-oidc-jwks`、`authelia/authelia-secrets`、
`backstage/backstage`、`cloudflared/cloudflared-tunnel`、`dynamic-runner/dynamic-runner`、
`gitea/gitea-db`、`gitea/gitea-hydra-oidc`、`hydra/hydra`、`monitoring/alertmanager-telegram`、
`nats/nats-auth`、`seaweedfs/seaweedfs-s3-config`、`zot/zot-s3`。

上述是同步链路故障，**不能等同于 12 个应用全部停机**；本次未逐一验证其业务请求。
没有观察到既有 Kubernetes Secret 被删除，也未读取其内容做数据审计。
Samba 整体退出还使 AD 身份服务不可用，但人类登录失败的次数及范围未测量。
告警已实际送达维护者；Telegram Secret 同步异常并不证明当时通知投递已失败。

## 时间线

| UTC | 事件与证据 |
| --- | --- |
| 06:36:09 | `apt-daily-upgrade` 启动 |
| 06:37:20–06:37:23 | APT 记录升级 `libssl3t64` 和 `openssl`，版本 `.15` → `.16` |
| 06:37:26 | systemd 停止 Samba；同窗口内多项服务停止并重新启动 |
| 06:37:28–06:37:29 | Samba 与 systemd-networkd 启动，后者重新配置 `enp1s0` |
| 06:37:30 | CLDAP/KDC 绑定 IPv6 地址失败；Samba 主进程退出，06:37:40 unit 标记 failed |
| 06:39:20 | `zot/zot-s3` 后续读到的 condition 转为同步错误 |
| 06:42:27 | ClusterSecretStore condition 转为 False |
| 06:48:00 | Alertmanager 记录 ClusterSecretStoreNotReady 开始；这不是通知实际送达时间 |
| 06:51:30 | OpenBaoMetricsUnavailable 开始 |
| 07:03:30 | TooManyScrapeErrors 开始 |
| 约 07:14–07:16 | 确认 Bao 直连健康、DNS 超时、ESO DNS 错误和采集 403 |
| 约 07:27 | SSH 到 DC，确认 Samba failed、无 DNS 监听；IPv6 地址已存在，磁盘与内存有余量 |
| 约 07:28:13 | 按维护者指令启动 Samba；DNS 和 Bao 域名访问恢复 |
| 07:28:15 | ClusterSecretStore 验证通过 |
| 约 07:30–07:31 | 对仍失败且引用 openbao store 的 ExternalSecret 添加 force-sync 注解，触发重新同步 |
| 07:31:35 | 12 个 ExternalSecret 全部 Ready |
| 07:31:44 | Bao 指标 Agent 自动重试登录成功，随后成功续期 |
| 07:32:00 | Bao 指标采集 up；稍后的告警查询仍有两条采集告警 |
| 08:16:42 | 报告阶段最终复核：Alertmanager 活跃告警为空 |

从 Samba 停止到 DNS 恢复约 **51 分钟**；到指标采集恢复约 **55 分钟**。
告警的精确清除时间未采样，不能将 08:16:42 当作服务恢复时间或告警实际清除时间。

## 故障机制与证据边界

```text
自动更新后的多服务重启窗口
  → Samba 启动时 IPv6 bind 失败 → Samba 整体退出 → DC DNS 不响应
  → Bao 域名无法解析
      → ESO 无法登录 → Secret 同步失败
      → 指标 Agent 无法登录 → 采集凭据不能恢复 → 指标接口 403
  → 多个下游告警
```

直接失败信息为 `NT_STATUS_ADDRESS_NOT_ASSOCIATED`，地址是
`fdd0:98df:15b0:10:5054:ff:fe2c:8778`，涉及 CLDAP 389 和 KDC UDP 88。
排查时此地址已正常存在；`systemctl show` 确认 `Restart=no`，unit 已包含
`After=network-online.target`。仅增加同样的启动依赖不能宣称已解决问题。

**最有证据支持的触发解释**是更新后的网络与 Samba 重启存在地址就绪竞态。
尚未捕获失败瞬间地址的 tentative 状态，也未定位发起每次重启的完整调用链，
不能断言为 OpenSSL 代码缺陷、已证明的 DAD 故障或 Samba 数据库损坏。

采集目标 URL 使用 IP，但 Agent 登录 URL 使用域名，因此仍依赖 DNS。
Agent 多次登录报解析错误；DNS 恢复后无需调整权限即可登录、续期和恢复采集，
支持旧采集凭据失效这一链路解释。未读取 token 或审计其精确失效原因，
所以不能把 token 到期时刻写成已确认事实。

## 根因层面的教训

1. **服务独立部署不等于依赖独立。** Bao 在 k3s 外运行仍通过单 DC 解析入口名，
   关键控制链路因 DNS 共因故障同时失效。
2. **多个 DNS 入口不等于冗余。** 若最终都依赖同一个 DC，前面增加副 resolver 仍不能
   容忍该 DC 离线。声明中的 CoreDNS 对 `ad.ddupan.top` 仅转发 `.5`，
   本机现场也将该域指向 `.5`；未逐台审计所有 LAN 客户端。
3. **缓存只是缓冲。** 本次设计验收必须覆盖冷启动和缓存过期，不能把热缓存的暂时成功
   当作权威数据或服务记录已有独立副本。
4. **自动恢复和可观测性有缺口。** Samba 一次启动失败即持续停机；本轮收到并查询到的
   告警以 Bao/ESO 下游症状为主，尚未证明 DC DNS 的直接探测与通知覆盖有效。
5. **短期恢复需要核对消费者。** DNS 先恢复，ESO 和 Agent 因退避稍后才恢复；
   单次 DNS 成功不足以结束验收，指标恢复也不等于告警立即清除。

## 短期优先整改：Samba 应能从暂态启动失败中自恢复

2026-09-30 维护者补充确认：DNS 冗余之外，应优先补上 Samba 自恢复。
本次不是必须人工修复配置或数据库才能启动：排查时 IPv6 地址已经存在，随后单次
`systemctl start samba-ad-dc` 即成功。`Restart=no` 把可能通过重试恢复的启动失败
延长成约 51 分钟的 DNS 中断，这是独立于 DNS 单点的第二个整改点。

短期通过 IaC 为 Samba 配置失败后自动重试、合理重试间隔与启动频率限制，并在持续
失败或触发限制时告警。既有 `After=network-online.target` 不能替代失败后重试。
具体重试间隔、次数和限流窗口须配套设计，确保正常地址就绪过程不会过早耗尽重试预算；
保留人工停止的维护语义，不建立无条件拉起服务的外部循环。

验收应重现一次地址暂未就绪导致的启动失败，确认地址恢复后无需人工 start/reset-failed
即可恢复 Samba、DNS 和依赖链；另测持续配置错误时重试受控且能告警。若就绪时间超过
重试预算，应明确限流后的恢复或升级处理路径，不能默认为会自行再次启动。

现有证据支持本次故障有自恢复条件，但未测量地址实际恢复时刻，不能承诺某组重试参数
一定覆盖了当时窗口。本项尚未实施或演练；自恢复缩短暂态故障，DNS 冗余继续覆盖
DC 长期故障及宿主离线，两者分别验收。

## 已实施处置

- 只读核对 DC 的服务日志、APT 历史、网络地址、监听、磁盘和内存。
- 执行 `sudo systemctl start samba-ad-dc`，未重启 VM、未改 Samba 数据库或配置。
- 验证 DC DNS、保留 TLS 校验的 Bao 域名健康接口及 ClusterSecretStore。
- 对仍失败的 11 个 OpenBao ExternalSecret 添加 `force-sync` 时间戳注解；
  `gitea/gitea-db` 已自动恢复。未手写或复制秘密值。
- 等待 Bao Agent 自动认证及采集恢复，最终复核告警清空。

## 后续整改与关闭标准

责任主体为 homelab 基础设施维护者；尚未建立本次专项 ticket，表格为整改建议和验收口径，
不代表部署完成或已选择实现技术。

| 优先级 | 动作 | 完成条件 |
| --- | --- | --- |
| P0（短期） | 为 Samba 启动失败加入受控自恢复 | IaC 管理重试、间隔、限流和失败通知；重现地址暂未就绪后验证无需人工恢复，并测试持续错误及超出重试预算的处理 |
| P1 | 设计并实施关键服务 DNS 冗余 | DC 离线时，LAN 与 Pod 仍能解析 Bao 等受保护服务名；覆盖冷启动、缓存过期与 UDP/TCP 53 |
| P1 | 消除备用 DNS 的共同故障依赖 | 备用具有独立服务记录来源/持久副本，放在不同宿主故障域；启动不要求先访问 Bao、AD 或故障中的 k3s |
| P1 | 为 DC DNS 建立直接监控 | 从 LAN 与 Pod 侧查询已知 A 记录及 AD SRV；能区分 DNS 根因与 Bao 进程/鉴权故障，并验证通知路径 |
| P2 | 完善升级后的健康验证 | 更新/重启后验证 DNS、LDAP/Kerberos、Bao 解析及消费者恢复；保留安全更新，控制重启时序 |
| P2 | 提升报告与告警可追溯性 | 记录通知时间、恢复时间和依赖关系，核查告警引用的 runbook 路径确实存在 |

### DNS 冗余方案的最小边界

- 先保护机器服务所需的静态记录，以 `infrastructure/dns/records.yml` 为声明来源，
  研究独立提供这些记录的双实例方案；明确同步、发布失败、旧版本继续服务和回滚规则。
  产品与地址未选定，不直接更改现有客户端或 DHCP。
- 保留 AD 动态记录的所有权。`_ldap`、`_kerberos`、DC locator 等不能用静态服务记录
  冒充，也不把独立 DNS 可用等同于 LDAP/Kerberos 高可用。
- 当前服务名位于 `ad.ddupan.top`，具体实现必须明确精确名称覆盖、子域拆分或受支持的
  复制方案及其边界；不能未经验证复制整个 AD zone、隐藏未知记录或假设 zone transfer 可用。
- 明确每类客户端如何到达两个 DNS 服务，测试超时、SERVFAIL 和单端不可用时的实际行为。
  仅在 DHCP 填两个地址不足以证明所有客户端和 CoreDNS 都能可靠切换。
- 初步验收目标：故障注入后 60 秒内恢复受保护服务名解析；DC 停机且备用冷启动时仍成功。
  此 60 秒为待设计验证的目标，不是既有 SLA；验证期间 Bao TLS 校验保持开启，
  ESO 与指标 Agent 可重新认证。还应测试任一 DNS 实例及其宿主下线。
- DNS 冗余整改与完整 AD HA 分别验收。第二个 DC 可以作为后续选项评估，但不是本次
  保护 Bao 等服务解析的前置条件。

**事故恢复已完成；只有 DNS 故障演练与相应监控、恢复保护通过后，才能关闭预防性整改。**

## 证据与关联资料

- 2026-09-30 当前排障与恢复会话的工具回执，未将含秘密的配置或 token 放入报告。
- DC：`journalctl -u samba-ad-dc`、`journalctl -u systemd-networkd -u apt-daily-upgrade`、
  `/var/log/apt/history.log`、`systemctl show samba-ad-dc`、`ip -6 addr`。
- Kubernetes：ESO condition 与日志、`bao-metrics-agent` 日志、vmagent `/api/v1/targets`、
  Alertmanager `/api/v2/alerts`；命令均未读取 Kubernetes Secret 内容。
- homelab-infra 工作区：`infrastructure/dns/records.yml`、`platform/k3s/coredns-custom.yaml`、
  `infrastructure/openbao/README.md`。部分来源有既有未提交修改，不代表已合并版本。
- [LAN DNS 与冗余目标](../services/lan-dns.md)、[Samba 恢复入口](../services/samba-ad.md)、
  [Pod DNS](../services/k3s-dns.md)、[架构约束](../architecture/constraints.md)。
- 当次告警引用 `guides/openbao-monitoring-maintenance.md`，本地 wiki checkout 不存在此文件；
  远端链接未验证，不能直接认定远端同样缺失。

本报告发布仅包含事故记录和整改目标；未改部署配置，尚无整改实现 commit 可关联。
