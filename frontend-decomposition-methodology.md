
## 6 轮对话工作流

## Round 1：定义 Persona（输入：项目描述）

**目标产出**：角色卡片表格（角色 / 核心目标 / 权限边界 / 不可见页面）

```
text
你是一个资深的前端产品架构师。

## 任务
基于以下项目描述，帮我完成第一步：定义用户 Persona。

## 项目描述
[粘贴你的项目描述，包括产品目标、用户群体、核心场景]

## 输出要求
以 Markdown 表格输出 Persona 卡片，每个角色包含：
- 角色名称
- 核心目标（用户用这个系统要完成什么）
- 与其他角色的关键差异（行为/路径）
- 权限边界（能写/只读/部分写）
- 对哪些页面不可见

不要输出流程、页面、feature。只输出角色定义。
```

------

## Round 2：Story Map（输入：Round 1 产出）

**目标产出**：每个角色的用户活动主干（Activity → Step → Story）

```
text
基于以下已确认的 Persona：

[粘贴 Round 1 的产出]

## 任务
为每个 Persona 分别绘制 User Story Map。

## 输出要求
- 每个 Persona 单独一个 Story Map
- 格式：Activity → Step → Story，用代码块缩进树状结构表示
- 只描述用户行为流程，不要提页面名称，不要提 feature 名称
- 每个 Activity 不超过 5 个 Step，避免过度细化

不要输出路由、组件、状态管理相关内容。
```

------

## Round 3：Page Map（输入：Round 2 产出）

**目标产出**：路由树 + 页面清单 + 每个页面属于哪个 Persona 流程

```
text
基于以下已确认的 Story Map：

[粘贴 Round 2 的产出]

## 任务
将 Story Map 中的步骤映射为页面（Page Map）。

## 映射规则（严格遵守）
- 对应独立路由 → 独立页面
- 属于上下文操作（无需跳转）→ 标注为「弹窗/Drawer/Tab」，不单独列路由
- 多个步骤落在同一页面 → 合并
- 不同 Persona 共用的页面只列一次，标注所有可访问的角色

## 输出要求
1. 路由树（代码块格式，含路由路径 + 页面中文名称）
2. 页面清单表格（路由 / 页面名 / 所属 Persona / 页面职责一句话描述）

不要输出 feature、组件、状态相关内容。
```

------

## Round 4：Feature Slicing（输入：Round 3 产出，逐页面进行）

**目标产出**：每个页面的 Feature 清单 + 目录结构

> ⚠️ **重要**：这一步建议**逐页面执行**，复杂项目不要一次拆所有页面。

```
text
基于以下已确认的页面地图：

[粘贴 Round 3 的产出]

## 当前任务
只对以下页面进行 Feature Slicing：
[指定 1-3 个页面，例如：/projects/:id 项目详情页]

## 判断标准（满足 3 条以上才独立为 feature）
- 有独立业务目的
- 有独立数据来源或状态
- 有独立的交互流程
- 可能单独演进或迭代
- 可能跨页面复用
- 可以单独测试和验证

## 输出要求
1. 该页面的 Feature 清单（feature 名 / 业务职责 / 状态类型：server/client/both）
2. 推荐目录结构（Vertical Slice 格式，每个 feature 包含哪些文件）
3. 哪些元素是 Shared Component（不拆 feature，放 components/ 目录）

不要输出 Given-When-Then。不要输出具体组件实现代码。
```

------

## Round 5：Given-When-Then（输入：Round 4 某个 Feature，逐 Feature 进行）

**目标产出**：`.feature` 文件内容（Gherkin 格式）

> ⚠️ **重要**：这一步必须**逐 Feature 执行**，一次一个，确保覆盖质量。

```
text
基于以下已确认的 feature 定义：

Feature 名称：[feature 名]
业务职责：[一句话描述]
所属页面：[页面名]
相关 Persona：[哪些角色会触发这个 feature]

## 任务
为这个 feature 编写 Given-When-Then 验收规格（Gherkin 格式）。

## 覆盖要求（每类至少一个 Scenario）
- Happy Path：正常流程，输入合法，结果符合预期
- Edge Case：边界输入（重复操作、空状态、数量上限等）
- Permission Case：不同 Persona 看到不同 UI 或操作权限
- Error Case：网络失败、后端报错时的系统行为

## 写法原则
- 声明式，描述业务意图（What），不描述 UI 操作细节（How）
- 错误示例：「我点击右上角的发送按钮」
- 正确示例：「我提交邀请请求」

## 输出格式
输出标准 Gherkin .feature 文件内容，不需要其他说明文字。
```

------

## Round 6：实现顺序规划（输入：所有前置产出）

**目标产出**：Vertical Slice 交付顺序 + 每个切片的依赖关系

```
text
基于以下已完成的分析：

## Persona
[粘贴]

## 页面清单
[粘贴]

## Feature 清单（含所有页面）
[粘贴]

## 任务
基于 Vertical Slice 交付原则，为这个项目规划前端实现顺序。

## 排序原则（按优先级）
1. 核心用户路径优先（最小可演示路径 MVP Slice）
2. 依赖少的 feature 优先
3. Shared Component 先于依赖它的 feature
4. 权限/认证 feature 最先实现

## 输出要求
1. 分阶段的交付计划（Phase 1 / Phase 2 / Phase 3）
2. 每个阶段：包含哪些 feature + 交付后可以演示什么
3. Feature 间的依赖关系（哪个必须在哪个之前完成）
4. 推荐第一个开工的 feature 是什么，理由是什么
```

------

## 轮次总览

| 轮次    | 对应方法论步骤  | 输入                 | 产出                    | 粒度           |
| ------- | --------------- | -------------------- | ----------------------- | -------------- |
| Round 1 | Persona         | 项目描述             | 角色卡片                | 整项目一次     |
| Round 2 | Story Map       | Round 1              | 用户活动树              | 整项目一次     |
| Round 3 | Page Map        | Round 2              | 路由树 + 页面清单       | 整项目一次     |
| Round 4 | Feature Slicing | Round 3              | Feature 清单 + 目录结构 | **逐页面**     |
| Round 5 | Given-When-Then | Round 4 单个 Feature | Gherkin 文件            | **逐 Feature** |
| Round 6 | 实现规划        | 所有前置产出         | 交付顺序 + 依赖图       | 整项目一次     |

 原方法论共 7 步（含 Component 拆分和 State Boundary），这里将 Component 和 State Boundary 合并进 Round 4 的目录结构产出中，因为这两步依附于 Feature 定义，不需要独立对话轮次。