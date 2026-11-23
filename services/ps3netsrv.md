---
title: ps3netsrv 使用指南
lifecycle: active
evidence: configuration
last_reviewed: 2026-11-23
last_verified: null
watch:
  - homelab-infra:apps/ps3netsrv/
---

# ps3netsrv

为 PS3 客户端通过网络读取游戏内容提供服务。
以 Docker Compose 运行在笔记本（192.168.10.127）上。

## 入口与内容目录

| 项目 | 配置记录 |
|---|---|
| 镜像 | `shawly/ps3netsrv:latest` |
| TCP 端口 | 宿主 `38008` → 容器 `38008` |
| 宿主内容目录 | `/mnt/pool/games/ps3` |
| 容器内目录 | `/games`，当前映射为读写 |

客户端填写服务器地址 `192.168.10.127`、端口 `38008`。
这不是浏览器 HTTP 服务，也不能将路径挂载成功等同于客户端已发现内容。

## 第一次从 PS3 浏览内容

1. 确认目标内容已放入宿主映射目录，且容器配置的用户具有读取权限。
2. 按客户端要求组织子目录，例如 ISO 内容位于 `PS3ISO/`，目录形式内容位于 `GAMES/`。
3. 在 webMAN MOD 的网络内容设置中填入服务器地址和端口 `38008`，启用对应网络内容扫描。
4. 刷新内容列表，选择一个条目挂载并读取，确认整个客户端路径。

目录结构见 [容器项目说明](https://github.com/shawly/docker-ps3netsrv)，客户端操作见
[webMAN MOD PS3 NET Server](https://github.com/aldostools/webMAN-MOD/wiki/~-PS3-NET-Server)。
不同客户端版本的菜单名称可能不同。

## 排障与维护边界

- 无法连接：先在笔记本上确认容器在运行（`docker ps | grep ps3netsrv`），再核对客户端到笔记本的网络。
- 列表为空：核对宿主目录、子目录结构、文件权限与客户端扫描设置。
- 发现内容但读取失败：核对文件可读性及客户端格式支持，再看服务日志。

Compose 的 `USER_ID` / `GROUP_ID` 控制容器读文件时的身份；调整前核对宿主所有权，
不要为排障递归修改整个存储池的权限。挂载目录属于内容数据，重建容器不会替代数据备份。
依赖为 Docker、宿主存储、网络和相容客户端。
