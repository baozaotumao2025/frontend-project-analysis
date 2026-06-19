# Frontend Project Analysis

`frontend-project-analysis` 是一个以文档为先的前端项目分析 skill，同时内置一套可复用的 Python 工作流基础设施。这个 skill 安装在 Codex 环境中运行，不要求目标项目复制一整套工具脚手架。它把前端项目拆解成 `Persona`、`Story Map`、`Page`、`Feature`、`GWT` 和 `Feature Spec` 等结构化产物，并用 SQLite 记录依赖、审核、版本和审计信息。

当前发布版本为 `1.3.1`。

## 快速开始

如果你想先跑通一条最小路径，先准备你自己的 brief 文件，再按这个顺序来：

```bash
uv sync
uv run fpa brief confirm --input ./project-brief.md --output ./project-brief.confirmed.md
uv run fpa init --project crm-web --name "CRM Web" --brief-file ./project-brief.confirmed.md
uv run fpa artifact add --project crm-web --type persona --slug sales-rep --title "Sales Rep"
uv run fpa review structural --project crm-web --artifact persona:sales-rep
```

## 两种使用方法

你可以用两种方式使用这个 skill：

1. 命令式使用
   - 适合熟悉 CLI 的用户
   - 直接运行 `uv run fpa ...` 命令完成初始化、录入、审查、导入导出和维护
2. 自然语言使用
   - 适合不想记命令的用户
   - 直接告诉 Codex 要做哪一轮分析、输入是什么、输出要落到哪些文件
   - Codex 会结合 `SKILL.md`、`references/methodology.md` 和本仓库文档自动推进流程
   - 你也可以用多轮对话逐步补充项目背景，等信息足够完整后先执行 `uv run fpa brief confirm ...`，再执行 `uv run fpa init ...`
   - 如果你不知道怎么写 brief，可以先运行 `uv run fpa brief interview --output ./project-brief.md`；如果你想让 LLM 帮你补问和收尾，可以用 `uv run fpa brief assistant --output ./project-brief.md`，由 skill 先问 3 个核心问题，再根据权限、约束、集成信号和 AI 建议做追问帮你收敛信息
   - 这两条命令都会先产出 `draft` brief，正式喂给 `init` 之前请再运行 `uv run fpa brief confirm --input ./project-brief.md --output ./project-brief.confirmed.md`，然后把确认后的文件传给 `init`

一个可以直接用的自然语言请求是：

> 根据当前仓库的 `SKILL.md` 和 `references/methodology.md`，从 Round 1 开始完整做项目拆解。先读取必要上下文，按轮次产出文档、做自检，再继续下一轮。输出要严格符合现有目录结构和质量门。

## 1. 项目有什么

### 代码包

核心 Python 包位于 [src/frontend_project_analysis/](src/frontend_project_analysis) 下，按职责分为：

- [cli.py](src/frontend_project_analysis/cli.py): CLI 入口，只负责注册命令组和启动时初始化
- [core/](src/frontend_project_analysis/core): 配置、领域枚举、提示词和稳定错误类型
- [commands/](src/frontend_project_analysis/commands): 所有 Typer 子命令
- [infrastructure/](src/frontend_project_analysis/infrastructure): 日志、文档解析、SQLite 会话和迁移辅助
- [models/](src/frontend_project_analysis/models): ORM 实体
- [repositories/](src/frontend_project_analysis/repositories): 项目、artifact、依赖、版本、review 持久化
- [workflow/](src/frontend_project_analysis/workflow): 状态检查、状态迁移、语义 packet 和 IO
- [llm/](src/frontend_project_analysis/llm): provider 路由、请求组装、响应校验、HTTP 传输和重试
- [schemas/](src/frontend_project_analysis/schemas): 结构化 payload 模型

### 仓库文件

仓库根目录当前包含：

- [SKILL.md](SKILL.md)
- [AGENTS.md](AGENTS.md)
- [pyproject.toml](pyproject.toml)
- [README.md](README.md)
- [frontend-decomposition-methodology.md](frontend-decomposition-methodology.md)
- [agents/](agents)
- [references/](references)
- [runbooks/](runbooks)
- [scripts/](scripts)
- [migrations/](migrations)
- [tests/](tests)

### 运行时目录

默认状态目录是目标项目根目录下的：

```text
.frontend-project-analysis/
  state.db
  backups/
  exports/
  logs/
  audits/
```

`uv run fpa init ...` 会自动把 `.frontend-project-analysis/` 写入调用项目的 `.gitignore`，这个目录只保存本地运行态数据库和审计数据，避免中间产物进入版本控制。

### 项目初始化会创建的内容

执行 `uv run fpa init ...` 后，会创建这些分析目录：

```text
analysis/index.md
analysis/brief.md
analysis/personas/
analysis/personas/index.md
analysis/story-maps/
analysis/story-maps/index.md
analysis/pages/
analysis/pages/index.md
analysis/features/
analysis/features/index.md
analysis/relations/
analysis/relations/persona-story-page-matrix.md
analysis/relations/feature-coverage-matrix.md
analysis/gwt/
analysis/specs/features/
```

### 语义定义

状态机语义图见 [references/state-machine.md](references/state-machine.md)。
状态 gate 与回退的设计背景见 [references/adr/index.md](references/adr/index.md)。
CLI 层面的用户影响和命令约束见 [references/cli-contract.md](references/cli-contract.md)。


## 2. 项目能做什么

### 项目治理

- 初始化项目状态库
- 创建项目根记录
- 建立 artifact、dependency、review 和 transition 关系
- 维护 artifact version 历史
- 记录 provider 调用审计

### Artifact 流程

- `artifact add`：注册 `persona`、`story_map`、`page`、`feature`、`gwt` 或 `feature_spec`，且新建内容只会进入 `draft`
- `artifact link`：建立 artifact 之间的依赖边
- `artifact list`：列出项目下的 artifact
- `artifact ready`：输出当前可以继续推进的 artifact

### Review 流程

- `review structural`：做确定性的结构校验，并把通过的 `draft` 推到 `structurally_valid`
- `review semantic-packet`：生成语义审查 packet
- `review semantic-run`：在 `host` 或外部 LLM 模式下执行语义审查
- `review semantic-record`：把语义审查结果写回数据库
- `review resubmit`：重提审手工修改后的 Markdown，自动重跑结构审查并继续语义审查或导出 host packet
- `review approve`：人工最终批准
- `review reject`：人工拒绝

### Import / Export

- `export manifest`：导出完整 JSON manifest
- `export relations`：导出关系矩阵 Markdown
- `import manifest`：从 JSON manifest 预览或写回数据库
- `import markdown-scan`：扫描 Markdown frontmatter 和文件身份变更，并把结果回写到数据库

`analysis/` 里的 Markdown 是人类可读、可编辑的投影层，不是和 SQLite 并列的第二套权威状态源。你直接改了 Markdown 之后，仍然需要运行对应的 import 命令把变更收敛进数据库；在那之前，数据库仍然视为权威，衍生索引和矩阵也可能暂时过期。

### Database Maintenance

- `db init`：初始化或迁移数据库
- `db backup`：备份数据库
- `db restore`：从备份恢复数据库
- `db wipe`：删除当前数据库

### LLM 支持

语义审查是 `host-first` 的：默认由当前 Codex 或 Claude Code 宿主自动完成判断，不需要外部大模型 API key。只有在你想让 CLI 直接请求外部模型时，才切换到下面这些 provider：

- `host`
- `openai`
- `openai-compatible`
- `anthropic`
- `gemini`
- `mock`

`host` 模式不由本仓库代码去调用外部大模型，而是把语义审查 packet 交给一个新的 Codex 或 Claude Code 审查上下文来判断；在支持 sub-agent 的 Codex 环境里，必须用 `fork_context: false` 起一个 fresh reviewer sub-agent，只读 packet，不继承生成文档时的上下文。
`FPA_SEMANTIC_REVIEW_AUTO_APPROVE=true` 时，语义审查 `passed` 会直接进入 `approved`；否则会停在 `semantic_review`，等待人工 `review approve`。

## 3. 项目怎么使用

### 3.1 初始化环境

```bash
uv python install 3.12
uv sync
```

### 3.2 查看命令

```bash
uv run fpa --help
uv run fpa project --help
uv run fpa artifact --help
uv run fpa review --help
```

### 3.3 初始化项目

先准备一个用户自己提供、且已经确认过的 brief 文件，然后再初始化。`init` 直接读取已确认 brief，并在目标项目里生成 `analysis/` 与 `.frontend-project-analysis/`，不需要把 `src/`、`migrations/` 或其他工具脚手架复制到目标项目：

```bash
uv run fpa brief confirm --input ./project-brief.md --output ./project-brief.confirmed.md
uv run fpa init --project crm-web --name "CRM Web" --brief-file ./project-brief.confirmed.md
```

初始化后，目标项目里只会出现 `analysis/` 和 `.frontend-project-analysis/` 两类产物。不会再复制 `README.md`、`Makefile`、`pyproject.toml` 或其他工具脚手架文件。

### 3.3.1 Brief 写法

一份好的 brief 通常只需要把分析起点说清楚，不用一次性写成完整 PRD。建议至少包含：

- 产品是做什么的
- 主要用户有哪些
- 他们最核心的使用场景是什么
- 哪些页面、能力或数据对他们不可见
- 哪些权限边界或业务约束最重要

如果你是通过多轮对话来补充 brief，建议先收敛在这些信息，再执行 `brief confirm`，然后把 confirmed brief 喂给 `init`。`analysis/brief.md` 会保存那一刻的输入快照，并带上 provenance frontmatter。
如果你一开始不知道怎么写，可以先运行：

```bash
uv run fpa brief interview --output ./project-brief.md
uv run fpa brief assistant --output ./project-brief.md
```

这个流程会先问 3 个核心问题，然后在预算允许时继续收集 `discovery`、`risk`、`accessibility`、`observability`、`release` 这些横切信号，再汇总成一版 draft brief。正式进入 `init` 之前，先用 `brief confirm` 把它变成 confirmed brief。
你也可以加上 `--max-questions <n>` 控制总提问上限，或者用 `--dry-run` 先预览生成结果而不落盘。
如果你想保留完整的问答过程，再额外加上 `--transcript ./brief-transcript.md`，这样 brief 和 transcript 会分别保存。
后续生成的 `Feature Spec` 还会显式保留 discovery evidence、risk、accessibility、observability、release 和 compliance 这些横切约束。

### 3.4 录入 artifact 和依赖

```bash
uv run fpa artifact add --project crm-web --type persona --slug sales-rep --title "Sales Rep"
uv run fpa artifact add --project crm-web --type feature --slug customer-assignment --title "Customer Assignment"
uv run fpa artifact link --project crm-web --from feature:customer-assignment --to persona:sales-rep
uv run fpa artifact list --project crm-web
uv run fpa artifact ready --project crm-web
```

### 3.5 做结构校验

```bash
uv run fpa review structural --project crm-web --artifact persona:sales-rep
uv run fpa review structural --project crm-web
```

### 3.6 做语义审查

```bash
uv run fpa review semantic-packet --project crm-web --artifact feature:customer-assignment --output /tmp/feature-review.json
uv run fpa review semantic-run --project crm-web --artifact feature:customer-assignment
uv run fpa review semantic-record --project crm-web --artifact feature:customer-assignment --input /tmp/review-result.json
uv run fpa review resubmit --project crm-web --artifact feature:customer-assignment
uv run fpa review approve --project crm-web --artifact feature:customer-assignment
uv run fpa review reject --project crm-web --artifact feature:customer-assignment
```

`host` 模式下，`semantic-run` 不会调用外部模型，而是直接把 packet 交给新的 Codex 或 Claude Code 审查上下文做判断，再用 `semantic-record` 记录结果。审查输出要先找 counterexamples，并且每条 finding 都要带 evidence，否则会被降级成 `needs_revision`。
如果用户手改了 `analysis/` 里的 Markdown，或者某个 revision 变成了 `stale`，优先用 `review resubmit` 把重导入、结构重审和语义重审串起来。
`review approve` 只接受已经进入 `semantic_review` 的 revision；如果 revision 变成 `stale`，需要先重新做 `review structural` 再继续后续审查。

### 3.7 命令与 gate 影响

命令对状态的具体影响、回退语义和导入约束不在 README 展开，统一以 [references/cli-contract.md](references/cli-contract.md) 为准。

### 3.8 导入和导出

```bash
uv run fpa export manifest --project crm-web
uv run fpa export relations --project crm-web
uv run fpa import manifest --project crm-web --input /tmp/manifest.json
uv run fpa import manifest --project crm-web --input /tmp/manifest.json --apply
uv run fpa import markdown-scan --project crm-web
uv run fpa import markdown-scan --project crm-web --apply
```

`import markdown-scan --apply` 不只会把 Markdown frontmatter 同步进数据库，还会刷新 `analysis/index.md`、各层级的 index 页，以及 `analysis/relations/` 下的关系矩阵。

### 3.9 维护数据库

```bash
uv run fpa db init
uv run fpa db backup
uv run fpa db restore --from /path/to/backup.db
uv run fpa db wipe --yes
```

### 3.10 配置环境变量

项目根目录下的 `.env` 负责运行时配置。常用键包括：

- `FPA_ROOT_DIR`
- `FPA_STATE_DIR`
- `FPA_DB_PATH`
- `FPA_EXPORT_DIR`
- `FPA_LOG_DIR`
- `FPA_AUDIT_DIR`
- `FPA_LOG_LEVEL`
- `FPA_LOG_JSON`
- `FPA_LLM_PROVIDER`
- `FPA_LLM_MODEL`
- `FPA_LLM_BASE_URL`
- `FPA_LLM_API_KEY`
- `FPA_LLM_API_PATH`
- `FPA_LLM_TIMEOUT_SECONDS`

### 3.11 运行测试

仓库提供了几组常用的测试入口，适合本地回归和 CI 拆分执行：

```bash
./scripts/test-smoke.sh
./scripts/test-check.sh
./scripts/test-full.sh
./scripts/test-all.sh
```

对应的 Make 目标是：

```bash
make smoke
make check
make full
make all
```
- `FPA_LLM_MAX_OUTPUT_TOKENS`
- `FPA_LLM_MAX_RETRIES`
- `FPA_LLM_RETRY_INITIAL_BACKOFF_SECONDS`
- `FPA_LLM_RETRY_MAX_BACKOFF_SECONDS`
- `FPA_SEMANTIC_REVIEW_AUTO_APPROVE`
- `FPA_ANTHROPIC_VERSION`

### 3.12 常见使用顺序

1. 准备 brief
2. `init`
3. `artifact add`
4. `artifact link`
5. `review structural`
6. `review semantic-packet`
7. `review semantic-run`、`review semantic-record`，或者在 `host` 模式下直接让当前 Codex / Claude Code 读取 packet 后再记录结果
8. `review approve` 或 `review reject`
9. `export manifest` 和 `export relations`

如果你要开始下一轮，直接跑 `uv run fpa workflow start --project crm-web --round 2`，它会自动先验 gate。
如果你还在边探索边修正，可以改用 `uv run fpa workflow explore start --project crm-web --round 2`，它会允许你先看后续轮次的草稿联动，再回头补前面的输入。
如果你想看哪些命令会改状态、哪些只是只读，见 `references/state-entrypoints.md`。

## 4. 项目怎么维护

### 验证命令

- `./scripts/test-smoke.sh`: CLI 回归
- `./scripts/test-check.sh`: `compileall` + smoke
- `./scripts/test-full.sh`: 全量测试
- `./scripts/test-all.sh`: 检查 + 全量测试
- `./scripts/lint.sh`: Ruff lint

### Make 入口

优先把 `make test`、`make quality` 和 `make release` 当作组入口，再按需下钻到细分 target。
命令层级约定见 [references/command-layer.md](references/command-layer.md)。
主目标使用 dotted 命名，如 `make test.smoke`、`make quality.lint` 和 `make release.card`；
hyphenated 名称只保留作兼容别名。

快速选择：

| 场景 | 推荐入口 |
| --- | --- |
| 日常维护和检查 | `make test` 或 `make quality` |
| 发布前检查 | `make release` |
| 只拿审查卡片 | `make release.card` |
| 自动化或 skill 调用 | `scripts/*.sh` |

Primary targets:

- `make help`
- `make test`
- `make quality`
- `make release`
- `make release.preflight`
- `make release.packet`
- `make release.card`
- `make test.smoke`
- `make test.full`
- `make test.check`
- `make quality.compile`
- `make quality.lint`

Compatibility aliases:

- `make release-card`

### 发布边界

对外发布分两层：

- Python 运行时代码：`src/frontend_project_analysis/`
- skill 入口和文档：`SKILL.md`、`README.md`、`references/`、`agents/openai.yaml` 和 `pyproject.toml`

不会随发布一起带走：

- `.frontend-project-analysis/` 运行时数据库和审计数据
- `.env` 和 `.venv/`
- `analysis/` 这类本地分析输出

`uv run fpa init ...` 会自动初始化数据库和 analysis 工作区，不需要你手动先建库，也不会复制额外的工具脚手架文件。skill 的实现、迁移和命令入口保留在 Codex 环境中的 skill 仓库本体，目标项目只保留输出和状态目录。
更直观的对照表见 [references/release-checklist.md](references/release-checklist.md)。
如果你准备发版，优先跑 `make release` 或 `./scripts/release.sh`。
如果你只想拿给 reviewer 的最小卡片，跑 `make release.card` 或 `./scripts/release-card.sh`。
它不会自动跑完整 preflight，适合在你已经完成前置检查后快速生成卡片。
如果你想分步执行，也可以先跑 `./scripts/release-preflight.sh` / `make release-preflight`，再跑 `./scripts/release-llm-review.sh` / `make release-llm-review`。

### 维护原则

- 先更新 `references/methodology.md`、`references/workflow.md`、`references/infrastructure.md`，再改 README
- 状态语义以 [references/state-machine.md](references/state-machine.md) 为准
- 关系密集型内容优先放在 `analysis/relations/` 或导出结果里
- 如果新增或修改命令，必须同步更新 README 和测试
- 如果修改状态流转，必须同步更新状态机语义图和回归测试
- 如果修改对外版本号，要同时更新 [pyproject.toml](pyproject.toml) 和 [src/frontend_project_analysis/__init__.py](src/frontend_project_analysis/__init__.py)

## 5. 补充说明

### 术语

以下术语保持英文：

- `Persona`
- `Story Map`
- `Feature`
- `Feature Spec`
- `Happy Path`
- `Edge Case`
- `Permission Case`
- `Error Case`
- `Given`
- `When`
- `Then`
- `Shared Component`

完整术语表见 [references/glossary.md](references/glossary.md)。

### 设计原则

- 文档优先，不直接产出实现代码
- 渐进式披露，优先小文件
- 代码负责生命周期与关系事实，Markdown 负责阅读和编辑入口
- SQLite 是结构事实源
- CLI 是工作流操作入口

### 文档地图

如果你想快速判断某个文件是不是权威来源，先看 [references/document-map.md](references/document-map.md)。
如果你想理解仓库的层级结构，先看 [references/repo-layers.md](references/repo-layers.md)。
如果你想准备一次对外发布，先看 [references/release-checklist.md](references/release-checklist.md)。
