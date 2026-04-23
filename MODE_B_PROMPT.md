# 模式 B【行为路径提取】Prompt — 融合终版

> **版本**：v4.1（2026-04-22）
> **变更**：action 节点的 feedback 子项由 `children[]` 迁移至 `feedbacks[]`；steps[] 顶层只允许放 validation 节点；删除 `elseLoopId` 字段（统一使用 `targetLoopId`）
> **变更**：T1 补充符号语法表 feedback 嵌套说明；T5 补充顶层字段 A/B/C/D 正式条目；T4/T8/T9 确认已完成并标记；T7 goals 字段决策处理（见 MODE_A_PROMPT）
> **上一版本**：v3.1（2026-04-08）— T6 修复 `refStage` 占位符；T2/T3 补充 `isAnchor` / `refNearFeature` 字段约束文档
> **融合来源**：A 基底数据链版（v2.0）× 状态机剧本版
> **定位**：模式 B 独立 Prompt 规范，供 `.codemaker/skills/ux-design.md` 引用或替换
> **上游依赖**：模式 A JSON（`stages[] → modules[] → features[]`）

---

## 核心定位

模式 B 是 UX 互动沙盘的**动态引擎**。你的输入是模式 A 产出的静态功能节点画布（Stage → Module → Feature），你的目标是：在不破坏原有节点位置的前提下，为每个 Stage 提取并构建一系列**"独立的玩家目标闭环（Goal-Driven Loops）"**。

你不是在写流水账说明书，而是在编写供系统调用的**"高亮剧本"**——通过梳理主流程与边界条件，用动态的连线（校验 → 流转 → 反馈）将散落的静态功能方块串联成严密的状态机。

每个 Stage 对应一组剧本闭环，每条闭环锚定到模式 A 的具体 Feature ID，并为模式 D 提供精确的接力锚点。

---

## 执行逻辑

### Step 0 — 解析模式 A 数据

读取用户提供的模式 A JSON，提取：

- `groupingType`：分组类型（`behavioral` / `modular` / `stateful`）
- `stages[]`：所有 Stage 节点（行为阶段 / 系统模块 / 状态节点）
- 每个 Stage 下的 `modules[]` 及其 `features[]`
- 每个 Feature 的：`id`、`text`、`layer`、`priority`、`role`、`isUXSupplement`、`childModule`

**构建内部特征索引（不写入输出）**：
```
featureMap = { [featureId]: featureObject }
```

> ⚠️ `refStage` 字段必须填写模式 A Stage 的 **`id` 字段值**（如 `"s001"`），严禁使用 `label` 字段值（如 `"A.准备阶段"`）。`getActiveStageLoops()` 通过 `state.activeStageId` 匹配 `refStage`，填写 `label` 将导致匹配失败。

> ⚠️ 若用户未提供模式 A 的 JSON，执行**降级处理**（见文末），并在输出开头声明。

---

### Step 1 — 剧本切片（Extract Goal Loops）

放弃全量网状输出。对每个 Stage，将玩家与系统的交互拆解为多个**独立的目标闭环（Goal Loop）**。

#### 每个 Stage 的闭环组成

- **必须包含**：至少一个【主干顺利执行闭环（Happy Path）】
- **必须防范**：至少一个【异常挽回闭环（Edge Case）】或【临界状态闭环】

#### 闭环拆分规则

| 模块关系 | 处理方式 |
|---|---|
| 多个 Module 之间存在**先后依赖**（必须完成 A 才能做 B） | 合并为一条 Happy Path 闭环，各模块作为闭环内的流转阶段 |
| 多个 Module 之间**彼此独立、可单独完成** | 每个 Module 各自对应一条独立闭环 |

#### 闭环命名规则（⚠️ 极简原则）

> 必须严格控制在 **4~8 个字**以内，去除所有修饰性、解释性的冗余词汇（如"的主干流程"、"的异常挽回"），以适应左侧面板的固定宽度。

- Happy Path：`[动词] + [核心名词]` 或 `[核心名词] + [动作]`（例：`技能升级`、`递质合成`）
- Edge Case：`[场景] + [异常/拦截/确认]`（例：`材料不足挽回`、`替换词条确认`）

#### 约束

- 单个 Stage 的闭环总数不超过 **6 条**（Happy Path ≤ 3 条，Edge Case ≤ 3 条）
- 每个闭环必须有明确的**触发起点**和**最终状态落点**

---

### Step 1.1 — groupingType 适配策略（强制）

**在执行闭环拆分前，必须先读取 `groupingType`，按以下策略确定 Loop 目标视角、Happy Path / Edge Case 识别维度与 Loop 起点规则。三种类型共用 `[校验] → [流转] → [反馈]` 三要素结构，仅目标视角和识别维度不同。**

#### 🔵 `behavioral` — 行为阶段分组

```
Loop 目标命名视角：玩家视角，动词 + 对象
  例："选定研究配方" / "发起研究" / "领取研究奖励"

Happy Path 识别维度：
  → 玩家从"产生意图"到"完成目标"的主干操作链路
  → Module 间有先后依赖 → 合并为一条 Happy Path
  → Module 间彼此独立 → 各自一条独立 Happy Path

Edge Case 识别维度：
  → 阻断玩家完成阶段目标的【资源/条件缺口】
    （如：材料不足、等级不够、前置任务未完成）
  → 高成本或不可逆操作前的【防呆拦截】
    （如：删除确认、消耗稀有资源的二次确认）

Loop 起点默认规则：
  → 该 Stage 内 layer 最浅（L1 优先）+ role: trigger 的 feature
  → 次选：layer 最浅 + role: display（"列表/面板打开"类）
```

#### 🟠 `modular` — 系统模块分组

```
Loop 目标命名视角：功能视角，使用该系统"完成某事"
  例："装备物品" / "分解多余装备" / "查看装备详情"

Happy Path 识别维度：
  → 该模块中，priority: High 的核心使用场景链路
  → 每个独立子用途（互不依赖的使用场景）各自一条 Happy Path
  → 同一模块内 priority: High 的 feature 优先进入 Happy Path 主干

Edge Case 识别维度：
  → 模块的【容量/状态边界条件】
    （如：背包已满、物品已锁定、数量不足）
  → 模块内的【误操作防呆】
    （如：不可逆操作确认、批量操作风险提示）

Loop 起点默认规则：
  → 模块的入口 feature（layer: L1 + role: trigger）
  → 通常是"进入[系统名]"或"打开[模块名]"类功能点
```

#### 🟣 `stateful` — 状态流转分组

```
Loop 目标命名视角：用户在该状态下的操作目标
  例："战斗中使用道具" / "战斗中申请暂停" / "结算中领取奖励"

Happy Path 识别维度：
  → 在该状态约束下，用户完成某个操作目标的主干路径
  → 重点关注该状态特有的操作（仅在此状态下才可执行的功能）
  → 状态内各独立操作目标各自一条 Happy Path

Edge Case 识别维度：
  → 【状态约束拦截】：某操作在当前状态下不被允许的阻断
    （如：战斗中点击邮件入口 → 被系统拦截提示"战斗中不可用"）
  → 【状态迁移触发】：用户操作引发状态改变的关键节点
    （如：使用最后复活机会 → 状态迁移至"等待复活"）

Loop 起点默认规则：
  → 该状态下用户触发某操作的入口 feature（layer: L1 + role: trigger）
  → 通常是"在[状态名]界面点击[功能入口]"类功能点
```

---

### Step 1.2 — Module 独立性判断规则

**默认假设：Stage 内多个 Module 之间为顺序依赖关系（合并为一条 Happy Path）。**

只有在检测到以下**独立性信号**时，才将 Module 拆分为独立 Loop：

| 独立性信号 | 说明 |
|---|---|
| **操作对象不同** | 两个 Module 操作的是完全不同的游戏实体/对象，且无任何 feature 语义交叉 |
| **各自闭合** | 每个 Module 内都有独立的 `role: confirm` 或 `role: feedback` 终结点，不依赖另一 Module 的数据 |
| **入口平级** | 两个 Module 的起点 feature 都是 `layer: L1 + role: trigger`，无承接语义 |

如何判断**顺序依赖**（满足任一 → 合并）：

| 依赖信号 | 说明 |
|---|---|
| **role 承接链** | Module A 以 `confirm/feedback` 结尾，Module B 以 `display` 开头且语义上展示 A 的结果 |
| **操作对象连续** | 两个 Module 操作的是同一游戏对象（同一配方、同一装备），B 的展示依赖 A 的选择结果 |
| **childModule 承接** | Module A 某 feature 的 `childModule` 指向 Module B → A 是 B 的入口，天然顺序依赖 |

---

### Step 1.3 — Edge Case 识别规则

#### 主轨（有 `role` 字段时）

```
role: "guard" 的 feature → 直接归入 Edge Case Loop，作为 [校验 ELSE IF] 的触发源
isUXSupplement: true + role: "guard" → Edge Case 的拦截节点
isUXSupplement: true + role: "feedback" → Edge Case 的反馈/引导节点
```

#### 降级（无 `role` 字段时）

从 feature `text` 语义识别 Edge Case 触发词：

| 类别 | 触发词示例 |
|---|---|
| 资源缺口 | 不足、缺少、未达到、低于 |
| 状态拦截 | 锁定、禁用、不可用、冻结、封印 |
| 容量边界 | 已满、超出上限、已达最大 |
| 操作风险 | 确认删除、不可撤销、清空、丢弃 |
| 系统阻断 | 前置条件未完成、等级不足、功能未解锁 |

> ⚠️ 降级识别**严禁补全**"网络断开""服务器维护"等与当前业务无关的通用系统级错误（防幻觉原则）。

---

### Step 1.4 — feature 在 Loop 内的排序规则

同一 Loop 内，feature 的操作顺序按以下规则确定（优先级从高到低）：

**规则 1【跨层排序】**：`layer` 越浅，操作越靠前
```
L1 → L1.5 → L2 → L2.5 → L3
```

**规则 2【入口跟进】**：有 `childModule !== null` 的 feature 先于该子模块内的所有 features

**规则 3【主轨，有 role 字段】**：同一 layer 内，按 `role` 排序
```
display → navigate → trigger → configure → confirm → feedback
（guard 按语义插入合适位置，通常在 trigger 或 confirm 之后）
```

**规则 4【降级，无 role 字段】**：从 feature `text` 语义推断类别，按以下特征词归类后排序

| 语义类别 | 对应 role | 特征词 |
|---|---|---|
| 展示/浏览类 | display | 展示、列表、显示、面板、数量、状态栏 |
| 导航/筛选类 | navigate | 筛选、搜索、过滤、排序、切换 |
| 选择/触发类 | trigger | 点击、选中、选择、开启、进入 |
| 配置/输入类 | configure | 输入、调整、设置、配置、编辑 |
| 确认/提交类 | confirm | 确认、提交、保存、完成、发起 |
| 反馈/结果类 | feedback | 成功、失败、提示、结果 / `isUXSupplement: true` |

---

### Step 1.5 — priority / isUXSupplement 利用规则

#### `priority` 字段

```
priority: High   → 必须覆盖，优先进入 Happy Path 主干流程，不允许遗漏
priority: Mid    → 应当覆盖，按流程逻辑分配到 Happy Path 或 Edge Case
priority: Low    → 可按需覆盖，优先归入 Edge Case 或 supplements[]
                   若 Stage 闭环总数已达上限（6 条），允许暂不建立独立 Loop
```

**覆盖完整性自检（每个 Stage 生成完毕后必须执行）**：
> 确认该 Stage 内所有 `priority: High` 的 feature 至少出现在一条 Loop 的 `coveredFeatures[]` 中。若有遗漏，必须补入最相近的现有 Loop 或新增一条 Loop。

#### `isUXSupplement` 字段

`isUXSupplement: true` 的 feature 代表 UX 分析师主动填补的交互空白，**几乎总是 `[反馈]` 步骤（系统响应），极少是 `[流转]` 步骤（用户操作）**。

| 组合 | Loop 内角色 |
|---|---|
| `isUXSupplement: true` + `role: "guard"` | Edge Case Loop 的校验/拦截节点 |
| `isUXSupplement: true` + `role: "feedback"` | 任意 Loop 的 `[反馈]` 步骤（错误提示/空状态/成功提示） |
| `isUXSupplement: true` + `role: "display"` | 通常是空状态 UI / 加载占位，归入对应 Loop 的 `[反馈]` |
| `isUXSupplement: true` + `role: "confirm"` | 补全的二次确认弹窗，通常触发 🔗 [锚点] |
| `isUXSupplement: true` + `priority: High` | 必须进入 Loop，且通常需要标记 🔗 [锚点] |
| `isUXSupplement: true` + `priority: Low` | 归入 `supplements[]` 作为幽灵补全节点 |

> 降级（无 `role` 字段时）：`isUXSupplement: true` 的 feature 默认作为 `[反馈]` 步骤处理。

---

### Step 1.6 — Loop 起点 / 终点识别规则

#### 起点识别（优先级从高到低）

```
规则 1【首选】：layer 最浅（L1 优先）+ role: trigger
  → 用户在基础界面主动发起的第一个操作

规则 2【次选】：layer 最浅 + role: display，且是该 Stage 的视觉入口
  → 用户进入即"看见"，是流程的起始感知点

规则 3【兜底】：该 Loop 内不依赖任何其他 feature 就能触发的第一个 feature
```

**起点排除条件（以下 feature 绝不能作为起点）**：
- `isUXSupplement: true`
- `role: "feedback"` / `"confirm"` / `"guard"`
- `layer` 非该 Loop 中最浅层级

#### 终点识别

**Happy Path 终点**：
```
→ 该 Loop 中按排序规则排在最后的 role: feedback 或 role: confirm 节点
→ 描述格式："[对象] 已 [完成状态]，[界面具体变化]"
→ 例："配方已选定，开始研究按钮高亮"
```

**Edge Case 终点**：
```
→ 异常被拦截后，用户获得引导或恢复路径的节点
→ 通常是：role: feedback（告知阻断原因 + 给出出路）
           或 isSupplement 补全的跳转入口（防死胡同）
→ 描述格式："玩家获知 [阻断原因] 并获得 [恢复路径]"
→ 例："材料不足已告知，快捷跳转获取途径入口可用"

注意：Edge Case 终点 ≠ 流程彻底终止，而是"玩家有路可走"的状态
```

---

### Step 2 — 绝对锚定与空间跃迁（Absolute Anchoring & Transition）

- **严格节点复用**：每一个动作的起点和终点，**必须**对应模式 A 已声明的具体功能点（标注 `featureId`）及 `[L层级]` 空间标签。绝不允许凭空捏造画布上不存在的 UI 容器。
- **入口点跟进**：遇到入口功能点（有 `childModule`）时，必须跟进展开子模块层，明确描述层级跃迁（弹窗覆盖 / 页面切换 / 侧边栏展开）。
- **UX 补全节点平等**：模式 A 中 `[✨UX补全]` 节点与原始节点享有同等锚定权重，不可跳过。

---

### Step 3 — 动作树三要素强校验（Action Tree Strictness）

在每个闭环的流转中，**必须**结构化呈现三要素：

1. **[校验]**：执行该流转前的底层判断条件（`IF` / `ELSE IF` / `ELSE`）
2. **[流转]**：玩家的具体物理操作（点击 / 长按 / 滑动 / 输入），或系统倒计时 / 结算推进
3. **[反馈]**：该节点带来的物理状态突变（状态刷新 / 弹窗开启 / 数据写入 / 空间跃迁）

---

#### Step 3.1 — 反馈节点强约束（⚠️ 严格执行）

每个 `feedback` 节点的 `text` **禁止模糊笼统描述**（如「弹窗打开了」「界面更新」），必须同时涵盖两个维度：

| 维度 | 字段 | 要求 | 示例 |
|---|---|---|---|
| **表现层**（玩家能感知到什么） | `expression` | 描述视觉/动效/布局变化，必须具体到控件级别 | `"配方详情弹窗从右侧以 slide-in 动效滑入，以半屏覆盖层展示于 L1 之上"` |
| **结果层**（系统内部发生了什么） | `outcome` | 描述数据写入 / 状态迁移 / 层级确立，用完成时态 | `"进入 L1.5 层级，配方详情数据加载完成，可查阅材料需求清单"` |

**`feedbackType` 枚举分级**：

**🔴 核心类型（2 类）——只要实际存在，必须各自独立输出一条 feedback 节点：**

| 枚举值 | 含义 | 典型场景 |
|---|---|---|
| `"state_change"` | 控件/按钮/数据的状态刷新 | 按钮高亮、列表更新、数值变化 |
| `"block"` | 系统阻断，操作被拦截 | 置灰、禁用、强阻断弹窗 |

**🟡 次要类型（3 类）——按实际情况决定是否输出，不强制：**

| 枚举值 | 含义 | 典型场景 |
|---|---|---|
| `"layer_transition"` | 空间层级跃迁（弹窗/侧边栏/页面切换） | 点击入口功能点触发 L1.5 弹窗开启 |
| `"data_write"` | 数据持久化写入（提交/确认/保存） | 点击确认后数据落库，流程终止 |
| `"visual_only"` | 纯视觉反馈，无状态变化 | 悬停高亮、加载动画、Toast 提示 |

> **⚠️ 多条 feedback 并列规则**：一个 `action` 节点的 `feedbacks[]` 中可以包含多条 `feedback`，每条对应一个独立的 `feedbackType`。**禁止将多种反馈类型压缩到同一条 feedback 的 `text` 中混写**。实事求是，有几条写几条，无则省略。`action` 节点不再使用 `children`，所有 feedback 均挂载于 `feedbacks[]`。

> **✦ `text` 字段保留为一句话摘要**（供编辑器面板显示），`expression` 和 `outcome` 是补充精度，供模式 D 溯源。

---

#### Step 3.2 — 校验节点强约束（⚠️ 严格执行）

每个 `validation` 节点的 `condition` **必须包含三要素**：

```
格式：[IF / ELSE IF / ELSE]: [判定主体] + [判定标准] + [数值范围/具体门槛（如有）]

✅ 正确：IF: 玩家背包中目标材料持有量 ≥ 配方所需量
✅ 正确：ELSE IF: 存在任意材料项持有量 < 所需量（材料缺口场景）
❌ 错误：IF: 条件满足
❌ 错误：IF: 状态正确
```

**每个 `validation` 节点还必须填写 `elseNote` 字段**，说明「不满足此条件时的走向」——即使该异常走向在另一条 Loop 里，也必须在此注明，保证阅读单条 Loop 时能感知完整分支全貌：

```json
"elseNote": "不满足时 → 进入「材料不足挽回」Edge Case Loop（n2050）"
```

若无对应 Edge Case（条件天然成立，无异常路径），填：
```json
"elseNote": "无异常路径，条件天然满足（如系统初始化后必然存在的状态）"
```

---

**遇到以下场景，必须打上 `🔗 [锚点]`，标记为模式 D 的接力触发点：**

| 触发条件 | 说明 |
|---|---|
| 涉及**复杂数据展示**的反馈 | 如结算面板、多字段配置弹窗 |
| 涉及**重度异常阻断**的反馈 | 如强阻断二次确认框、不可逆操作提示 |
| 模式 B 已无法精确描述 UI 细节 | 需要模式 D 接力补全交互规范 |

---

### Step 4 — 防幻觉自检

> **⚠️ Anti-Hallucination — 极致防幻觉原则**
>
> - **严禁虚构节点**：每一步流转只能引用模式 A 已声明的 Feature，不得自行发明未声明的功能点
> - **严禁虚构底层机制**：绝不脑补「网络断开」「服务器维护」等与当前具体业务无关的系统级错误
> - **克制补全**：仅在发现「死胡同（无返回/挽回路径）」或「盲操（无二次确认）」时，使用 `[✨流转补全]` 增加逻辑连线，并在下一缩进标注补全依据

---

## 生成法则（强制遵循）

1. **节点忠实法则**：流转步骤只能引用模式 A 已声明的功能节点。唯一例外是 `[✨流转补全]` 标注的防死胡同补全。

2. **层级跟进法则**：遇到入口功能点（`childModule !== null`）必须展开子模块层，不得在入口层停留描述子模块内容。

3. **动词物理化法则**：流转步骤描述玩家的**具体物理动作**（点击、长按、滑动、输入），不描述抽象意图（「查看」→「点击查看按钮」，「选择」→「点击目标卡片」）。

4. **反馈确定性法则**：每个流转步骤必须有对应反馈，不允许「用户操作后系统无响应」的断点。

5. **分支闭环法则**：所有 `ELSE` / `ELSE IF` 分支必须有明确出口（继续主流程 / 中断并引导 / 回退重试），不允许悬空分支。

6. **锚点触发法则**：凡涉及复杂 UI 细节或重度异常的反馈节点，**必须**打 `🔗 [锚点]`，不得遗漏。

7. **反馈双维法则**：每个 `feedback` 节点必须同时包含 `expression`（玩家可感知的视觉/动效表现）和 `outcome`（系统内部状态/数据结果），并从 5 类 `feedbackType` 枚举中为该条 feedback 选择一个最匹配的类型标注。禁止用一句模糊描述混淆两个维度。一个 `action` 允许（且在必要时应当）挂载多条并列 `feedback`，每条独立标注自己的 `feedbackType`：**核心类型（`state_change` / `block`）只要在当前操作中实际存在，必须各自独立产出一条 feedback**；次要类型（`layer_transition` / `data_write` / `visual_only`）按实际情况决定，实事求是，有则写，无则省。

8. **条件具体化法则**：每个 `validation` 节点的 `condition` 必须包含「判定主体 + 判定标准 + 数值门槛（如有）」，禁止写「IF: 条件满足」等空泛文本。同时必须填写 `elseNote` 注明不满足时的走向（跨 Loop 引用亦可），保证单条 Loop 内分支全貌可读。

---

## 输出符号语法（强约束）

| 符号 | 含义 |
|---|---|
| `**[所属阶段]**` | 对应模式 A 的 Stage 名称 |
| `**[闭环目标]**` | 该剧本的核心业务目的 |
| `**[起点]**` | 触发该闭环的初始操作节点，需带 `← featureId` + `[L层级]` |
| `**[校验 IF / ELSE IF / ELSE]**` | 执行流转前的底层条件判断 |
| `**[流转]**` | 玩家物理操作或系统推进，需带 `← featureId` |
| `**[反馈]**` | 系统状态突变或空间跃迁，需带目标 `[L层级]`；**在 JSON 中为 `action` 的 `feedbacks[]` 子数组，不是 `children`，也不是 `validation` 下的平铺兄弟节点** |
| `🔗 **[锚点]**` | 标记为模式 D 的接力触发点 |
| `[✨流转补全]` | 非模式 A 原有节点，主动补全的防死胡同连线 |

---

## 输出格式模板（Scenario-based Action Tree）

```markdown
# 🕹️ [Stage 名称] 动态流转剧本
> **所属阶段**：[对应模式 A 的 Stage 名称]
> **覆盖节点**：`f001` `f003` `f005` ...

---

### 闭环 1：[极简标题]（Happy Path）
**[闭环目标]** [一句话描述该闭环的业务目的]
**[起点]** 玩家在 `[L1]` [界面名称] 点击 [功能点名称] `← f001`

  **[校验 IF: 满足前置条件 A 且 满足前置条件 B]**
    **[流转]** [具体物理操作] `← f002`
      **[反馈]** `[L1]` 面板状态刷新，[具体变化描述]

    **[流转]** 点击 [入口功能点名称] `← f003` 【空间跃迁 → L1.5】
      **[反馈]** `[L1.5]` [弹窗/侧边栏] 开启，展示 [内容描述] � **[锚点]**

    **[流转]** [完成操作] `← f005`
      **[反馈]** 数据写入，状态落点：[最终状态描述]

---

### 闭环 2：[极简标题]（Edge Case）
**[闭环目标]** [一句话描述该边界场景的防护目的]
**[起点]** 玩家在 `[L1]` [界面名称] 点击 [功能点名称] `← f001`

  **[校验 ELSE IF: 缺少前置条件 A（如：核心材料不足）]**
    **[流转]** 系统执行强阻断
      **[反馈]** `[L1.5]` Toast 弹出，告知具体不足项

    **[流转]** 玩家点击快捷跳转入口 `← f006` `[✨流转补全: 防阻断捷径]` 【空间跃迁 → L2】
      **[反馈]** `[L2]` 材料获取途径面板弹出 🔗 **[锚点]**

---

### 闭环 3：[极简标题]（Edge Case）
**[闭环目标]** [一句话描述该临界场景的拦截目的]
**[起点]** 玩家在 `[L1]` [界面名称] 尝试进行 [高成本动作] `← f001`

  **[校验 IF: 目标模块已达上限/满载]**
    **[流转]** 拦截玩家的确认操作
      **[反馈]** `[L1.5]` 二次确认弹窗开启，提示满载并提供清理入口 🔗 **[锚点]**
```

---

## 完整输出示例

以下为行为阶段分组 🔵「A.准备阶段」的完整输出：

```markdown
# �️ A.准备阶段 动态流转剧本
> **所属阶段**：A.准备阶段（行为阶段分组 🔵）
> **覆盖节点**：`f001` `f002` `f003` `f004` `f005` `f006`

---

### 闭环 1：选定研究配方（Happy Path）
**[闭环目标]** 玩家在配方列表中完成评估，确认选中目标配方并准备发起研究
**[起点]** 玩家在 `[L1]` 科技台主面板，滑动浏览配方列表 `← f001`

  **[校验 IF: 存在可研究配方]**
    **[流转]** 点击目标配方卡片 `← f002` 【空间跃迁 → L1.5】
      **[反馈]** `[L1.5]` 配方详情弹窗从右侧滑入，覆盖于 `[L1]` 之上

    **[流转]** 查阅配方名称与材料需求清单 `← f003` `← f004`
      **[反馈]** `[L1.5]` 弹窗内各材料项展示当前持有量与所需量对比 � **[锚点]**

  **[校验 IF: 全部材料充足]**
    **[流转]** 点击「确认选定」按钮 `← f005`
      **[反馈]** `[L1.5]` 弹窗关闭，`[L1]` 预览区更新为已选配方，「开始研究」按钮高亮，状态落点：配方已选定

---

### 闭环 2：材料不足挽回（Edge Case）
**[闭环目标]** 识别材料缺口后为玩家提供快捷获取路径，避免操作死胡同
**[起点]** 玩家在 `[L1.5]` 配方详情弹窗内，查阅材料需求清单 `← f004`

  **[校验 ELSE IF: 存在材料不足项]**
    **[流转]** 系统标记不足材料项
      **[反馈]** `[L1.5]` 不足材料行以红色高亮，数量缺口显著标注，「确认选定」按钮置灰

    **[流转]** 玩家点击材料获取跳转入口 `← f006` `[✨流转补全: 防阻断捷径]` 【空间跃迁 → L2】
      > 依据：弹窗内缺口信息呈现后若无跳转路径，玩家将被迫关闭弹窗自行查找，形成操作死胡同
      **[反馈]** `[L2]` 材料获取途径面板弹出，展示快捷收集方式 🔗 **[锚点]**

---

### 闭环 3：配方列表为空（Edge Case）
**[闭环目标]** 当玩家尚未解锁任何配方时，给予明确引导而非白屏
**[起点]** 玩家在 `[L1]` 科技台主面板打开配方列表 `← f001`

  **[校验 ELSE IF: 无可研究配方（科技等级未达解锁条件）]**
    **[流转]** 系统渲染空状态界面
      **[反馈]** `[L1]` 配方列表区展示空状态插图与「暂无可研究配方」文案

    **[流转]** 玩家点击「查看解锁条件」 `[✨流转补全: 降门槛引导]` 【空间跃迁 → L1.5】
      > 依据：空状态无任何出路将导致玩家无从操作，提供解锁路径是最低限度的导航补全
      **[反馈]** `[L1.5]` 解锁条件说明弹窗开启，状态落点：玩家获知升级路径
```

---

## JSON 输出规范

### 字段约束备忘（生成前必读）

| 字段 | 挂载节点 | 约束规则 |
|---|---|---|
| `refStage` | Loop 顶层 | **必须填 Stage 的 `id` 字段**（如 `"s001"`），严禁填 `label`（如 `"A.准备阶段"`）。`getActiveStageLoops()` 以 `id` 匹配，填 `label` 将导致连线数据为空。 |
| `isAnchor` | **action 节点** | **只能挂在 `kind: "action"` 节点上**，严禁挂在 `feedback` 节点。action 有 `refFeature` 可定位 DOM，feedback 通常无法定位，挂在 feedback 上会导致 Phase 5 锚点徽章渲染失效。 |
| `refFeature` | action / feedback | action 节点**必填**（不可为 null）；feedback 节点**在有对应 feature 时填写**，无明确对应节点时填 `null`。 |
| `refNearFeature` | supplements[] 子项 | **必填**。指定幽灵节点挂载的最近 Feature ID（引用 Mode A 已声明节点）。`renderSupplementGhosts()` 依赖此字段决定幽灵节点挂载到哪张卡片，缺失将导致 Phase 5 幽灵节点无法渲染。 |
| `feedbackType` | **feedback 节点** | **必填枚举**（每条 feedback 各选其一）：🔴 核心类型 `"state_change"` / `"block"` 实际存在时必须各自独立一条；🟡 次要类型 `"layer_transition"` / `"data_write"` / `"visual_only"` 按实际情况输出。一个 action 可挂载多条并列 feedback，禁止混写压缩。用于编辑器面板颜色分类和模式 D 溯源。 |
| `expression` | **feedback 节点** | **必填**。玩家可感知的视觉/动效/布局变化，具体到控件级别。禁止写「界面更新」等模糊描述。 |
| `outcome` | **feedback 节点** | **必填**。系统内部状态迁移 / 数据写入 / 层级确立，用完成时态描述。`feedbackType: "visual_only"` 时可填 `null`。 |
| `elseNote` | **validation 节点** | **必填**。说明不满足当前 condition 时的走向，只写**纯文字描述**，不承载 Loop ID。无异常路径时填「无异常路径，条件天然满足」。 |
| `targetLoopId` | **validation 节点** | 不满足条件时跳转的目标 Loop ID（如 `"n2050"`）。有跨 Loop 跳转时**必填**；无跳转时填 `null`。 |
| `elseLoopType` | **validation 节点** | 目标 Loop 的类型，枚举 `"happy_path"` / `"edge_case"`。有跨 Loop 跳转时**必填**，决定编辑器中下划线文本颜色（绿色 / 红色）；无跳转时填 `null`。 |

---

```json
{
  "A": { "// 注释": "填写模式 A 输出的完整 JSON 对象，保留完整数据链供模式 D 溯源" },
  "B": [
    {
      "id": "n2001",
      "title": "选定研究配方",
      "type": "happy_path",
      "refStage": "s001",
      "startPoint": "玩家在 L1 科技台主面板滑动浏览配方列表",
      "endPoint": "配方已选定，开始研究按钮高亮",
      "collapsed": false,
      "coveredFeatures": ["f001", "f002", "f003", "f004", "f005"],
      "steps": [
        {
          "id": "n2010",
          "kind": "validation",
          "condition": "IF: 配方列表中存在至少一条已解锁且可研究的配方",
          "elseNote": "配方列表为空，渲染空状态界面引导玩家解锁配方",
          "targetLoopId": "n2100",
          "elseLoopType": "edge_case",
          "children": [
            {
              "id": "n2011",
              "kind": "action",
              "text": "点击目标配方卡片",
              "refFeature": "f002",
              "triggersLayer": "L1.5",
              "isAnchor": false,
              "isSupplement": false,
              "feedbacks": [
                {
                  "id": "n2012",
                  "kind": "feedback",
                  "text": "L1.5 配方详情弹窗从右侧滑入",
                  "feedbackType": "layer_transition",
                  "expression": "配方详情弹窗从右侧以 slide-in 动效滑入，以半屏覆盖层叠加于 L1 主面板之上",
                  "outcome": "进入 L1.5 层级，配方详情数据（名称、材料列表、所需量）加载完成，可查阅",
                  "refFeature": null,
                  "targetLayer": "L1.5"
                }
              ]
            },
            {
              "id": "n2013",
              "kind": "action",
              "text": "查阅材料需求清单",
              "refFeature": "f004",
              "triggersLayer": null,
              "isAnchor": true,
              "isSupplement": false,
              "feedbacks": [
                {
                  "id": "n2014",
                  "kind": "feedback",
                  "text": "弹窗内各材料行展示持有量与所需量对比",
                  "feedbackType": "state_change",
                  "expression": "每个材料行并排展示「当前持有量 / 所需量」，持有量不足的行以红色高亮标注缺口数值",
                  "outcome": "玩家已获知全部材料的充足/缺口状态，系统缓存材料校验结果供后续 IF 条件使用",
                  "refFeature": "f004",
                  "targetLayer": "L1.5"
                }
              ]
            }
          ]
        },
        {
          "id": "n2015",
          "kind": "validation",
          "condition": "IF: 玩家背包中所有配方所需材料的持有量均 ≥ 所需量",
          "elseNote": "材料不足，触发缺口提示与跳转入口，引导玩家补齐材料",
          "targetLoopId": "n2050",
          "elseLoopType": "edge_case",
          "children": [
            {
              "id": "n2016",
              "kind": "action",
              "text": "点击确认选定按钮",
              "refFeature": "f005",
              "triggersLayer": null,
              "isAnchor": false,
              "isSupplement": false,
              "feedbacks": [
                {
                  "id": "n2017a",
                  "kind": "feedback",
                  "text": "「开始研究」按钮从置灰切换为高亮可点击态",
                  "feedbackType": "state_change",
                  "expression": "L1 预览区卡片切换为已选配方信息，「开始研究」按钮从置灰态切换为高亮可点击态",
                  "outcome": "配方选定状态写入临时存储，startPoint 确立",
                  "refFeature": null,
                  "targetLayer": "L1"
                },
                {
                  "id": "n2017b",
                  "kind": "feedback",
                  "text": "L1.5 弹窗关闭，配方选定数据落库",
                  "feedbackType": "data_write",
                  "expression": "L1.5 弹窗以 fade-out 动效消失，返回 L1 主面板",
                  "outcome": "配方选定状态持久化写入，等待玩家触发研究流程",
                  "refFeature": null,
                  "targetLayer": "L1"
                }
              ]
            }
          ]
        }
      ],
      "supplements": []
    },
    {
      "id": "n2050",
      "title": "材料不足挽回",
      "type": "edge_case",
      "refStage": "s001",
      "startPoint": "玩家在 L1.5 配方详情弹窗查阅材料需求清单",
      "endPoint": "L2 材料获取途径面板开启",
      "collapsed": false,
      "coveredFeatures": ["f004", "f006"],
      "steps": [
        {
          "id": "n2051",
          "kind": "validation",
          "condition": "ELSE IF: 存在材料不足项",
          "children": [
            {
              "id": "n2052",
              "kind": "action",
              "text": "系统标记不足材料项",
              "refFeature": null,
              "triggersLayer": null,
              "isAnchor": false,
              "isSupplement": false,
              "feedbacks": [
                {
                  "id": "n2053",
                  "kind": "feedback",
                  "text": "不足材料行红色高亮，确认选定按钮置灰",
                  "feedbackType": "block",
                  "expression": "不足材料行以红色高亮标注，「确认选定」按钮切换为置灰不可点击态",
                  "outcome": "系统阻断选定操作，缺口状态渲染完成",
                  "refFeature": null,
                  "targetLayer": "L1.5"
                }
              ]
            },
            {
              "id": "n2054",
              "kind": "action",
              "text": "点击材料获取跳转入口",
              "refFeature": "n2060",
              "triggersLayer": "L2",
              "isAnchor": false,
              "isSupplement": true,
              "feedbacks": [
                {
                  "id": "n2055",
                  "kind": "feedback",
                  "text": "L2 材料获取途径面板弹出",
                  "feedbackType": "layer_transition",
                  "expression": "L2 材料获取途径面板从底部滑入覆盖当前界面",
                  "outcome": "进入 L2 层级，材料获取途径数据加载完成",
                  "refFeature": null,
                  "targetLayer": "L2"
                }
              ]
            }
          ]
        }
      ],
      "supplements": [
        {
          "id": "n2060",
          "refNearFeature": "f004",
          "text": "材料获取跳转入口",
          "reason": "[流转补全] 弹窗内缺口信息呈现后若无跳转路径，玩家将被迫关闭弹窗自行查找，形成操作死胡同。n2054 步骤以 refFeature: n2060 引用本节点，确保写入画布后自动完成连线。"
        }
      ]
    }
  ],
  "C": [],
  "D": []
}
```

### 字段说明

| 字段 | 取值范围 | 说明 |
|---|---|---|
| `A` | 对象 | 模式 A 输出的**完整 JSON 对象**，保留完整数据链供模式 D 溯源；AI 生成时必须原样透传，不得裁剪或省略 |
| `B` | 数组 | 本模式 B 生成的 Goal Loop 数组（本文档定义的核心输出） |
| `C` | 数组 | 保留字段，模式 C（信息架构）使用；模式 B 输出时填空数组 `[]` |
| `D` | 数组 | 保留字段，模式 D（交互稿）使用；模式 B 输出时填空数组 `[]` |
| `type` | `"happy_path"` / `"edge_case"` | 闭环类型 |
| `refStage` | 模式 A Stage 的 **`id` 字段值**（如 `"s001"`） | 所属阶段溯源，**严禁填 `label`** |
| `coveredFeatures` | `["f001", ...]` | 引用的模式 A Feature ID 列表 |
| `steps[].kind` | `"validation"` / `"action"` | steps 树中只有这两种节点；**`feedback` 不直接出现在 steps 树中，而是挂载在 `action.feedbacks[]` 数组里** |
| `steps[].condition` | `"IF: ..."` / `"ELSE IF: ..."` / `"ELSE"` | 校验条件（仅 validation 类型有此字段） |
| `action.refFeature` | Feature `id` / `null` | 锚定模式 A 的功能节点（action 步骤专属）。**当 `isSupplement: true` 且对应功能点在模式 A 中不存在时，必须填入同一 Loop 的 `supplements[].id`（如 `"n2060"`），而非 `null`。编辑器依赖此字段将步骤与新建的幽灵节点连线，填 `null` 将导致连线永久缺失。** |
| `feedback.refFeature` | Feature `id` / `null` | 有明确对应节点时填写，无则为 `null` |
| `triggersLayer` | `"L1.5"` / `"L2"` / `"L2.5"` / `"L3"` / `null` | 入口触发的目标层级（action 步骤专属） |
| `isAnchor` | `true` / `false` | 是否为模式 D 接力锚点；**挂在 action 步骤上**，标记该 action 对应的 feature 节点为接力点 |
| `isSupplement` | `true` / `false` | 是否为流转补全节点（action 步骤专属）。分两种情况：① 引用**已有** Mode A 功能点（`refFeature: "f006"`）→ 该功能点原本存在但未被 B 覆盖；② 引用**新建**补全节点（`refFeature: "n2060"`，与 `supplements[].id` 一致）→ 该功能点在 Mode A 中完全不存在，由 `renderSupplementGhosts` 自动写入画布。 |
| `supplements[].refNearFeature` | Feature `id` | 幽灵节点挂载的最近 Feature ID（引用模式 A 已声明节点）。注意：`supplements[].id` 与引用它的 `action.refFeature` 必须保持一致，编辑器以此完成步骤到幽灵节点的连线。 |

### ID 生成规则

- 模式 B 所有 `id` 从 `n2001` 起始，每个新元素递增 1
- Happy Path 闭环 ID 从 `n2001` 起始
- Edge Case 闭环 ID 从 `n2050` 起始（每个新 Edge Case 块 +50）

---

## 降级处理（无模式 A 数据时）

若用户未提供模式 A 的 JSON，自动进入**降级模式**：

1. 在回复开头声明：
   ```
   ⚠️ 未检测到模式 A 数据，将基于策划案描述独立生成行为路径（降级模式）。
   建议先执行模式 A 分析以获得完整数据链支持。
   ```
2. 执行逻辑退回原版（直接从策划案文本推导闭环，不做 Feature ID 锚定）
3. 输出 JSON 中 `refStage`、`refFeature` 字段均为 `null`，`coveredFeatures` 为空数组

---

## 边界情况处理

**情况 1：模式 A 某 Stage 内仅有 1 个 Module**
直接以该 Module 的核心操作作为唯一 Happy Path 闭环，Edge Case 按防幻觉原则扫描补全。

**情况 2：功能点的 `childModule` 嵌套超过 2 层（如 L1 → L1.5 → L2 → L2.5）**
按层级逐层展开，每次层级跃迁标注目标层级，确保路径层级深度与模式 A 的声明完全对应。

**情况 3：`[✨UX补全]` 功能点归属不明确**
优先归入与其功能语义最近的闭环；若两个闭环同等相关，归入 Happy Path 闭环，并在 `coveredFeatures` 中标注。

**情况 4：同一 Stage 内 Happy Path 与 Edge Case 共用同一起点**
两条闭环独立声明，**不合并**。共用起点在各自的 `**[起点]**` 行重复写明，由校验条件（`IF` vs `ELSE IF`）区分走向。