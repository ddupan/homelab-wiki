---
title: OpenEBS PVC 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# OpenEBS 本地持久存储

应用通过 PVC 申请持久存储。homelab 使用的 StorageClass 为 `localpv-zfs-ceph`，
provisioner 为 `zfs.csi.openebs.io`，底层来自宿主 `data/ceph` ZFS pool/dataset。
名称中的 `ceph` 不代表它提供 Ceph 分布式存储能力。

本页依据 homelab-infra `platform/openebs/README.md` 与 `storageclasses.yaml` 整理，
未查询 PVC、宿主存储或现场容量。源码 README 的历史消费者列表包含已退役项目，
当前服务归属以[服务总览](index.md)为准，不照抄为现役卷清单。

## 为应用声明 PVC

先确定容量、namespace、备份需求及应用调度约束。
以下在应用已有 namespace 中申请 1 GiB，容量和名称需按实际用途替换：

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: your-app-data
  namespace: your-app
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: localpv-zfs-ceph
  resources:
    requests:
      storage: 1Gi
```

在应用 Pod spec 中引用该 PVC，容器再用 `volumeMounts` 挂载：

```yaml
volumes:
  - name: data
    persistentVolumeClaim:
      claimName: your-app-data
```

```yaml
volumeMounts:
  - name: data
    mountPath: /var/lib/your-app
```

后两段分别是 Pod 与容器配置片段，不是独立 Kubernetes 对象。
应用与 PVC 必须位于同一 namespace；挂载路径及文件权限以应用要求为准。
把声明纳入应用既有的 GitOps/部署入口，本轮未创建或挂载 PVC。

## 等待绑定与节点约束

StorageClass 配置 `WaitForFirstConsumer`，PVC 在没有可调度消费者时保持 Pending 不一定是故障。
检查时结合消费 Pod 的调度事件、StorageClass、节点与存储池容量，不能通过删除重建业务 PVC 试错。
此为节点本地存储，数据可用性依赖对应宿主；应用不能假设跨节点重调度后自动获得同一份数据。
绑定与回收语义参见 [Kubernetes StorageClass 文档](https://kubernetes.io/docs/concepts/storage/storage-classes/)。

## 扩容、删除与恢复

配置允许卷扩容，但扩容需要按 CSI、文件系统和应用要求确认结果；不要将其理解为支持任意缩容。
默认 `reclaimPolicy: Delete`：删除 PVC 可能触发其 PV 与底层数据删除，
实际处理还应检查该 PV 自身的回收策略。应用退役前需明确数据保留或删除决定。

本地持久卷不是独立备份，也不自动提供多副本高可用。
为数据库等应用选择备份和恢复方式时，需考虑应用一致性及宿主故障，而不只看 PVC 是否 Bound。

运维与 break-glass 入口为 `platform/openebs/README.md`。
StorageClass 独立于 Helm release 管理；不要通过卸载 chart、删除 CRD 或业务卷验证升级。
依赖包括 OpenEBS ZFS CSI、宿主 ZFS、文件系统与 Kubernetes 调度。

来源文件的固定版本与工作区差异见[来源追溯](../sources.md#openebs)。
