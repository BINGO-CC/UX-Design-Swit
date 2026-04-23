# UX 设计交互编辑器 — 项目续接文档

> **文档版本**：v5.0.0（2026-04-23）
> **用途**：在新对话中快速恢复项目上下文，确保迭代连续性
> ⚠️ **视觉规范**：所有 UI 新增/修改必须遵守 `UI_REDESIGN.md`（Notion Dark 设计系统 v1.3.0）

---

## 〇、快速恢复上下文

### 📂 核心文件清单

| 文件 | 说明 | 备注 |
|------|------|------|
| `ux-design-editor.html` | **主文件** — 单文件 Mindmap 编辑器（8200+ 行） | HTML + CSS + Vanilla JS，无第三方依赖 |
| `index.html` | 入口页 — 重定向到 `ux-design-editor.html` | GitHub Pages 入口 |
| `PROJECT_RESUME.md` | 项目续接文档（本文件） | 新对话必读 |
| `.codemaker/skills/ux-design.md` | Skill 指令文件 — AI 四模式执行规范 | 随版本同步维护 |
| `ux-design-editor.bak.html` | 旧版 v4.3.0 卡片编辑器备份 | 仅归档，不再维护 |

### 🚀 部署信息

| 项目 | 值 |
|------|-----|
| 托管平台 | GitHub Pages |
| 部署分支 | `main` |
| 部署方式 | push 即自动部署 |
| 入口文件 | `index.html` → `ux-design-editor.html` |
| 线上 URL | https://bingo-cc.github.io/UX-Design-Swit/ |

### 💬 新对话启动指令

```
请阅读以下文件恢复项目上下文：
1. PROJECT_RESUME.md — 项目架构、数据模型、版本历史
2. ux-design-editor.html — 主文件源码
3. .codemaker/skills/ux-design.md — Skill 执行规范

本次需要开发的内容是：[在此描述]
```

---

## 一、整体架构决策

### 1.1 三模式核心架构原则

> 这是整个项目最重要的开发约束，所有实现决策必须以此为基准：

**模式总览**：
- **Mode A**（策划案分析）：信息架构层级拆解，Stage → Module → Feature → childModule 树状结构
- **Mode B**（行为路径）：用户行为流程建模，Goal Loop → Steps 步骤序列 → 连线流转
- **Mode C**（交互稿）：Spec Card 交互规格定义，可见层 / 交互层 / 边界层

**原则一：共享代码只写一次**
Mode A 和 Mode B 共用**同一套**画布渲染、卡片组件、Stage TAB、布局算法、连线基础样式、tooltip 系统。这些共享代码统一维护在一处，任何修改自动对两个模式生效，**禁止为 Mode B 复制任何已有函数**。

**原则一补充（2026-04-09）：`viewMode` 分流边界强制约束**

> `state.viewMode` 判断**只允许出现在以下两处**，违反此规则视为架构错误：
> 1. `render()` 函数中 — 用于分流「左侧面板」（`renderStageTabs` vs `renderBSidePanel`）及控制连线层显隐
> 2. `renderCanvas()` 末帧回调中 — 用于决定是否触发行为路径叠加层（`renderBLines` / `renderBLinesOverview`）

> **连线层显示规则**：
> - `#mm-lines`（结构连线 / childModule）：**仅 Mode A 显示**
> - `#mm-b-lines`（行为路径叠加层）：**仅 Mode B 显示**
> - 两层 SVG 互斥：Mode B 画布不展示任何结构连线，连线内容完全由 Loop 数据驱动
>
> `renderCanvas()` / `renderCard()` / `renderFeatureWrap()` 内部**严禁出现 `viewMode` 判断**，唯一例外如下：
>
> **合法例外 — 连线触发按钮（2026-04-09）**：
>
> `mm-feature-connect`（`>` 按钮）显示规则：
> - **Mode A**：未连线 + 非 L3 列 → 显示，点击调用 `enterConnectMode()` 写入 `childModule`
> - **Mode B + 无 Loop 选中（Stage TAB）**：不渲染 → 无依附对象，连线无意义
> - **Mode B + 有 Loop 选中（Loop TAB）**：显示，点击调用 `enterBConnectMode()`，连线写入该 Loop 的 `steps[]`

**原则二：Mode B 只开发自己专属的部分**
```
Mode B 专属范围（仅此而已）：
  ├── 数据层       mockDataB（Goal Loops 结构）
  ├── 左侧面板     Stage 下的 Loop 二级列表
  ├── 连线逻辑     renderBLines()（数据源不同，调用共享 helper）
  └── 连线样式     .b-happy / .b-edge / .line-path--layer-jump（轻度色调区分）
```

**原则三：`renderBLines()` 是 `renderLines()` 的数据源扩展**
两者调用**同一套共享 helper 函数**（贝塞尔路径计算、SVG 元素创建、事件绑定），差异仅在连线的来源：
- `renderLines()`  → 遍历 `feature.childModule` 父子关系
- `renderBLines()` → 遍历 `loop.steps[]` action 步骤序列

---

### 1.2 文件结构

```
ux-design-editor.html              ← 主文件，A+B+C 三模式合体
  ├── <style>                       ← 内联 CSS，深色主题（Design Tokens 系统）
  ├── <div#app>                     ← 应用根节点
  │   ├── .mm-header                ← 顶栏：[策划案分析 A] [行为路径 B] [交互稿 C] + 撤销/重做/导入导出
  │   ├── .mm-stage-col             ← 左侧面板（Mode A: Stage TAB / Mode B: Stage+Loop 二级列表）
  │   └── .mm-canvas                ← 主画布（A/B 共用，横向滚动容器）
  │       ├── .mm-layer-col × 5     ← L1 / L1.5 / L2 / L2.5 / L3 列
  │       ├── svg#mm-lines          ← Mode A 结构连线层（childModule 关系）
  │       └── svg#mm-b-lines        ← Mode B 行为连线层（steps[] 流转序列）
  └── <script>
      ├── ── 共享层（A/B 共用）──────────────────────────────
      ├── mockData                  ← Mode A 数据（stages[] 结构）
      ├── state                     ← 运行时状态（含 viewMode / selectedLoopId）
      ├── render()                  ← 全量重渲染入口（按 viewMode 分流）
      ├── renderStageTabs()         ← Stage TAB 渲染（A/B 共用）
      ├── renderCanvas()            ← 卡片画布渲染（A/B 共用）
      ├── renderLines()             ← Mode A 结构连线
      ├── save() / undo() / redo()  ← 历史栈系统（80 步）
      ├── ── Mode B 专属层 ──────────────────────────────────
      ├── mockDataB                 ← Mode B 数据（Goal Loops 结构）
      ├── renderBSidePanel()        ← 左侧 Loop 二级列表
      ├── renderBLines()            ← Mode B 行为连线
      ├── ── Mode C 专属层 ──────────────────────────────────
      └── storeC                    ← Mode C 数据（Spec Cards 结构）
```

### 1.3 渲染策略

- **数据驱动重渲染**：每次数据变更后调用 `render()` 全量重绘卡片，`renderLines()` 重绘连线
- **SVG 连线层**：独立 `<svg>` 覆盖在画布上，`pointer-events: none`（线本身可 click 除外）
- **不引入第三方库**：纯 HTML + CSS + Vanilla JS

### 1.4 数据模型

#### Mode A（策划案分析）
```javascript
const mockData = {
  activeStageId: "s001",
  stages: [
    {
      id: "s001",
      label: "A.行为阶段",
      modules: [
        {
          id: "m001",
          name: "功能模块名称",
          layer: "L1",
          features: [
            {
              id: "f001",
              text: "功能点名称",
              layer: "L1",
              priority: "High",
              isUXSupplement: false,
              supplementReason: "",
              l3Reason: "",
              childModule: null    // 或 { id, name, targetLayer, features[] }
            }
          ]
        }
      ]
    }
  ]
}
```

#### Mode B（行为路径）
```javascript
const mockDataB = {
  "s001": {
    loops: [
      {
        id: "loop001",
        name: "Goal Loop 名称",
        supplements: [],           // 幽灵补全节点声明
        _supplementsReason: "",    // 补全理由
        steps: [
          {
            kind: "validation",
            children: [
              { kind: "action", text: "操作步骤", refFeature: "f001",
                feedbacks: [{ kind: "feedback", text: "反馈", feedbackType: "toast" }]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

#### Mode C（交互稿）
```javascript
const storeC = [
  {
    id: "spec001",
    title: "Spec Card 标题",
    visible: [],      // 可见层条目
    interact: [],      // 交互层条目
    boundary: []       // 边界层条目
  }
]
```

#### LocalStorage 持久化格式
```javascript
// key: 'mm-editor-data'
{
  A: { activeStageId, stages },
  B: mockDataB,
  C: storeC
}
```

---

## 二、UI 组件规格

### 2.1 顶栏（`mm-header`）

```
[UX Editor] [←] [→]  |  策划案分析(active) / 行为路径 / 交互稿  |  ●已保存  导入 导出▾ 分享 清除数据
```

### 2.2 左侧 Stage TAB（`.mm-stage-col`）

| 元素 | 说明 |
|---|---|
| TAB 列表 | 从 `stages[]` 渲染，每项显示 `stage.label` |
| 激活态 | 选中项背景高亮（白色背景 + 深色文字） |
| 非激活态 | 暗色背景，文字低透明度 |
| 点击切换 | 更新 `activeStageId`，重渲染主画布 |

### 2.3 Layer 列（`mm-layer-col`）

共 5 列，固定宽度，横向滚动。

**层级 Tooltip 文案**：
```
L1   → 系统第一级独立页面，主承载面板。关闭后回到 HUD。
L1.5 → 依附于 L1 的覆盖层（浮层/侧边栏）。关闭后回到 L1。
L2   → 从 L1 某功能点进入的第二级页面。关闭后回到 L1。
L2.5 → 依附于 L2 的覆盖层。关闭后回到 L2。
L3   → 从 L2 进入的第三级页面。严格控制，必须附理由。
```

### 2.4 模块卡片（`.mm-card`）

| 元素 | 交互 |
|---|---|
| 模块名称文字 | 点击进入内联编辑 |
| `+` 按钮 | 在功能点列表末尾新增空功能节点，进入编辑态 |
| `×` 按钮（红色） | 删除当前卡片（含其所有出向连线 + 级联删除所有子孙卡片） |

### 2.5 功能节点（`.mm-feature`）

- **优先级**：排序顺序隐式体现（靠上=High，靠下=Low），UI 层不显示点
- **UX补全图标 `✦`**：`isUXSupplement: true` 时显示，hover 显示 `supplementReason` tooltip
- **悬浮态**：左侧 `×`（删除）、右侧 `>`（创建子模块）
- **编辑态**：点击文字进入内联编辑，Enter/Escape 确认/取消
- **已连接态**：右侧 `→` 常态显示（黄绿色实心）

---

## 三、连线系统规格

### 3.1 路由规则

```
P1 = 功能节点右侧中心 (x = 父卡片右边缘 + 4px, y = 节点中心)
P2 = (列分割线 x 坐标, P1.y)
P3 = (列分割线 x 坐标, 目标卡片标题中心.y)
P4 = 目标卡片标题左侧中心
```

SVG path：`M P1 L P2 L P3 L P4`（折线，直角转折）

### 3.2 连线视觉

| 状态 | 样式 |
|---|---|
| 默认 | stroke: `#CCFF00`，opacity: 40%，stroke-width: 1.5 |
| Hover | opacity: 100% |

---

## 四、已实现功能清单

### 核心功能

| 功能 | 说明 |
|------|------|
| 三模式切换 | A 策划案分析 / B 行为路径 / C 交互稿，Header TAB 切换 |
| 画布渲染 | 5 层横向画布（L1~L3），卡片数据驱动全量重渲染 |
| SVG 连线 | Mode A 结构连线 + Mode B 行为连线，共享 helper 架构 |
| 撤销/重做 | 80 步历史栈，Ctrl+Z / Ctrl+Y 快捷键 |
| LocalStorage 持久化 | 自动保存，含 v4.x 旧数据自动清除迁移 |
| 导入系统 | JSON 导入 → 注释过滤 → 格式兼容 → 覆盖/合并模式选择 |
| 导出系统 | 复制为 Prompt / 导出 Markdown |
| 分享功能 | 生成分享链接 |
| CRUD 全套 | 卡片/功能点/模块的增删改查 + 拖拽排序 |
| Mode B 行为路径 | Goal Loop 管理、Steps 面板、幽灵补全节点、行为连线 |
| Mode C 交互稿 | Spec Card 编辑（可见层/交互层/边界层） |

### 导入流程（五步）

```
AI 输出 → stripJsonComments → JSON.parse → normalizeBData → migrateSteps → applyImportedData
```

---

## 五、版本发布记录

### v5.0.0（2026-04-23）— Mindmap 编辑器架构重构上线

- 旧版 v4.3.0 卡片编辑器完全替换为 Mindmap 画布编辑器
- 三模式架构（A 策划案分析 / B 行为路径 / C 交互稿）
- 5 层横向画布 + SVG 连线系统
- 撤销/重做（80 步历史栈）
- 合并导入 + Skill 分段输出规范
- 旧版 LocalStorage 数据自动清除迁移
- 文档合并：`MINDMAP_EDITOR_DEV_PLAN.md` → `PROJECT_RESUME.md`

### v5.0.0 开发会话记录

#### 会话一（2026-04-22）：2.0 接管 + 七项核心功能

1. `mindmap-prototype.html` 正式替换为 `ux-design-editor.html`（2.0 接管主文件名）
2. Mode C 交互稿新增完整复制系统（5 个粒度的富文本复制）
3. 导入系统增强（自动剥离 Markdown 代码块 + B 格式数组→对象兼容转换）
4. Skill 文件与编辑器数据结构完全对齐
5. Mode A 连线缩放偏移 Bug 修复（解析法替代 getBoundingClientRect）
6. 撤销/重做系统（80步历史栈 + Ctrl+Z/Y 快捷键 + Header 按钮）
7. 一系列 UI 细节修复（弹窗宽度/颜色/Toast 层级等）

#### 会话二（2026-04-22）：合并导入 + Skill 分段输出规范

- 导入流程升级为三步走（检测 → 模式选择弹窗 → 执行）
- 新增核心函数：`hasExistingData()` / `normalizeImportData()` / `detectImportContent()` / `applyMergeData()`
- 合并逻辑：A 非空覆盖 / B 按 Stage ID 合并 / C 按 spec ID 去重追加
- Skill 分段输出规范（Stage ≥ 3 或 Loop ≥ 8 自动分段）

#### 会话三（2026-04-22）：B 模式行为路径全面修复

- `buildBLineEdges()` 完整重写（深度优先遍历）
- `renderBLines()` 执行顺序重构
- `renderSupplementGhosts()` 完整重写（纯 DOM 注入）
- Mode B 下 UX 补充标识（✦）完全隐藏
- Skill Step 4.1 强制流转补全扫描规范

#### 会话四（2026-04-22）：B 模式架构对齐 + Skill JSON 结构迁移

- 根因诊断：字段名不一致（`elseLoopId` vs `targetLoopId`）、数据结构不一致（`children` vs `feedbacks`）
- `buildBLineEdges` 还原 walkGroup 分组算法
- `renderSupplementGhosts` 还原持久化写入方案
- Skill + MODE_B_PROMPT 规范迁移至 `action.feedbacks[]` + `targetLoopId`
- 模式 D 接力点系统完整移除

#### 会话五（2026-04-23）：Skill-编辑器兼容性全面对齐

- 6 项 Skill ↔ 编辑器 JSON 不匹配系统性修复
- 新增导入预处理函数：`stripJsonComments` / `normalizeBData` / `migrateSteps`
- 撤销/重做功能完整落地
- UI 修复（Tab 可读性、交互稿面板标题、导出菜单精简）

---

## 六、待办事项

- [ ] 合并导入弹窗「B 模式冲突」二级选项联动隐藏待验证
- [ ] Mode C 分段输出规范待补充
- [ ] `role` 字段可视化（画布展示）未实现，如有需求可后续添加
- [ ] 幽灵节点「一键接受补全」功能（当前需手动切 Mode A 补录）