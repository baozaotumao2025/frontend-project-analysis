# Frontend Project Analysis

一个用于前端项目分析与拆解的 Codex skill。

这个 skill 适合在新项目启动、需求澄清、方案收敛和实现前分析阶段使用。它通过一套文档优先的工作流，把一个前端产品或功能范围逐步拆解为 `Persona`、`Story Map`、`Page Map`、`Feature`、`Given-When-Then` 和 `Feature Spec` 等结构化产物，帮助团队减少“直接开写、边做边改”的重复成本。

## 这个 skill 能做什么

- 基于项目描述定义 `Persona`
- 为不同 `Persona` 生成 `Story Map`
- 将用户行为映射为 `Page Map`
- 按 Vertical Slice 思路拆分 `Feature`
- 为单个 `Feature` 生成 Gherkin 格式的 `Given-When-Then`
- 为后续实现规划交付顺序与依赖关系

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
├── agents/
│   └── openai.yaml
└── references/
    ├── glossary.md
    ├── methodology.md
    ├── quality-gates.md
    ├── structure.md
    ├── templates.md
    └── workflow.md
```

各文件职责如下：

- `SKILL.md`：skill 主入口，给 Codex 读取
- `agents/openai.yaml`：skill 的 UI 元数据与默认 prompt
- `references/methodology.md`：方法论与完整 6 轮工作流
- `references/workflow.md`：每一轮的输入与输出要求
- `references/quality-gates.md`：每一轮的质量门与自检标准
- `references/structure.md`：推荐产物目录结构
- `references/templates.md`：文档模板
- `references/glossary.md`：术语规范

## 如何安装

你可以把这个仓库作为一个独立 skill 源使用。

常见方式是将仓库内容放入本地 Codex skill 目录，例如：

```text
~/.codex/skills/frontend-project-analysis/
```

只要目录内包含 `SKILL.md`、`agents/openai.yaml` 和 `references/`，Codex 就可以识别这个 skill。

如果你的团队已经有统一的 skill 安装方式，也可以直接把这个仓库接入现有流程。

## 如何使用

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
- 关系密集内容放在索引或矩阵文件中
- 按轮次推进，降低一次性拆解过深的风险
- 把分析过程标准化，方便团队协作与复用

## 后续维护建议

- 如果你调整了流程，请优先更新 `SKILL.md` 和 `references/`
- 如果你调整了对外使用方式，再更新 `README.md`
- 如果你新增了术语规范，先更新 `references/glossary.md`
- 如果你新增了模板，更新 `references/templates.md`

## 许可与团队使用

如果你计划在团队内部长期复用，建议结合你们自己的安装说明、仓库规范或项目脚手架一起使用，这样同事在新项目启动时会更顺手。
