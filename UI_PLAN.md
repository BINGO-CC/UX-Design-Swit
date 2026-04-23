
# 可交互原型生成系统 开发计划

> **版本**：v1.0（2026-04-10）
> **目标**：基于 Mode A + Mode B + Mode D 串联输出，结合 Design System Profile，自动生成绑定真实组件库的可交互 HTML 原型
> **组件库**：❓ 待确认（候选：Yike Design / 其他，见第九节 Q0）
> **核心产出**：`prototype-generator.js` + `design-system-profile.json` + 可交互 HTML 原型

> ⚠️ **开发记录规则**：本文件是原型生成系统的**唯一**开发计划与记录文件。所有会话产生的开发日志、QA 修订、BUG 修复、待办事项，**一律追加写入本文件对应章节**，禁止新建额外记录文件。

---

## 一、整体流水线架构

```
┌─────────────────────────────────────────────────────────────┐
│                      INPUT 输入层                            │
│  策划案文本  +  项目设计规范文档  +  【待定】组件库文档         │
└──────────────────┬──────────────────────┬───────────────────┘
                   │                      │
                   ▼                      ▼
┌──────────────────────────┐  ┌────────────────────────────────┐
│  Mode A：功能节点提取     │  │  Design System Profile (DSP)   │
│  → stages/modules/       │  │  → 组件注册表 (Component Map)   │
│    features JSON         │  │  → Token 对照表 (Token Map)     │
│  → role / layer /        │  │  → 布局模板库 (Layout Patterns) │
│    priority / childModule │  │  → 交互规范约束 (Rules)         │
└──────────┬───────────────┘  └──────────────┬─────────────────┘
           │                                 │
           ▼                                 │
┌──────────────────────────┐                 │
│  Mode B：行为路径剧本     │                 │
│  → Goal Loops            │                 │
│  → steps[] 状态机        │                 │
│  → Happy Path +          │                 │
│    Edge Case             │                 │
└──────────┬───────────────┘                 │
           │                                 │
           ▼                                 │
┌──────────────────────────┐                 │
│  Mode D：交互稿输出       │◄────────────────┘
│  → 组件语义描述           │  注入 DSP 上下文
│  → 状态定义              │
│  → 系统边界补全           │
│  → 防御性设计            │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│              原型生成引擎（Prototype Generator）              │
│                                                             │
│  输出 A：HTML 可交互原型（绑定【待定】组件库 CSS + Token）     │
│  输出 B：Vue 组件代码（绑定【待定】组件库）                   │
│  输出 C：交互说明文档（供开发/美术参考）                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、各环节职责说明

### 2.1 Mode A（已有）
- **输入**：策划案文本
- **输出**：`storeA JSON`（stages → modules → features，含 role/layer/priority/childModule）
- **状态**：✅ 已实现（见 `MINDMAP_EDITOR_DEV_PLAN.md`）

### 2.2 Mode B（已有）
- **输入**：Mode A JSON
- **输出**：`storeB JSON`（Goal Loops → steps[]，含 validation/action/feedback 三要素）
- **状态**：✅ 已实现（见 `MINDMAP_EDITOR_DEV_PLAN.md`）

### 2.3 Mode D（已有 Prompt 规范）
- **输入**：Mode B JSON + DSP 上下文
- **输出**：交互稿 Markdown（组件语义描述 + 状态定义 + 系统边界）
- **状态**：📄 Prompt 规范已定义，待与 DSP 联调

### 2.4 Design System Profile（本计划核心）
- **输入**：❓ 待确认的组件库文档（见第九节 Q0）
- **输出**：`design-system-profile.json`
- **状态**：🔲 待开发（需组件库确认后启动，本计划核心环节）

### 2.5 原型生成引擎（本计划核心）
- **输入**：Mode D 输出 + DSP JSON
- **输出**：可交互 HTML 原型
- **状态**：🔲 待开发

---

## 三、Design System Profile 数据结构规范

### 3.1 完整 JSON Schema

```json
{
  "meta": {
    "library": "【待确认】",
    "version": "latest",
    "prefix": "【待确认，如 Yk / El / A 等】",
    "sourceUrl": "【待确认组件库文档地址】",
    "extractedAt": "2026-04-10"
  },

  "componentRegistry": [
    {
      "semanticName": "主操作按钮",
      "componentId": "【待确认，如 YkButton / ElButton 等】",
      "importFrom": "【待确认组件库包名】",
      "category": "通用",
      "props": {
        "type": ["primary", "secondary", "outline"],
        "size": ["s", "m", "l", "xl"],
        "shape": ["round", "circle", "square"],
        "status": ["primary", "success", "warning", "danger"],
        "disabled": "boolean",
        "loading": "boolean",
        "long": "boolean"
      },
      "defaultProps": { "type": "primary", "size": "l" },
      "slots": ["default", "icon"],
      "usageRule": "触发不可逆操作或核心流程推进，同区域建议最多出现一次",
      "modeD_keywords": ["主操作按钮", "确认按钮", "提交按钮", "核心操作", "发起操作"]
    }
  ],

  "tokenMap": {
    "colorTokens": {
      "主操作色":   "【待确认，如 --yk-color-primary 等】",
      "成功色":     "【待确认】",
      "警告色":     "【待确认】",
      "危险色":     "【待确认】",
      "禁用色":     "【待确认】",
      "背景底色":   "【待确认】",
      "卡片背景":   "【待确认】",
      "主文字":     "【待确认】",
      "次要文字":   "【待确认】",
      "边框色":     "【待确认】"
    },
    "spacingTokens": {
      "紧凑间距":   "【待确认】",
      "标准间距":   "【待确认】",
      "宽松间距":   "【待确认】"
    },
    "radiusTokens": {
      "小圆角":     "【待确认】",
      "标准圆角":   "【待确认】",
      "全圆角":     "【待确认】"
    }
  },

  "layoutPatterns": [
    {
      "semanticName": "顶栏 + 内容区 + 底部操作栏",
      "templateId": "page-with-footer",
      "structure": "header(fixed) + main(scroll) + footer(fixed)",
      "usage": "需要固定操作区的全屏页面，如表单页、详情页"
    },
    {
      "semanticName": "左侧列表 + 右侧详情",
      "templateId": "master-detail",
      "structure": "aside(40%) + main(60%)",
      "usage": "配方选择、道具管理等需要对比查看的场景"
    },
    {
      "semanticName": "网格卡片列表",
      "templateId": "grid-list",
      "structure": "grid(2~4 cols, auto rows)",
      "usage": "物品/道具/配方等同质化内容批量展示"
    }
  ],

  "interactionRules": {
    "layerRules": {
      "L1": "全屏独立页面，关闭回 HUD",
      "L1.5": "【待确认】抽屉 / 半屏弹窗组件，关闭回 L1",
      "L2": "全屏二级页面（push 切换），关闭回 L1",
      "L2.5": "【待确认】小弹窗组件，关闭回 L2",
      "L3": "全屏三级页面，严格控制，必须附理由"
    },
    "modalStackLimit": 2,
    "irreversibleActions": {
      "rule": "消耗/删除/提交类操作必须使用【待确认】气泡确认 / 对话框组件 二次确认",
      "forbidden": "Toast 不可替代二次确认弹窗"
    },
    "emptyState": {
      "rule": "列表为空时必须使用【待确认】空状态组件，且提供至少一个操作入口",
      "forbidden": "纯文字空状态"
    },
    "loadingState": {
      "rule": "数据加载中使用【待确认】骨架屏组件",
      "forbidden": "白屏 + 加载动画（首屏加载禁用）"
    },
    "buttonLoading": {
      "rule": "提交操作后按钮立即进入 loading 态，防重复点击"
    }
  }
}
```

---

## 四、分批开发计划

---

### Batch 1 — 组件库爬取 🔲 待开发（⚠️ 前置依赖 Q0）

**目标**：自动抓取目标组件库所有组件页面，提取组件名称、Props API、使用说明

> ⚠️ **前置依赖**：需等待第九节 Q0「组件库选型」决策完成后方可启动。

| 任务 | 说明 | 状态 |
|---|---|---|
| B1-0 确认组件库文档地址 | 根据 Q0 决策锁定目标组件库文档站 URL | ⏳ 阻塞中 |
| B1-1 遍历组件导航列表 | 从文档站导航页提取所有组件链接 | 🔲 |
| B1-2 逐页爬取 API 表格 | 提取每个组件的 Props/类型/默认值 | 🔲 |
| B1-3 提取 Slots 定义 | 提取每个组件的插槽说明 | 🔲 |
| B1-4 提取使用示例描述 | 从组件介绍文字提取使用场景 | 🔲 |
| B1-5 构建原始组件数据 JSON | 输出 `raw-components.json` | 🔲 |

**验收**：`raw-components.json` 包含目标组件库全部组件的完整 API 信息

---

### Batch 2 — 组件注册表构建（Component Registry）🔲 待开发（依赖 B1 完成）

**目标**：在原始数据基础上，为每个组件补充语义别名和 Mode D 关键词映射

| 任务 | 说明 | 状态 |
|---|---|---|
| B2-1 通用组件注册 | Button / Icon / Typography / Link | 🔲 |
| B2-2 布局组件注册 | Space / Divider | 🔲 |
| B2-3 导航组件注册 | Anchor / Breadcrumb / Dropdown / Pagination / Scrollbar | 🔲 |
| B2-4 数据录入组件注册 | Input / Form / Checkbox / Radio / Switch / Slider / Upload 等 | 🔲 |
| B2-5 数据展示组件注册 | Table / Tabs / Tag / Badge / Avatar / Tree / Collapse / Empty / Skeleton 等 | 🔲 |
| B2-6 反馈组件注册 | Modal / Drawer / Message / Alert / Tooltip / Popover / Popconfirm / Progress / Spinner 等 | 🔲 |
| B2-7 modeD_keywords 语义映射 | 为每个组件填写 Mode D 可能输出的中文语义词 | 🔲 |
| B2-8 usageRule 使用规则填写 | 何时用 A 而不用 B 的判断规则 | 🔲 |

**验收**：`component-registry.json` 覆盖全部组件，每个组件至少有 3 条 `modeD_keywords`

---

### Batch 3 — Token 对照表构建（Token Map）🔲 待开发（⚠️ 前置依赖 Q0）

**目标**：从目标组件库色彩页面提取完整色彩系统，建立语义色 → CSS 变量映射

| 任务 | 说明 | 状态 |
|---|---|---|
| B3-1 爬取 Color 页面 | 访问组件库色彩文档页，提取所有颜色分类 | 🔲 |
| B3-2 提取主色/辅色系统 | primary / success / warning / danger 色阶 | 🔲 |
| B3-3 提取中性色/文字色 | 背景/边框/文字/占位色 | 🔲 |
| B3-4 提取 CSS 变量名 | 检查实际 CSS 变量命名规则 | 🔲 |
| B3-5 建立语义 → 变量对照表 | "主操作色" → 实际 CSS 变量名 | 🔲 |
| B3-6 补充间距/圆角 Token | 从间距/排版页面提取 | 🔲 |

**验收**：`token-map.json` 覆盖颜色/间距/圆角三类 Token，语义名称与 Mode D 描述一致

---

### Batch 4 — 布局模板库构建（Layout Patterns）🔲 待开发

**目标**：基于常见 UI 场景建立布局模板，每个模板对应可直接使用的 HTML/CSS 骨架

| 任务 | 说明 | 状态 |
|---|---|---|
| B4-1 全屏页面模板 | Header + Scroll Content + Fixed Footer | 🔲 |
| B4-2 Master-Detail 模板 | 左侧列表 + 右侧详情（对应 L1 + L1.5 分屏） | 🔲 |
| B4-3 网格卡片模板 | 2/3/4 列自适应网格 | 🔲 |
| B4-4 弹窗内容模板 | Modal 内：标题 + 内容区 + 底部操作栏 | 🔲 |
| B4-5 表单页模板 | Label + Input 行列布局 | 🔲 |
| B4-6 空状态模板 | 空状态组件 + 操作引导入口 | 🔲 |
| B4-7 骨架屏模板 | 骨架屏组件 列表/卡片/详情页变体 | 🔲 |

**验收**：每个模板有完整 HTML 代码片段，可直接嵌入原型生成引擎

---

### Batch 5 — 交互规范约束文档（Interaction Rules）🔲 待开发

**目标**：定义项目级交互约束，防止 Mode D 生成越界内容

| 任务 | 说明 | 状态 |
|---|---|---|
| B5-1 层级实现规则 | L1~L3 各层对应【待定】组件库哪个组件承载 | 🔲 |
| B5-2 弹窗堆叠规则 | 最大堆叠数 + 禁止规则 | 🔲 |
| B5-3 不可逆操作规则 | 哪类操作必须气泡确认框 / 对话框二次确认 | 🔲 |
| B5-4 空状态规则 | 强制使用空状态组件 + 操作引导 | 🔲 |
| B5-5 加载状态规则 | 骨架屏 vs 加载动画使用边界 | 🔲 |
| B5-6 按钮状态规则 | 提交后 loading 态 + 防重复点击 | 🔲 |
| B5-7 文案规范 | 按钮 ≤4 字、Toast ≤16 字等约束 | 🔲 |

**验收**：`interaction-rules.json` 可作为约束条件注入 Mode D Prompt

---

### Batch 6 — DSP 整合 + Mode D 联调 🔲 待开发

**目标**：将 B1~B5 产出整合为完整 `design-system-profile.json`，注入 Mode D 验证输出质量

| 任务 | 说明 | 状态 |
|---|---|---|
| B6-1 整合四个子模块 | 组件注册表 + Token + 布局 + 规则 → 单一 JSON | 🔲 |
| B6-2 构建 Mode D 注入模板 | System Prompt 模板，含 DSP 上下文插槽 | 🔲 |
| B6-3 用真实策划案端到端测试 | A → B → D（注入 DSP）→ 验收输出 | 🔲 |
| B6-4 验证组件名称命中率 | Mode D 输出中【待定】组件库组件名准确率 ≥ 85% | 🔲 |
| B6-5 修订 modeD_keywords | 根据测试结果补充未命中的语义词 | 🔲 |

**验收**：Mode D 输出中的组件描述与【待定】组件库一一对应，无幻觉组件名称

---

### Batch 7 — 原型生成引擎（Prototype Generator）🔲 待开发

**目标**：接受 Mode D 输出 + DSP，自动生成可在浏览器运行的 HTML 交互原型

| 任务 | 说明 | 状态 |
|---|---|---|
| B7-1 输入解析器 | 解析 Mode D Markdown 结构（元素状态 / 交互流 / 系统边界）| 🔲 |
| B7-2 组件匹配引擎 | 用 modeD_keywords 将语义描述映射到【待定】组件库具体组件 | 🔲 |
| B7-3 状态机生成 | 将 Mode B steps[] 转为 JS 状态机（IF/ELSE 分支逻辑）| 🔲 |
| B7-4 HTML 骨架生成 | 按 Layout Patterns 生成页面骨架 | 🔲 |
| B7-5 组件实例填充 | 将匹配到的【待定】组件库组件填入骨架 | 🔲 |
| B7-6 Token 绑定 | 将 Mode D 语义色 → 实际 CSS 变量替换 | 🔲 |
| B7-7 交互逻辑注入 | 状态机 JS 绑定到 HTML 组件事件 | 🔲 |
| B7-8 Edge Case 分支注入 | 异常分支（不足/禁用/空状态）对应组件状态自动切换 | 🔲 |
| B7-9 原型预览输出 | 生成单文件 `prototype-[系统名称].html`，浏览器直接打开 | 🔲 |

**验收**：输入任意一套 A+B+D 数据，5 分钟内生成可点击的 HTML 原型，覆盖主流程 + 至少 2 个 Edge Case

---

## 五、文件结构规划

```
f:\codemake\
  ├── PROTOTYPE_GENERATOR_DEV_PLAN.md        ← 本文件（唯一开发记录）
  │
  ├── design-system/
  │   ├── raw-components.json                ← Batch 1 产出（爬取原始数据）
  │   ├── component-registry.json            ← Batch 2 产出（含语义映射）
  │   ├── token-map.json                     ← Batch 3 产出
  │   ├── layout-patterns.json               ← Batch 4 产出（含 HTML 模板片段）
  │   ├── interaction-rules.json             ← Batch 5 产出
  │   └── design-system-profile.json         ← Batch 6 整合产出（最终 DSP）
  │
  ├── prototype-generator/
  │   ├── parser.js                          ← Mode D 输出解析器
  │   ├── component-matcher.js               ← 语义 → 组件匹配引擎
  │   ├── state-machine.js                   ← steps[] → JS 状态机生成
  │   ├── layout-builder.js                  ← HTML 骨架构建
  │   └── generator.js                       ← 主入口，整合所有模块
  │
  └── output/
      └── prototype-[系统名称]-[日期].html   ← 生成的可交互原型
```

---

## 六、质量验收标准

| 维度 | 目标指标 |
|---|---|
| **组件覆盖率** | DSP 覆盖【待定】组件库全部组件 |
| **语义命中率** | Mode D 输出 → 组件名匹配准确率 ≥ 85% |
| **逻辑完整性** | 生成原型覆盖所有 Happy Path + Edge Case 分支 |
| **Token 绑定** | 原型中所有颜色/间距引用 CSS 变量，无硬编码值 |
| **生成效率** | A→B→D→原型完整链路耗时 ≤ 30 分钟（含人工确认） |
| **可维护性** | DSP 更新后，重新生成原型无需修改生成引擎代码 |

---

## 七、依赖与前置条件

| 依赖项 | 说明 | 状态 |
|---|---|---|
| Mode A Prompt | `MODE_A_PROMPT.md` | ✅ 已有 |
| Mode B Prompt | `MODE_B_PROMPT.md` | ✅ 已有 |
| Mode D Prompt | 已在对话中定义 | ✅ 已有 |
| 目标组件库文档站 | ❓ 待确认（见第九节 Q0） | ⏳ 待确认 |
| Yike Design（技术可行性验证用） | https://yike.design/module/ | ✅ 可访问 |
| Mindmap 编辑器原型 | `mindmap-prototype.html` | ✅ 已有（Mode A/B 数据源）|

---

## 八、开发日志

> 本章节用于追加记录每个 Batch 的开发过程、QA 问题、修订记录。

### 2026-04-10

- 完成整体架构设计与开发计划文档初稿
- 组件库选型尚未确认，候选项包含 Yike Design 等，待 Q0 决策后锁定
- 已验证 Yike Design 网站可访问，初步爬取 Button 组件 API 作为技术可行性验证（非最终确认）

---

## 九、待决策问题

| # | 问题 | 选项 | 状态 |
|---|---|---|---|
| **Q0** | **🔴 组件库选型？（B1~B6 的前置依赖）** | Yike Design / 其他指定库 / 自研 | ❓ **待确认（阻塞）** |
| Q1 | 原型输出格式优先级？ | HTML 单文件 / Vue 组件 / 两者都要 | ❓ 待确认 |
| Q2 | Mode D 输入方式？ | 粘贴 Markdown / JSON 文件 / API 调用 | ❓ 待确认 |
| Q3 | 原型中组件引入方式？ | CDN 引入完整库 / npm 本地 / 仅用样式变量 | ❓ 待确认（依赖 Q0）|
| Q4 | DSP 更新机制？ | 手动维护 / 定期自动爬取更新 | ❓ 待确认 |
