# Frontend Project Analysis

`frontend-project-analysis` 是一个以文档为先的前端项目分析 skill，同时内置一套可复用的 Python 工作流基础设施。它把前端项目拆解成 `Persona`、`Story Map`、`Page`、`Feature`、`GWT` 和 `Feature Spec` 等结构化产物，并用 SQLite 记录依赖、审核、版本和审计信息。

当前发布版本为 `1.0.0`。

## 快速开始

如果你想先跑通一条最小路径，直接按这个顺序来：

```bash
uv sync
uv run fpa project init --project crm-web --name "CRM Web"
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
- [references/](references)
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

### 项目初始化会创建的内容

执行 `uv run fpa project init ...` 后，会创建这些文档目录：

```text
docs/personas/
docs/story-maps/
docs/pages/
docs/features/
docs/relations/
docs/gwt/
specs/features/
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

- `artifact add`：注册 `persona`、`story_map`、`page`、`feature`、`gwt` 或 `feature_spec`
- `artifact link`：建立 artifact 之间的依赖边
- `artifact list`：列出项目下的 artifact
- `artifact ready`：输出当前可以继续推进的 artifact

### Review 流程

- `review structural`：做确定性的结构校验
- `review semantic-packet`：生成语义审查 packet
- `review semantic-run`：在 `host` 或外部 LLM 模式下执行语义审查
- `review semantic-record`：把语义审查结果写回数据库
- `review approve`：人工最终批准
- `review reject`：人工拒绝

### Import / Export

- `export manifest`：导出完整 JSON manifest
- `export relations`：导出关系矩阵 Markdown
- `import manifest`：从 JSON manifest 预览或写回数据库
- `import markdown-scan`：扫描 Markdown frontmatter 并同步到数据库

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

`host` 模式不由本仓库代码去调用外部大模型，而是把语义审查 packet 交给当前的 Codex 或 Claude Code 宿主自动完成判断；这适合 skill 发布时没有外部 API key 的场景。
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

```bash
uv run fpa project init --project crm-web --name "CRM Web"
```

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
uv run fpa review approve --project crm-web --artifact feature:customer-assignment
uv run fpa review reject --project crm-web --artifact feature:customer-assignment
```

`host` 模式下，`semantic-run` 不会调用外部模型，而是直接把 packet 交给当前 Codex 或 Claude Code 会话做判断，再用 `semantic-record` 记录结果。

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
- `FPA_LLM_MAX_OUTPUT_TOKENS`
- `FPA_LLM_MAX_RETRIES`
- `FPA_LLM_RETRY_INITIAL_BACKOFF_SECONDS`
- `FPA_LLM_RETRY_MAX_BACKOFF_SECONDS`
- `FPA_SEMANTIC_REVIEW_AUTO_APPROVE`
- `FPA_ANTHROPIC_VERSION`

### 3.11 常见使用顺序

1. `project init`
2. `artifact add`
3. `artifact link`
4. `review structural`
5. `review semantic-packet`
6. `review semantic-run`、`review semantic-record`，或者在 `host` 模式下直接让当前 Codex / Claude Code 读取 packet 后再记录结果
7. `review approve` 或 `review reject`
8. `export manifest` 和 `export relations`

如果你要开始下一轮，直接跑 `uv run fpa workflow start --project crm-web --round 2`，它会自动先验 gate。

## 4. 项目怎么维护

### 验证命令

- `./scripts/test-smoke.sh`: CLI 和兼容入口回归
- `./scripts/test-check.sh`: `compileall` + smoke
- `./scripts/test-full.sh`: 全量测试
- `./scripts/test-all.sh`: 检查 + 全量测试
- `./scripts/lint.sh`: Ruff lint

### Make 入口

- `make smoke`
- `make check`
- `make full`
- `make lint`
- `make all`

### 发布边界

这个仓库的对外发布边界分两层：

- Python 运行时代码发布为 `src/frontend_project_analysis/` 下的包
- skill 入口和文档发布为 `SKILL.md`、`README.md`、`references/`、`agents/openai.yaml` 和 `pyproject.toml`

不会随发布一起带走的内容：

- `.frontend-project-analysis/` 运行时数据库和审计数据
- `.env` 和 `.venv/`
- `docs/`、`specs/` 这类本地分析输出

`uv run fpa project init ...` 会自动初始化数据库和项目目录结构，不需要你手动先建库。
更直观的对照表见 [references/release-checklist.md](references/release-checklist.md)。

### 维护原则

- 先更新 `references/methodology.md`、`references/workflow.md`、`references/infrastructure.md`，再改 README
- 状态语义以 [references/state-machine.md](references/state-machine.md) 为准
- 关系密集型内容优先放在 `docs/relations/` 或导出结果里，不要手工维护成散落说明
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
- 代码负责事实，Markdown 负责阅读
- SQLite 是结构事实源
- CLI 是工作流操作入口

### 文档地图

如果你想快速判断某个文件是不是权威来源，先看 [references/document-map.md](references/document-map.md)。
如果你想理解仓库的层级结构，先看 [references/repo-layers.md](references/repo-layers.md)。
如果你想准备一次对外发布，先看 [references/release-checklist.md](references/release-checklist.md)。
