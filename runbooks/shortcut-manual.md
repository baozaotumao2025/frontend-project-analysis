# 快捷指令手册

## 目标

这份手册用于把 `goal` 指令和自然语言分析流程配合起来，帮助你按轮次完成业务拆解：

`Persona -> Story Map -> Page Map -> Feature -> GWT -> Feature Spec`

这是一份便捷 prompt 模板，不是 canonical workflow 定义；canonical rules 仍以 `SKILL.md` 和 `references/*` 为准。

## 基本用法

1. 先开一个总 `goal`，锁定这次业务拆解。
2. 每轮只发当前轮的自然语言指令。
3. 先对账，再产出，再暂停；需要判断、复核、挑错时，用 subagent。

## 总 `goal` 模板

```text
目标：完成 XXX 产品的业务拆解分析，按 Persona -> Story Map -> Page Map -> Feature -> GWT -> Feature Spec 的顺序推进。
要求：每轮只做当前轮，先做 inventory 和 coverage 对账，再生成产物，最后暂停等待下一步。
```

## 六轮指令

### Round 1: Persona

```text
现在开始 Round 1，只做 Persona。

输入是当前 brief。
请先列出所有可能的 Persona 候选，再收敛成最终 Persona 表。

每个 Persona 必须包含：
- name
- core goal
- key difference
- permission boundary
- invisible pages / capabilities

约束：
- 不要写 Story、Page、Feature
- 不要写实现细节
- 如果有歧义，请标记为 needs_review
- 先做 coverage 对账，再输出结论
- 做完后暂停
```

### Round 2: Story Map

```text
现在开始 Round 2，只做 Story Map。

输入只允许使用已确认的 Persona。
请为每个 Persona 输出 Activity -> Step -> Story 的树形结构。

约束：
- 只描述用户行为
- 不要写 page 名、feature 名、实现细节
- 每个 Activity 控制在 5 个 Step 内
- 先做 inventory 和 coverage ledger
- 覆盖不到的部分写 needs_review
- 做完后暂停
```

### Round 3: Page Map

```text
现在开始 Round 3，只做 Page Map。

输入只允许使用已确认的 Story Map。
请输出：
1. route tree
2. page inventory table
3. Persona-to-page mapping

约束：
- 一个 distinct route 对应一个 page
- contextual action 只能标成 modal / drawer / tab
- 合并同页上的多个 step
- 不要写 feature 或组件实现
- 先做 coverage 对账
- 做完后暂停
```

### Round 4: Feature Slicing

```text
现在开始 Round 4，只做 Feature Slicing。

输入只允许使用已确认的 Page Map。
这轮只处理我指定的页面批次，不要一次把全站都展开。

输出：
- Feature list
- 每个 Feature 的责任边界
- state type
- 推荐的 vertical slice 结构
- 哪些应该归为 Shared Component

约束：
- 只有满足独立业务目的、独立状态、独立交互等条件才算 Feature
- 不要写 GWT
- 不要写实现代码
- 先做 coverage ledger，再输出
- 做完后暂停
```

### Round 5: GWT

```text
现在开始 Round 5，只做 GWT。

输入只允许使用已确认的单个 Feature。
请输出标准 Gherkin，必须覆盖：
- Happy Path
- Edge Case
- Permission Case
- Error Case
- Accessibility Case

约束：
- 只写业务意图，不写点击细节
- 不要扩展到其他 Feature
- 需要 LLM 判断的内容必须走 subagent
- 做完后暂停
```

### Round 6: Feature Spec

```text
现在开始 Round 6，只做 Feature Spec 和 delivery planning。

输入只允许使用已经确认的 Persona、Page、Feature、GWT。
请输出：
- 分阶段交付顺序
- 每阶段的 Feature 划分
- 每阶段能证明什么
- Feature 依赖关系
- 第一优先实现项以及原因

约束：
- 优先核心路径
- 优先低依赖项
- Shared Component 要前置
- 权限和认证能力要早处理
- 不要新增分析维度
- 做完后暂停
```

## 完整性硬约束

- 每轮先列 inventory
- 逐项对账，状态只允许 `mapped` / `excluded` / `needs_review`
- 没完成对账前，不允许进入最终输出
- 如果发现新证据，当前 packet 失效，必须重新对账
- 所有需要判断、审查、挑错的 LLM 步骤都必须走 subagent

## 最短可复用总指令

```text
请在这个 goal 下，按 Persona -> Story Map -> Page Map -> Feature -> GWT -> Feature Spec 的顺序逐轮推进。
每轮都先做 inventory 和 coverage 对账，状态只允许 mapped / excluded / needs_review。
只处理当前轮，不要越级。
任何 LLM 判断都必须用 subagent。
每轮完成后先自检并暂停，等我确认后再继续。
```

## 小白指令

如果你刚开始用这个 skill，不需要记上面的细节，也不需要自己拼参数。
你只要用一句话告诉 Codex：这是个什么产品，先想拆什么，最后想看到什么。

推荐直接复制这一版：

```text
这是一个给 [谁] 用的 [什么产品]。
请先帮我做业务拆解，优先从最重要的用户和场景开始。
最后请把结果整理成清楚的文档。
```

如果你想再省一点事，也可以直接这样说：

```text
请按这个 skill 的默认方式，帮我完整拆这个项目。
先从最重要的业务开始，缺什么你就补问我。
每一步都帮我确认有没有遗漏，再继续下一步。
```

如果你想要最短版本，直接用这 3 句：

```text
这是一个给 [谁] 用的 [什么产品]。
先帮我从最重要的业务开始拆解。
每一步都先确认有没有遗漏，再继续。
```

对初学者来说，最重要的不是记术语，而是记住这三句话：

- 先问清楚业务
- 一轮只做一件事
- 先确认完整，再往下走
