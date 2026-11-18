# AI 在本 wiki 的工作规则

**这个库主要给人看。** 写作规则见 [CONTRIBUTING.md](CONTRIBUTING.md)，本文件只放 AI 的工作流程。
实现细节和陷阱属于源码仓库的 README / `AGENTS.md`，不要搬进 wiki。

先读 README.md，按 guides/task-index.md 或 sop/index.md 找到相关页面；不要一次读入整个仓库。

## 写作

- 正文写给人：按任务组织，命令可以直接复制，写出预期结果。不在正文里叙述你的整理过程、
  查阅范围或"本轮未验证"——来源、验证状态放进 frontmatter。
- SOP 用 templates/sop.md。从真实处理过的事件提炼；在源码仓库处理完一次故障或运维操作后，
  主动在这里新建或更新对应的 SOP。
- 页面依赖源码时在 `watch` 中列出路径，好让过时检查找到它。

## 事实与验证

- 区分设计、配置、部署记录与现场验证。没有访问现场，不得写"运行正常"。
- `last_verified` 只在完成所述现场验证后更新；`last_reviewed` 在按现状核对正文后更新。
- 查询服务现状前先问维护者哪些工作正在进行、由哪个 ticket 跟踪。已有明确授权的范围不必重复询问；
  不能从一个项目扩大到其他项目或现场查询。
- Samba AD、OCI、Proxmox 以 IaC 代码为配置依据（维护者指定），读代码无需再问；现场查询仍需授权。
- ticket open 不等于尚未部署；README 与 ticket 不一致不能直接认定为运行异常。
- 架构约束变更要写明旧规则、新规则和原因，不得静默删除约束来迁就实现。
- 凭据只记录取得方式和存放位置，不复制密码、token、私钥、state 或含敏感值的输出。

## 处理「文档待复核」issue

逐页对照 issue 列出的提交：影响正文就改正文，然后更新 `last_reviewed`；不受影响只更新日期。
路径已不存在时，找到代码的新位置并更新 `watch`。

## 提交

运行 `python3 scripts/check_docs.py`；修改脚本时运行 `python3 -m unittest discover -s tests -v`。
检查通过后直接提交并推送 main，无需 PR；不要覆盖其他工作区的修改。
