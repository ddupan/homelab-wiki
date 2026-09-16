---
title: Gitea 与 Actions 使用指南
lifecycle: active
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# Gitea 与 Actions

Gitea 托管 homelab 的代码、文档、issue 和 PR；Actions 执行仓库声明的 CI workflow。
入口为 <https://git.ddupan.top>，人类登录使用 [Authelia](authelia.md)。

本页依据现有服务 README、runner README、仓库 workflow 和官方使用文档整理。
本轮没有重新验证登录或运行示例；下面的操作是使用指南，不是本轮执行记录。

## 登录并找到项目

1. 打开 Gitea，选择已配置的 Authelia/OIDC 登录入口。
2. 在 Authelia 完成认证，返回 Gitea；应用权限由 Gitea 账号和仓库授权决定。
3. 打开目标仓库：Code 看源码，Issues 看动态工作，Pull Requests 看待合并改动，Actions 看 CI。

登录成功但看不到仓库时，先确认当前账号与仓库权限；OIDC 登录本身不会赋予所有项目的管理权。
已有账号应沿用原账号关联，遇到关联问题交由管理员处理，不另建同名账号规避。

## 创建与修改仓库

通过页面的 New Repository 创建仓库，选择所属用户或组织、名称及可见性。
仓库里的 Clone 按钮提供当前准确的 HTTPS/SSH 地址，复制该地址到 Git 客户端即可。
浏览器的 OIDC 会话不直接充当 Git 命令行凭据；客户端使用自己的凭据管理或已登记 SSH key。

日常修改先建分支、提交并推送，再开 PR 合并到 main。PR 应说明最终行为与验证结果，
不要把本机未提交的其他工作一并带入。基础设施仓库默认以中文维护 commit、PR 和文档。

## 第一个 CI workflow

在可信的测试仓库中启用 Repository Actions，再添加 `.gitea/workflows/hello.yaml`：

```yaml
name: Hello
on: [push]
jobs:
  hello:
    runs-on: [self-hosted, pod]
    steps:
      - name: Check execution
        run: echo 'homelab CI is running'
```

推送该文件后，进入 Actions，打开本次运行和 hello job。
预期看到输出 `homelab CI is running` 且 job 成功；示例不需要检出源码或读取秘密。
若仓库设置没有 Actions 开关，先确认自己的管理权限。
workflow 路径、启用方式与事件规则见 [Gitea 官方入门](https://docs.gitea.com/usage/actions/quickstart/)。

维护者于 2026-09-16 说明：动态 `pod` 已上线测试，系统总并发量为 4；
纯 `self-hosted` runner 准备退役，新 workflow 使用明确的动态环境 labels。
本例据此采用 `[self-hosted, pod]`，本轮未实际运行示例。
若任务排队，除 runner 在线状态和 labels 外，也要考虑系统并发容量，不能把入队当作执行成功。

## 选择 runner

| 需求 | 使用入口 |
|---|---|
| 动态 Pod：已上线测试 | `[self-hosted, pod]`；系统总并发 4，不是每个仓库各有 4 个名额 |
| 动态 VM：正在工作 | `[self-hosted, vm]`；系统总并发 1，具体可用范围和进度以项目文档为准 |
| 旧常驻 runner：准备退役 | 纯 `self-hosted`，不再作为新 workflow 的默认示例；已有 workflow 需按需求迁移到明确的 Pod/VM 接口 |

上述阶段与容量由维护者于 2026-09-16 提供。实现与后续变化见
[Dynamic Runner](gitea-dynamic-runner.md) 及其项目文档。

常驻 runner 使用 privileged DinD，README 明确限定可信 workflow；不要为不可信代码开放它。
动态 runner 提供环境及获取自身 SPIFFE 身份的能力；登录下游、请求 token 和凭据清理由 workflow 负责。

## 遇到问题先看哪里

- 没有触发：看 Actions 是否启用、文件是否位于正确路径、事件是否匹配此次推送。
- 一直排队：看仓库可用 runner、在线状态和 labels；动态 runner 的问题回到其项目文档。
- job 失败：打开具体 step 的日志，从第一个失败步骤排查，不只看最终退出码。
- Git 命令失败但网页能登录：分别检查 Git 使用的身份、凭据方式和仓库权限。

服务部署与升级恢复以 homelab-infra `apps/gitea/README.md` 为入口；常驻 runner 以
`platform/gitea-runner/README.md` 为入口。本页不复制 token、密码或部署命令。
