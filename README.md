# Frontend Project Analysis

一个用于前端项目分析与拆解的 Codex skill，同时内置一套可跨项目复用的 Python 工作流基础设施。

这个 skill 适合在新项目启动、需求澄清、方案收敛和实现前分析阶段使用。它通过一套文档优先的工作流，把一个前端产品或功能范围逐步拆解为 `Persona`、`Story Map`、`Page Map`、`Feature`、`Given-When-Then` 和 `Feature Spec` 等结构化产物，并用 SQLite 持久化这些中间产物、依赖关系与审核状态，帮助团队减少“直接开写、边做边改”的重复成本。

## 这个 skill 能做什么

- 基于项目描述定义 `Persona`
- 为不同 `Persona` 生成 `Story Map`
- 将用户行为映射为 `Page Map`
- 按 Vertical Slice 思路拆分 `Feature`
- 为单个 `Feature` 生成 Gherkin 格式的 `Given-When-Then`
- 为后续实现规划交付顺序与依赖关系
- 以 `uv run fpa ...` 命令管理数据库、依赖 DAG、审核记录与导出物

## 适用场景

- 团队准备启动一个新的前端项目
- 需要把一个复杂产品范围拆成可实施的前端切片
- 希望先产出文档，再进入设计或开发
- 需要把分析方法标准化，减少不同同事各自摸索

## 不适用场景

- 直接编写页面、组件或业务实现代码
- 已经进入工程实现阶段，只需要修某个具体 bug
- 只想做视觉设计，不需要结构化产品拆解

## 工作流概览

这个 skill 按轮次推进，默认不跳轮。

1. `Round 1`：定义 `Persona`
2. `Round 2`：生成 `Story Map`
3. `Round 3`：映射 `Page Map`
4. `Round 4`：拆分 `Feature`
5. `Round 5`：编写 `Given-When-Then`
6. `Round 6`：生成 `Feature Spec` 与实现顺序建议

每一轮的默认执行规则是：

- 先输出产物
- 再输出自检结果
- 然后暂停，等待确认后进入下一轮

## 仓库结构

```text
.
├── SKILL.md
├── README.md
├── AGENTS.md
├── pyproject.toml
├── .python-version
├── agents/
│   └── openai.yaml
└── references/
    ├── glossary.md
    ├── infrastructure.md
    ├── methodology.md
    ├── quality-gates.md
    ├── structure.md
    ├── templates.md
    └── workflow.md
```

各文件职责如下：

- `SKILL.md`：skill 主入口，给 Codex 读取
- `pyproject.toml`：`uv` / Python 项目配置
- `agents/openai.yaml`：skill 的 UI 元数据与默认 prompt
- `references/infrastructure.md`：数据库、审核分层与 CLI 约定
- `references/methodology.md`：方法论与完整 6 轮工作流
- `references/workflow.md`：每一轮的输入与输出要求
- `references/quality-gates.md`：每一轮的质量门与自检标准
- `references/structure.md`：推荐产物目录结构
- `references/templates.md`：文档模板
- `references/glossary.md`：术语规范

## Python 基础设施

这个仓库现在使用：

- `uv`
- Python `3.12`
- `SQLite` 作为工作流状态数据库
- `Alembic` 作为数据库迁移管理
- `Typer` 作为 CLI
- `SQLAlchemy` 作为数据层

代码层面现在也按职责分层：

- `domain` 只放稳定业务规则
- `schemas` 只放结构化载荷
- `storage` 和 `migrations` 只管持久化与 schema 演进
- `repositories` 只做兼容转发，实际实现拆在 `repository_artifacts` / `repository_reviews`
- `workflow_state` 只做兼容转发，实际实现拆在 `state_checks` / `state_transitions` / `state_packets`
- `llm` 只负责 provider 路由
- `llm_common` 和 `llm_*` 负责 provider 适配、重试、payload 校验和审计
- `service` 只管用例编排
- `cli` 只做命令入口，具体命令拆在 `project_commands` / `artifact_commands` / `review_commands` / `export_commands` / `import_commands` / `db_commands`

默认状态目录位于目标项目根目录下：

```text
.frontend-project-analysis/
  state.db
  backups/
  exports/
  logs/
```

这意味着：

- Markdown 负责面向人阅读
- 数据库负责依赖、审核、状态与审计
- 关系矩阵优先由 CLI 导出，而不是手工维护

## `.env` 配置

所有运行时配置现在都可以通过项目根目录下的 `.env` 控制。你可以从 [.env.example](/Users/cherubines/Documents/MaxCPA/.env.example:1) 复制一份开始。

当前重点配置包括：

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
- `FPA_STATE_DIR`
- `FPA_DB_PATH`
- `FPA_EXPORT_DIR`
- `FPA_LOG_DIR`
- `FPA_AUDIT_DIR`
- `FPA_LOG_LEVEL`
- `FPA_LOG_JSON`
- `FPA_SEMANTIC_REVIEW_AUTO_APPROVE`
- `FPA_ANTHROPIC_VERSION`

日志现在支持两种格式：

- 默认文本日志，便于本地阅读
- `FPA_LOG_JSON=true` 时输出结构化 JSON，便于接入后续审计系统

Provider 审计也会保留更细的事件时间线，方便回放一次调用经历了哪些请求、重试和解析步骤。

这让后续切换 provider、调整本地目录结构、修改日志输出策略时不需要改代码。

## 如何安装

你可以把这个仓库作为一个独立 skill 源使用。

常见方式是将仓库内容放入本地 Codex skill 目录，例如：

```text
~/.codex/skills/frontend-project-analysis/
```

只要目录内包含 `SKILL.md`、`agents/openai.yaml`、`references/` 和 Python 包配置，Codex 就可以识别并调用这套 skill。

如果你的团队已经有统一的 skill 安装方式，也可以直接把这个仓库接入现有流程。

## 如何使用

### 初始化 Python 环境

```bash
uv python install 3.12
uv sync
```

### 初始化一个项目状态库

```bash
uv run fpa project init --project crm-web --name "CRM Web"
```

### 常用命令

```bash
uv run fpa artifact add --project crm-web --type persona --slug sales-rep --title "Sales Rep" --source-path docs/personas/sales-rep.md
uv run fpa artifact link --project crm-web --from story_map:sales-rep --to persona:sales-rep
uv run fpa review structural --project crm-web --artifact persona:sales-rep
uv run fpa review semantic-packet --project crm-web --artifact feature:customer-assignment --output /tmp/feature-review.json
uv run fpa review semantic-run --project crm-web --artifact feature:customer-assignment
uv run fpa review semantic-record --project crm-web --artifact feature:customer-assignment --input /tmp/review-result.json
uv run fpa review approve --project crm-web --artifact feature:customer-assignment
uv run fpa export relations --project crm-web
uv run fpa db migrate
uv run fpa db backup
```

### 方式一：显式调用 skill

在 prompt 里直接提到 skill 名称：

```text
使用 $frontend-project-analysis 帮我分析一个新的 CRM 前端项目。
```

```text
用 $frontend-project-analysis 从 Persona 开始拆解这个后台管理系统。
```

### 方式二：自然触发

如果你在描述里明确提出这些需求，Codex 也可能自动触发这个 skill：

- 定义 `Persona`
- 创建 `Story Map`
- 做页面映射
- 拆分 `Feature`
- 编写 `Given-When-Then`
- 生成 `Feature Spec`

例如：

```text
帮我把这个新项目拆成 Persona、Story Map、页面和 Feature，先不要写代码。
```

## 推荐输入方式

为了让输出更稳定，建议在开始时提供这些信息：

- 产品目标
- 目标用户
- 核心业务场景
- 已知角色差异
- 关键权限边界
- 是否已有页面草图或需求文档

输入越具体，后续 `Persona`、`Story Map` 和 `Feature` 拆分越稳定。

## 审核模型

审核分为两层：

- `structural review`：纯代码逻辑校验，负责前后依赖、前置审批、frontmatter、文件存在性、环检测、一致性
- `semantic review`：由 LLM 审核 `Persona` 合理性、`Story Map` 业务性、`Feature` 切分质量等语义问题

`semantic-packet` 命令会把当前 `.env` 中的 LLM provider 配置一并写入 review packet，方便后续 skill 或脚本直接消费。

如果你希望 CLI 直接发起 provider 请求，可以使用：

```bash
uv run fpa review semantic-run --project crm-web --artifact feature:customer-assignment
```

当前内置支持：

- `openai`
- `openai-compatible`
- `anthropic`
- `gemini`
- `mock`

## Log 与异常处理

当前已经有一层基础架构：

- CLI 启动时统一初始化 logging
- 日志默认写入 `.frontend-project-analysis/logs/app.log`
- 支持通过 `.env` 控制日志级别和是否输出到 stderr
- 统一的应用异常基类：配置异常、存储异常、审核异常
- CLI 顶层有兜底异常处理，未预期错误会写日志并给出简短终端提示
- provider 调用带指数退避重试
- provider 请求/响应会归档到 `.frontend-project-analysis/audits/`
- 数据库会记录 provider 调用摘要，便于后续查询和审计

这几项现在已经补齐：

- 结构化 JSON log 可通过 `FPA_LOG_JSON=true` 打开
- `request_id` / `trace_id` 已贯穿日志、审计和归档文件名
- provider-specific error taxonomy 已拆分为更细的异常类
- 审计日志事件模型已支持事件时间线

推荐顺序：

1. 先生成或更新文档
2. 用 `uv run fpa import markdown-scan --project <key> --apply` 注册结构化状态
3. 用 `uv run fpa review structural ...` 跑硬校验
4. 用 `uv run fpa review semantic-packet ...` 生成审查上下文给 skill / LLM
5. 将结构化语义审查结果写回 `uv run fpa review semantic-record ...`
6. 人工或流程调用 `uv run fpa review approve ...`

## 数据库维护

内置维护命令如下：

- `uv run fpa db init`
- `uv run fpa db check`
- `uv run fpa db backup`
- `uv run fpa db restore --from <backup.db>`
- `uv run fpa db reset-project --project <key> --yes`
- `uv run fpa db wipe --yes`
- `uv run fpa import manifest --project <key> --input <manifest.json> [--apply]`
- `uv run fpa import markdown-scan --project <key> [--apply]`
- `uv run fpa export manifest --project <key>`
- `uv run fpa export sql`

## 典型使用示例

```text
使用 $frontend-project-analysis 帮我分析一个面向销售团队的 CRM Web 应用。

背景：
- 目标是管理客户、跟进记录和销售机会
- 用户包括销售、销售主管和运营
- 主管可以查看团队数据，销售只能看自己的客户
- 先从 Persona 开始，不要跳轮，也不要写实现代码
```

## 输出产物示例

这个 skill 默认倾向于生成如下类型的文档：

- `docs/personas/*.md`
- `docs/story-maps/*.md`
- `docs/pages/*.md`
- `docs/features/*.md`
- `docs/gwt/*.feature`
- `specs/features/*-spec.md`

如果目标仓库没有这些目录，Codex 也可以按 `references/structure.md` 中的建议结构进行创建。

## 术语说明

这个 skill 对部分专业术语采用固定英文写法，不建议翻译，包括：

- `Persona`
- `Story Map`
- `Feature`
- `Feature Spec`
- `Happy Path`
- `Edge Case`
- `Permission Case`
- `Error Case`
- `Given / When / Then`

完整规则见 [references/glossary.md](/Users/cherubines/Documents/MaxCPA/references/glossary.md:1)。

## 设计原则

- 文档优先，不直接产出实现代码
- 渐进式披露，优先小文件
- 关系密集内容放在索引或矩阵文件中，但数据库是结构事实源
- 按轮次推进，降低一次性拆解过深的风险
- 把分析过程标准化，方便团队协作与复用

## 后续维护建议

- 如果你调整了流程，请优先更新 `SKILL.md` 和 `references/`
- 如果你调整了对外使用方式，再更新 `README.md`
- 如果你新增了术语规范，先更新 `references/glossary.md`
- 如果你新增了模板，更新 `references/templates.md`

## 许可与团队使用

如果你计划在团队内部长期复用，建议结合你们自己的安装说明、仓库规范或项目脚手架一起使用，这样同事在新项目启动时会更顺手。
