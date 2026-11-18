---
title: 笔记本重启后检查
last_reviewed: 2026-11-18
watch:
  - homelab-infra:infrastructure/shared-postgresql/switchover.py
  - homelab-infra:infrastructure/openbao/README.md
  - homelab-infra:infrastructure/host-services/
  - homelab-infra:apps/backstage/
  - homelab-infra:apps/netboot/compose.yaml
---

# 笔记本重启后检查

## 什么时候用

笔记本（192.168.10.127）重启或意外断电之后，不管是计划内还是意外。它同时是 k3s、NFS、
libvirt（DC、OpenBao）和 netboot 主机，重启后有几件事不会自己恢复。

按下面的顺序检查：后面的服务依赖前面的。每一项只在检查结果异常时才需要处理。

如果 Proxmox 节点也一起重启过，做完这篇再看最后的 [Proxmox 节点也重启过](#proxmox-节点也重启过)。

## 先确认

以下命令都在笔记本上，以自己的账号执行。

**1. DNS**

```bash
cat /etc/resolv.conf
```

正常：只有一行 `nameserver 192.168.10.127`。如果内容是 Tailscale 的 `100.100.100.100`，
或者文件为空，见下面步骤 1。

**2. k3s 的 Pod**

```bash
kubectl --context default get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded
```

正常：开机几分钟后列表为空，或者只剩几个刚创建、很快结束的 Job。大量 Pod 一直 `Pending` /
`ContainerCreating`，基本是 DNS 问题，回到第 1 项。

**3. OpenBao 是否已解封**

```bash
curl -s https://bao.lab.ddupan.top:8200/v1/sys/seal-status | python3 -c 'import json,sys; print(json.load(sys.stdin)["sealed"])'
```

正常：`False`。bao 从 TPM 自动解封，不需要人工操作。

**4. 生产 PostgreSQL 的主库在哪里**

```bash
sudo -u pgprod /opt/homelab-patroni/bin/patronictl -c /etc/homelab-postgresql/prod/patroni.yml list
```

正常：`Leader` 是笔记本上的成员。重启后它**几乎一定**切到了 `pg-pve1`（HDD，慢），
同时会触发告警 `SharedPostgresPrimaryOnStandbyHost`。

**5. Backstage**

```bash
kubectl --context default -n backstage get pod
```

正常：`READY 1/1`。如果启动 5 分钟后仍是 `0/1`，就是卡在半启动状态了。

**6. 失败的 systemd 单元**

```bash
systemctl --failed
```

正常：没有输出。

## 操作步骤

**1. 修复 DNS**（第 1 项异常时）

```bash
echo 'nameserver 192.168.10.127' | sudo tee /etc/resolv.conf
```

Pod 会在几分钟内自己重试并恢复，不需要重启 k3s。

**2. 解封 OpenBao**（第 3 项为 `True` 时）

自动解封失败，说明 TPM 那一侧出了问题，不是例行情况。先看日志：

```bash
ssh ansible@192.168.10.8 sudo journalctl -u openbao -b --no-pager | tail -50
```

然后在插着 YubiKey 的机器上（不能通过 ssh 在笔记本上执行，转发的 agent 无法解密），
在 homelab-infra 仓库根目录执行：

```bash
infrastructure/openbao/unseal.sh    # 按提示触摸 YubiKey，输出 unsealed
```

TPM 被清空或更换的情况，按 homelab-infra `infrastructure/openbao/README.md` 的
"TPM seal" 一节恢复。

**3. 把 PostgreSQL 主库切回笔记本**（第 4 项 Leader 不在笔记本时）

切换会让生产写入中断几秒（演练实测约 9 秒），所以先确认没有正在进行的重要写入。
在笔记本上、homelab-infra 仓库根目录执行：

```bash
python3 infrastructure/shared-postgresql/switchover.py          # 只做预检，看输出是否满足条件
python3 infrastructure/shared-postgresql/switchover.py --run    # 真正切换
```

**4. 重启卡住的 Backstage**（第 5 项异常时）

它在共享 PostgreSQL 就绪之前启动，所有插件都初始化失败，但进程不退出。删掉 Pod 让它重建：

```bash
kubectl --context default -n backstage delete pod -l app.kubernetes.io/name=backstage
```

不要用 `kubectl rollout restart`：它会给 Deployment 留下 Flux 不认识的注解。

**5. 处理失败的 systemd 单元**（第 6 项有输出时）

以下几个是已知的、每次重启都可能出现的，确认后清掉状态即可：

| 单元 | 原因 |
|---|---|
| `systemd-networkd-wait-online.service` | netplan 还配置着一块已经不在的 USB 网卡 |
| `nvidia-cdi-refresh.path` / `.service` | NVIDIA 驱动与库版本不一致，下次重启通常会好 |

```bash
sudo systemctl reset-failed systemd-networkd-wait-online.service nvidia-cdi-refresh.path nvidia-cdi-refresh.service
```

不在这张表里的单元是新问题，用 `journalctl -u <单元> -b` 查看原因。
**不要停用 `systemd-networkd`**：它管理 `br0`，停掉会让整个实验室断网。

**6. netboot**

```bash
cd ~/services/apps/netboot && docker compose ps
```

容器没在运行就执行 `docker compose up -d`。如果报错说 `dnsmasq.conf` 是目录，
说明 compose 是从旧路径启动的、自动建了空目录：删掉旧路径下的空目录，从上面这个目录重新 `up -d`。

## 验证

把"先确认"里的 6 条命令再执行一遍，结果都应该是正常值。之后 15 分钟内，
Grafana 的告警列表里不应再有 `HostSystemdUnitFailed`、`SharedPostgresPrimaryOnStandbyHost`
或任何探针告警。

### Proxmox 节点也重启过

在 pve1 上检查：

```bash
ssh root@192.168.10.4 linstor node list
ssh root@192.168.10.4 ha-manager status
```

正常：所有节点 `Online`；`vm:100` 为 `started`。

- 某节点是 `EVICTED`：它的存储副本全部失效，上面的 LXC 和 `vm:100`（路由器）会起不来，
  而且**目前没有告警**。执行 `ssh root@192.168.10.4 linstor node restore <节点名>`。
- `vm:100` 是 `error`：先修好上一条，再执行

  ```bash
  ssh root@192.168.10.4 ha-manager set vm:100 --state disabled
  ssh root@192.168.10.4 ha-manager set vm:100 --state started
  ```

## 回滚 / 升级

- 主库切换失败：`switchover.py` 预检不通过时不会切换，按它的输出处理；切换后出错，
  Patroni 会自己选出新主库，再执行一次预检看状态。
- DNS 改完 Pod 仍然起不来、bao 无法解封、或者 `linstor node restore` 后仍有副本不同步：
  停止操作，不要继续重启别的服务——这几样是其他所有服务的根。
