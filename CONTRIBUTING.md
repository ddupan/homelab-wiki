# 文档维护规则

## 这个库给谁看

**wiki 写给人看**，由人和 AI 共同维护。各源码仓库的 README / `AGENTS.md` 写给 AI 和改代码的人，
讲实现细节与陷阱；wiki 不复制它们，需要原理时链接过去。

判断一段内容该放哪里：

| 内容 | 位置 |
|---|---|
| 出了状况怎么处理、计划内的运维操作 | wiki `sop/` |
| 怎么使用一个服务（入口、登录、第一次使用） | wiki `services/` |
| 跨服务的任务（发布新服务、写 CI） | wiki `guides/` |
| 跨服务的设计约束、事故复盘 | wiki `architecture/`、`incidents/` |
| 某个配置为什么这样写、改代码会踩的坑 | 源码仓库 README / `AGENTS.md` |
| 进行中的工作 | 源码仓库的 issue / PR |

## 怎么写

- **按读者要做的事来组织，不按系统结构。** 标题写"Bao 被 seal 了怎么办"，不写"OpenBao seal 机制"。
- **正文只写读者需要的内容。** 不写"本页依据……整理""本轮未查询现场"这类整理过程；
  来源、验证状态放进 frontmatter（见下文），正文最多在末尾用一句话说明状态。
- **命令可以直接复制。** 写明在哪台机器、以哪个身份执行；需要替换的值用 `<尖括号>` 标出。
- **写出预期结果。** 每条检查命令都说明正常时输出什么样。
- 凭据只写取得方式和存放位置，不写值。
- 中文正文；命令、配置键和上游专有名词保留原文。

### SOP

放在 `sop/`，从 [templates/sop.md](templates/sop.md) 复制，必须包含模板中的五个小节：
什么时候用、先确认、操作步骤、验证、回滚 / 升级。新增的 SOP 要加进 [sop/index.md](sop/index.md)。

SOP 从实际处理过的事情里提炼，不凭空预写。处理完一次事故或一次计划操作后，
在同一次工作中新建或更新对应的 SOP；告警的 `runbook_url` 指向 SOP 的对应小节。

### 服务页

放在 `services/`，从 [templates/service.md](templates/service.md) 复制；新增或退役时同步
[services/index.md](services/index.md)。退役的服务页标为 `lifecycle: retired`，开头写明替代方案。

## frontmatter

```yaml
---
title: 页面标题
last_reviewed: 2026-11-18   # 最近一次按现状核对正文的日期
watch:                      # 本页依赖的源码路径，变化后会提示复核
  - homelab-infra:infrastructure/openbao/
  - homelab-cookbooks:cookbooks/homelab_bao/
---
```

服务页另有 `lifecycle`（planned / experimental / active / retired / unknown）、
`evidence`（configuration / documented / live-verified）和 `last_verified`（最近一次现场验证日期，
没有验证写 null，不能因为编辑文字就刷新）。`sources` 是可选的自由文本来源列表。

### `watch` 与过时提醒

`watch` 中每项为 `<仓库>:<路径>`，仓库默认属于 Gitea 的 `panxiao81`，其他所有者写成 `<所有者>/<仓库>:<路径>`；
已迁到 GitHub 的仓库（在 Gitea 上归档且网站指向 github.com）自动改查 GitHub，`watch` 不用改。
路径可以是目录。定时任务 [stale.yml](.github/workflows/stale.yml) 每周查询这些路径在
`last_reviewed` 之后的提交（跳过 Renovate 依赖升级与 merge commit），把需要复核的页面汇总到一个
固定 issue「文档待复核」。路径已不存在的也会列出，通常表示代码搬了家。

复核时对照列出的提交修改正文，然后更新 `last_reviewed`；内容不受影响时也只更新日期。
没有对应源码的页面（例如纯人工流程）可以不写 `watch`。

## 一次变更应更新哪里

| 变化 | 要看的页面 |
|---|---|
| 使用入口、认证、权限、客户端参数 | 对应 `services/` 页面；入口变化同时更新服务总览 |
| 新增或退役组件 | 服务页、`services/index.md`；任务入口变化再改 `guides/task-index.md` |
| 处理了一次故障或做了一次运维操作 | 对应 SOP；没有就新建 |
| 跨服务设计或边界 | `architecture/constraints.md` 及受影响的页面 |
| 只有开发进度变化 | 不改 wiki，记在源码仓库的 ticket |

先改最接近事实的页面，再同步导航；同一套操作不在多处复制。

本 wiki 的修改在检查通过后直接提交并推送 `main`，无需 PR（维护者 2026-09-27 约定）；
代码仓库仍按各自约定走分支和 PR。不得跳过检查，也不得覆盖其他工作区的修改。

## 本地与 CI 检查

需要 Python 3.10 或更新版本：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-docs.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_docs.py
git diff --check
```

[docs.yml](.github/workflows/docs.yml) 在 push、PR 和手动触发时于 GitHub 托管 runner 运行同样的检查。
检查器离线运行，检查内容：

- 相对链接、图片、引用式链接与标题锚点；不探测远端 URL。
- frontmatter 的类型、重复键、枚举值、日期，`live-verified` 必须有验证日期，`watch` 的格式。
- 服务页字段齐全且被服务总览链接；SOP 包含五个必需小节且被 SOP 索引链接。

标题锚点按 Gitea/GitHub 规则处理中文；需要特殊字符锚点时用 HTML `id`。
检查器不证明命令正确、外链可达、事实最新或服务健康。
