# AGENTS.md

## 仓库用途

这个仓库用于发布和维护一个以文档为先的前端项目分析 skill。

## 入口路由

- 如果任务是 Persona 定义、Story Map、页面映射、Feature 拆分、GWT 编写或 Feature Spec 生成，优先使用根目录的 [SKILL.md](SKILL.md)。
- 对于这条工作流，把 [references/methodology.md](references/methodology.md) 视为方法论唯一依据。
- 轮次流程、模板和质量门放在根目录 skill 的 `references/` 中，不放在这个文件里。
- 归属判断先看 [references/document-map.md](references/document-map.md)。

## 持久规则

- 默认产出是文档，不是实现代码。
- 关系密集型内容优先放在索引文件或矩阵文件中，不要塞满实体文件。
- 优先保持小文件和渐进式披露；Markdown 文件在可行情况下尽量控制在 200 行以内。
- 保持这个文件简短；可复用的多步工作流放到根目录 skill 及其 `references/` 中。
- 专业术语如 `Persona`、`Story Map`、`Feature`、`Feature Spec`、`Happy Path`、`Edge Case`、`Permission Case`、`Error Case` 保持英文，不翻译为中文。

## 分层约束

- `AGENTS.md` 只放仓库级、长期有效的元规则，不放具体 workflow 步骤。
- `references/` 放规范、语义、契约、索引、方法论和决策依据。
- `runbooks/` 放可执行的操作流程、维护步骤和发布步骤。
- 如果某条内容是在描述“是什么”或“为什么”，优先放 `references/`。
- 如果某条内容是在描述“怎么做”，优先放 `runbooks/`。
- 如果某条内容是在约束 AI 下次不要再犯错，优先写成 `AGENTS.md` 中的短规则，再在 `references/` 里补充定义或依据。
- 不要把 `SKILL.md` 的 workflow、round、template、quality gate 内容搬进 `AGENTS.md`。
- 如果 `AGENTS.md` 与 `SKILL.md`、`references/*`、或 `runbooks/*` 出现冲突，先保持 `AGENTS.md` 简短，以更高层文档的约定为准。
