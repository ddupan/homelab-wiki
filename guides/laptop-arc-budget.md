---
title: laptop ARC 内存预算
last_reviewed: 2026-09-27
---

# laptop ARC 内存预算

laptop 同时运行 Kubernetes、数据库和 libvirt VM。维护者于 2026-09-27 明确批准
先将 ZFS ARC 上限设为 **4 GiB**，为应用和虚拟机保留突发余量。保留自动 ARC 下限。

## 当前配置与验证

2026-09-27 已在线应用 `zfs_arc_max=4294967296`，持久文件为
`/etc/modprobe.d/homelab-zfs-arc.conf`，并更新所有已安装内核的 initramfs。
没有重启主机、卸载 ZFS 或重启业务。现场 `arcstats` 的 `c`、`c_max` 均为
4294967296，`c_min` 保持 1038999680；随后 ARC 实际使用量约 3.75 GiB，
内存 PSI 的 10/60/300 秒窗口均为 0。这个即时结果不等于已经验证下一次更新负载。

配置源码和回滚操作见
[PR #165](https://git.ddupan.top/panxiao81/homelab-infra/pulls/165) 的
[Ansible play](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/06943d4c6583f1b62fea6176b56f237da54a12e7/infrastructure/host-memory/laptop-arc.yml) 与
[操作说明](https://git.ddupan.top/panxiao81/homelab-infra/src/commit/06943d4c6583f1b62fea6176b56f237da54a12e7/infrastructure/host-memory/README.md)。
现场已部署，PR 已于 2026-09-27 合并至 main；合并提交为
[06943d4](https://git.ddupan.top/panxiao81/homelab-infra/commit/06943d4c6583f1b62fea6176b56f237da54a12e7)。

## 为什么设置预算

2026-09-26 17:13–17:21 UTC，Gitea RunnerService 请求超过内网 Envoy 的 15 秒超时。
集中日志确认其中一次 Declare 请求在 Gitea 内耗时约 45.5 秒。
同期宿主机发生内存回收、换页与 I/O 压力，ARC 从约 3.8 GiB 增至 5.8 GiB，
当时自动上限约 15.5 GiB。数据库、DNS 与控制面都有延迟迹象。

进程指标 `vm:winadmin` 写入由约 0.04 MiB/s 升至约 5.8–7.5 MiB/s，
与虚拟磁盘 `zd128` 对应。Windows 任务日志确认 Edge 自动更新在
17:10:59 开始、17:20:55 结束，期间有安装/AppX 活动。多层证据支持它是重要触发负载，
但没有 Windows 进程级 I/O 历史，不能宣称已证明唯一原因。

排查优先使用已有 process-exporter：QEMU 按 VM 名分组，支持 PSS、SwapPss 和 I/O。
进程 I/O 计数可能包含退出子进程的记账，containerd-shim 突跳不能直接解释为实时盘吞吐。
宿主机物理盘、zvol、进程指标需相互验证，不能相加。

## 后续观察

从 [Grafana](../services/grafana.md) 的 Homelab 内存与 Swap 面板查看 ARC、PSI 与换页，
对照 winadmin 下次自动更新及数据库延迟。必要时再调整缓存预算或 VM I/O 策略。
当前未改变 runner fail-fast、Windows 自动更新、swap 或 VM I/O 上限。
ARC 上限不是 ZFS 全部内存的硬上限；已有 swap 占用不会因为降低 ARC 自动清零。
