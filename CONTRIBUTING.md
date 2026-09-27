# 文档维护规则

## 查询前先对齐

查询项目状态前，先询问维护者正在进行的工作、跟踪 ticket 和尚未成文的现状。
已有明确授权则在该范围内继续，不重复询问；文档查询授权不自动扩展为现场检查。
2026-09-16 维护者指定 SPIFFE/SPIRE 基本以 homelab-infra #34 的记录为依据；
本轮仅查该 ticket 及其直接引用的 runbook，没有查询现场。其他项目仍需先询问。

2026-09-16 维护者指定 Samba AD、OCI、Proxmox 优先 IaC、以代码为准。
可直接核对其仓库中的配置与任务，README 与代码不一致时优先解释代码；此授权不等于现场变更或验收。

稳定设计与使用方法放知识库，动态进度链接到 ticket。知识库只保留注明查阅日期的阶段摘要，
不复制维护第二份实时任务列表。issue open 可能表示后续阶段未完成，不能据此推断基础服务未部署。

## 状态与证据

分别记录服务生命周期和验证程度，避免一个“完成”掩盖多个状态：

- 生命周期：planned（计划）、experimental（试验）、active（投入使用）、retired（退役）、unknown（未知）。
- 证据：configuration（仅配置）、documented（已有实施记录）、live-verified（现场验证）。
- 存在冲突时明确标记 conflict，并链接待核实项；不按文件日期自动决定谁正确。

设计另用 draft / accepted / implementing / implemented / superseded 表示进度；
accepted 不代表部署完成，implemented 必须附实现和验收依据。

`last_reviewed` 是文档审阅日期；`last_verified` 是对应运行事实的最近核实日期。
没有核实就写 null。历史验证要说明日期、范围和来源，不能冒充本轮验证。

## 一项工作的完成条件

1. 先按上述规则对齐查询范围，再读取服务文档、相关 ticket 和约束，区分动态工作与事实冲突。
2. 实施和必要验证后，同步用途、入口、使用方法、依赖和恢复步骤中的变化。
3. 新增或退役服务时更新服务总览；退役文档保留替代入口和原因。
4. 代码与文档分属仓库时互相链接 commit/PR；未部署或未同步的部分明确写出。
5. 报告分别说明已实施、已验证、仍待完成的内容。

新增服务至少提供一次真实的使用路径。部署步骤不等于使用说明；不能只有 Helm/Compose 命令。
页面上半部分面向使用者，下半部分说明运维和证据。

## 来源与归属

每份事实只维护一个权威正文位置，其他页面链接到它。链接源码时标明仓库与路径；
历史验收尽量使用 commit permalink，现状入口可指向默认分支。引用未提交工作区时明确标记，
合并后补正式链接。禁止把所有来源路径一律转换成可能不存在的远端链接。

发生冲突时在 verification.md 记录两边来源、影响、核实方法和结果。核实完成后更新权威
文档及引用它的总览，保留决策原因；不要长期维护两种“现状”。

## 格式与检查

使用普通 Markdown 链接、相对附件路径和文字说明；关键事实直接写入正文。
可选 Obsidian 编辑，个人布局、缓存、插件和同步配置不提交。对外分享前检查敏感内容。
提交前检查相对链接、服务目录覆盖，以及新增内容是否混淆计划和运行事实。


## 一次服务变更应更新哪里

| 变化 | 必须查看的文档 |
|---|---|
| 使用入口、认证、权限、客户端参数 | 对应 `services/` 页面；入口变化同时更新服务总览 |
| 新增或退役组件 | 服务页、`services/index.md`；任务入口变化再改 `guides/task-index.md` |
| 跨服务设计或边界 | `architecture/constraints.md` 及受影响指南 |
| 只有开发进度变化 | 原项目 ticket；wiki 仅在阶段摘要需要变化时更新并注明日期 |
| 取得新的验证结果 | 服务页说明日期与验证范围，据实更新 `last_verified` |
| 工作区来源已合并 | 核对实际内容后更新 `sources.md` 的固定链接及差异标记 |

先修改最接近事实的页面，再同步导航，避免把同一套操作复制到多份文档。
无需每次修改都更新首页、所有服务页或整个来源索引。
原仓库 README 同步按维护者要求暂缓，不阻塞 wiki 的维护。

按维护者 2026-09-27 的明确约定，本 Wiki 的修改完成检查后直接提交并推送 `main`，
无需创建 PR。此规则仅适用于 Wiki；代码仓库仍按各自约定新建分支并提交 PR。
不得跳过文档检查或覆盖其他工作区修改。

## 本地与 CI 检查

需要 Python 3.10 或更新版本；首次在 wiki 根目录准备环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-docs.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_docs.py
git diff --check
```

依赖版本固定在 [requirements-docs.txt](requirements-docs.txt)。安装依赖需要网络，检查器本身离线运行。
Gitea 工作流 [.gitea/workflows/docs.yml](.gitea/workflows/docs.yml) 在 main push、PR 和手动触发时运行，
使用 `[self-hosted, pod]` 的 Python 虚拟环境；无需业务秘密或集群权限。
不设置 job `container`：此次 Pod runner 日志确认没有 Docker socket，额外启动 job 容器会在检查前失败。
CI 获取 checkout action 和依赖仍需要对应网络可用。

检查范围：

- Markdown 的相对文件链接、图片、引用式链接及本地标题锚点；不探测远端 URL。
- frontmatter 的类型、重复键、状态枚举、日期与 `live-verified` 必须有验证日期的约束。
- `services/` 下的服务页必须有完整状态字段，并由服务总览链接；总览及外部消费者范围页除外。
- 已有 frontmatter 的其他页面校验 title 和审阅日期；`templates/` 允许日期占位为 null。

标题锚点按常见 Gitea/GitHub 规则处理中文、字母、数字、连字符和重复标题。
需要特殊字符锚点时可声明 HTML `id`，不要依赖 Obsidian 插件或非标准 heading 属性。
代码块和行内代码里的路径是示例或说明，不当链接执行或检查；源码路径的存在性由 `sources.md` 的明确核对维护。
检查错误带文件与行号，但不打印原始 frontmatter 内容。

检查器不证明命令正确、外链可达、事实最新或服务健康，也不自动获取凭据或执行文档中的示例。
