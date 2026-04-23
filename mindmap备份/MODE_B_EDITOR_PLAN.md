# 模式 B 编辑器呈现效果开发计划

> **文档版本**：v2.0（2026-04-08）
> **基准文件**：`mindmap-prototype.html`（模式 A 编辑器现有实现）
> **关联文档**：`MODE_B_PROMPT.md`（v3.0 行为路径提取 Prompt）
> **开发目标**：在现有 Mode A 编辑器基础上，增量实现模式 B「行为路径」视图，不破坏 Mode A 已有功能
> **集成策略**：在 `mindmap-prototype.html` 上直接增量开发 A+B 合体原型，验证完毕后整体集成入 `ux-design-editor.html`

---

## 一、产品定义

### 1.1 模式 B 是什么

模式 B 是与模式 A **并列的独立视图**。它完全复用 Mode A 的画布结构（Stage × Layer 多列卡片布局），所有卡片和功能节点的位置与 Mode A 完全一致，**差异仅在连线层**：

- **Mode A 连线**（`#mm-lines`）：结构连线，基于 `childModule` 父子关系绘制，随 Mode A 激活显示
- **Mode B 连线**（`#mm-b-lines`）：行为连线，基于 Goal Loop 的 `steps[]` 流转顺序绘制有向箭头连线，随 Mode B 激活显示

两套连线层**互斥切换**，切换 Tab 时对应层显示/隐藏。Mode B 下画布完全只读，不可编辑。

### 1.2 核心交互模型

```
顶层 Tab                        右侧画布（A / B 共用 L1～L3 列布局）
────────────────────────────────────────────────────────────────────
[策划案分析 A] [行为路径 B]

Mode A 激活：
  左侧 Stage TAB（可编辑）      #mm-lines 显示（结构连线）
                                #mm-b-lines 隐藏

Mode B 激活：
  左侧 Stage TAB ▼              #mm-lines 隐藏
    🟢 选定研究配方  ←选中──→   #mm-b-lines 显示 Loop 行为连线（有向箭头）
    🔴 材料不足挽回              无关卡片压暗至 0.15
    🔴 列表为空降级              isAnchor 节点显示 🔗 徽章
  Stage B.执行阶段 ▶            [✨流转补全] 幽灵节点虚线叠加
────────────────────────────────────────────────────────────────────
```

### 1.3 与现有代码的关系

| 现有能力 | Mode B 复用方式 |
|---|---|
| `renderCanvas()` 卡片渲染 | 完全复用，Mode B 下加只读保护 guard |
| `renderStageTabs()` 左侧阶段列表 | 复用结构，Mode B 在 Stage 行下追加 Loop 二级列表 |
| `state.activeStageId` 驱动画布 | 保持不变，Mode B 切换 Stage 时同样驱动画布渲染 |
| `.mm-card.dimmed { opacity: 0.15 }` | 直接复用，无关卡片压暗 |
| `.mm-preview-card` 虚线样式 | 参考样式，实现幽灵补全节点 |
| `attachTip()` tooltip 函数 | 直接复用，幽灵节点和锚点徽章的悬浮提示 |
| `#mm-lines` SVG 连线层 | Mode B 激活时隐藏，**不操作其内容** |
| **`#mm-b-lines`（新增）** | Mode B 专属 SVG 层，按 steps[] 顺序绘制有向行为连线 |

---

## 二、整体架构

```
现有代码基座
  ├── mockData            Mode A 功能节点数据
  ├── state               视图状态对象
  ├── render()            主渲染入口
  ├── renderStageTabs()   左侧阶段列表
  ├── renderCanvas()      右侧画布（列 + 卡片 + 连线）
  └── renderLines()       SVG 连线绘制

新增模块（Mode B 专属）
  ├── mockDataB              Goal Loops 数据层                    ← Phase 1
  ├── state.viewMode         全局视图模式标识（'A' | 'B'）         ← Phase 2
  ├── state.selectedLoopId   当前选中闭环 ID                      ← Phase 2
  ├── renderHeaderTabs()     Tab 激活态同步                       ← Phase 2
  ├── renderBSidePanel()     左侧 Stage → Loops 二级面板          ← Phase 3
  ├── #mm-b-lines            Mode B 专属 SVG 行为连线层（HTML新增）← Phase 4
  ├── flattenActionSteps()   steps[] 扁平化，提取有序 action 序列  ← Phase 4
  ├── getFeatureConnectPoints() feature 节点画布坐标获取           ← Phase 4
  ├── drawBezierArrow()      有向贝塞尔折角箭头绘制               ← Phase 4
  ├── ensureArrowMarkers()   arrowhead SVG marker 初始化          ← Phase 4
  ├── renderBLines(loopId)   行为连线主渲染入口                   ← Phase 4
  ├── clearBLines()          行为连线 + 卡片压暗清除              ← Phase 4
  ├── renderAnchorBadges()   锚点徽章注入                         ← Phase 5
  └── renderSupplementGhosts() 补全幽灵节点                       ← Phase 5
      （Phase 6）renderBStepList() 步骤展开 + 单节点聚焦
```

---

## 三、数据结构定义

### 3.1 mockDataB 顶层结构

```js
const mockDataB = {
  loops: [ /* GoalLoop[] */ ]
};
```

### 3.2 GoalLoop 对象

```js
{
  id:              "n2001",           // 唯一 ID，从 n2001 起始递增
  title:           "选定研究配方的主干流程",
  type:            "happy_path",      // "happy_path" | "edge_case"
  refStage:        "s001",            // 对应 mockData.stages[].id
  startPoint:      "玩家在 L1 科技台主面板滑动浏览配方列表",
  endPoint:        "配方已选定，开始研究按钮高亮",
  coveredFeatures: ["f001", "f002", "f003", "f004", "f005"],
  steps:           [ /* Step[] */ ],  // Phase 6 使用
  supplements:     [ /* Supplement[] */ ]
}
```

### 3.3 Step 对象（Phase 6 使用，Phase 1 建立骨架即可）

```js
{
  id:         "n2001_s1",
  kind:       "validation",     // "validation" | "action" | "feedback"
  condition:  "IF: 存在可研究配方",   // 仅 validation 类型有此字段
  refFeature: "f001",           // 对应 mockData feature ID，action 类型才有
  isAnchor:   false,            // true = 此节点为模式 D 接力触发点
  children:   [ /* Step[] */ ] // 嵌套子步骤
}
```

### 3.4 Supplement 对象（幽灵补全节点）

```js
{
  id:             "ns001",
  text:           "查看解锁条件",
  targetLayer:    "L1.5",
  refNearFeature: "f001",    // 幽灵节点插入在哪个 feature 所在卡片的末尾
  reason:         "空状态无出路，最低限度导航补全"
}
```

### 3.5 完整 mockDataB 示例（覆盖 s001 准备阶段）

```js
const mockDataB = {
  loops: [
    // ── s001 A.准备阶段 ──────────────────────────────────────
    {
      id: "n2001", title: "选定研究配方的主干流程",
      type: "happy_path", refStage: "s001",
      startPoint: "玩家在 L1 科技台主面板滑动浏览配方列表",
      endPoint: "配方已选定，开始研究按钮高亮",
      coveredFeatures: ["f001", "f002", "f003", "f004", "f005", "f008"],
      steps: [
        {
          id: "n2001_s1", kind: "validation",
          condition: "IF: 存在可研究配方", refFeature: null, isAnchor: false,
          children: [
            { id: "n2001_s2", kind: "action",   refFeature: "f001", isAnchor: false, children: [] },
            { id: "n2001_s3", kind: "feedback",  refFeature: null,   isAnchor: false, children: [] },
            { id: "n2001_s4", kind: "action",   refFeature: "f002", isAnchor: false, children: [] },
            { id: "n2001_s5", kind: "feedback",  refFeature: null,   isAnchor: true,  children: [] }
          ]
        },
        {
          id: "n2001_s6", kind: "validation",
          condition: "IF: 全部材料充足", refFeature: null, isAnchor: false,
          children: [
            { id: "n2001_s7", kind: "action",   refFeature: "f005", isAnchor: false, children: [] },
            { id: "n2001_s8", kind: "feedback",  refFeature: null,   isAnchor: false, children: [] }
          ]
        }
      ],
      supplements: []
    },
    {
      id: "n2002", title: "材料不足时的异常挽回",
      type: "edge_case", refStage: "s001",
      startPoint: "玩家在 L1.5 配方详情弹窗查阅材料需求清单",
      endPoint: "L2 材料获取途径面板开启",
      coveredFeatures: ["f004", "f005", "f006", "f007"],
      steps: [
        {
          id: "n2002_s1", kind: "validation",
          condition: "ELSE IF: 存在材料不足项", refFeature: null, isAnchor: false,
          children: [
            { id: "n2002_s2", kind: "action",  refFeature: null,   isAnchor: false, children: [] },
            { id: "n2002_s3", kind: "feedback", refFeature: null,   isAnchor: false, children: [] },
            { id: "n2002_s4", kind: "action",  refFeature: "f007", isAnchor: false, children: [] },
            { id: "n2002_s5", kind: "feedback", refFeature: null,   isAnchor: true,  children: [] }
          ]
        }
      ],
      supplements: [
        {
          id: "ns001", text: "材料获取跳转入口",
          targetLayer: "L1.5", refNearFeature: "f004",
          reason: "弹窗内缺口信息呈现后若无跳转路径，玩家被迫关闭弹窗自行查找，形成死胡同"
        }
      ]
    },
    {
      id: "n2003", title: "配方列表为空时的降级处理",
      type: "edge_case", refStage: "s001",
      startPoint: "玩家在 L1 科技台主面板打开配方列表",
      endPoint: "L1.5 解锁条件说明弹窗开启",
      coveredFeatures: ["f001"],
      steps: [
        {
          id: "n2003_s1", kind: "validation",
          condition: "ELSE IF: 无可研究配方", refFeature: null, isAnchor: false,
          children: [
            { id: "n2003_s2", kind: "action",  refFeature: "f001", isAnchor: false, children: [] },
            { id: "n2003_s3", kind: "feedback", refFeature: null,   isAnchor: false, children: [] }
          ]
        }
      ],
      supplements: [
        {
          id: "ns002", text: "查看解锁条件",
          targetLayer: "L1.5", refNearFeature: "f001",
          reason: "空状态无任何出路将导致玩家无从操作，提供解锁路径是最低限度导航补全"
        }
      ]
    },

    // ── s002 B.执行阶段 ──────────────────────────────────────
    {
      id: "n2010", title: "启动研究的主干流程",
      type: "happy_path", refStage: "s002",
      startPoint: "玩家在 L1 主面板点击开始研究",
      endPoint: "倒计时开始，进度条激活",
      coveredFeatures: ["f012"],
      steps: [], supplements: []
    },
    {
      id: "n2011", title: "使用加速道具加速研究",
      type: "happy_path", refStage: "s002",
      startPoint: "玩家在 L1 倒计时面板点击加速入口",
      endPoint: "加速完成，倒计时缩短",
      coveredFeatures: ["f012", "f013", "f014", "f015"],
      steps: [], supplements: []
    },
    {
      id: "n2012", title: "取消研究的防呆确认",
      type: "edge_case", refStage: "s002",
      startPoint: "玩家在 L1 倒计时面板点击取消研究",
      endPoint: "研究已取消，资源部分返还",
      coveredFeatures: ["f016"],
      steps: [], supplements: []
    }
  ]
};
```

---

## 四、开发阶段详细说明

### Phase 1 — 数据层扩展

**目标**：建立 `mockDataB` 数据结构，作为所有视图逻辑的数据源。

**交付物**：
- `mockDataB` 对象完整声明（参照第三节示例）
- 覆盖 `s001` 准备阶段 3 条 loops、`s002` 执行阶段 3 条 loops

**工具函数（新增）**：

```js
// 根据 stageId 获取该 Stage 的所有 loops
function getLoopsByStage(stageId) {
  return mockDataB.loops.filter(l => l.refStage === stageId);
}

// 根据 loopId 获取 loop 对象
function getLoopById(loopId) {
  return mockDataB.loops.find(l => l.id === loopId) || null;
}

// 递归收集 steps 中 isAnchor=true 的 refFeature IDs
function collectAnchorFeatureIds(loop) {
  const anchors = new Set();
  function walk(steps) {
    for (const s of (steps || [])) {
      if (s.isAnchor && s.refFeature) anchors.add(s.refFeature);
      if (s.children) walk(s.children);
    }
  }
  walk(loop.steps);
  return anchors;
}
```

**验收标准**：
- `getLoopsByStage('s001').length === 3`
- `getLoopsByStage('s002').length === 3`
- `getLoopById('n2001').coveredFeatures.length > 0`

---

### Phase 2 — 视图模式状态与 Tab 切换

**目标**：让顶部三个 Tab 实际工作，驱动全局视图在 Mode A / B / D 间切换，主 `render()` 函数分流。

**State 扩展**：

```js
const state = {
  // ── 所有现有字段保持不变 ──

  // ── 新增 ──
  viewMode:       'A',    // 'A' | 'B' | 'D'
  selectedLoopId: null,   // Mode B 当前选中的 Goal Loop ID
  expandedStageIds: new Set(['s001'])  // Mode B 左侧面板展开的 Stage ID 集合
};
```

**顶部 HTML 结构**（两个 Tab 按钮，替换现有三 Tab 结构）：

```html
<!-- 顶部 Tab 栏，仅保留 A / B 两个 Tab -->
<button class="mm-header-tab" data-mode="A">策划案分析</button>
<button class="mm-header-tab" data-mode="B">行为路径</button>
```

**新增 `renderHeaderTabs()` 函数**：

```js
function renderHeaderTabs() {
  document.querySelectorAll('.mm-header-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mode === state.viewMode);
  });
}
```

**Tab 事件绑定**（在初始化阶段执行一次）：

```js
function initTabEvents() {
  document.querySelectorAll('.mm-header-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      state.viewMode = btn.dataset.mode;
      state.selectedLoopId = null;
      // 切换 viewMode 时重置 B 面板展开状态
      state.expandedStageIds = new Set([state.activeStageId]);
      render();
    });
  });
}
```

**`render()` 函数改造**：

```js
function render() {
  renderHeaderTabs();                          // 新增：同步 Tab 高亮

  // 连线层互斥切换
  const mmLines  = document.getElementById('mm-lines');
  const mmBLines = document.getElementById('mm-b-lines');
  if (mmLines)  mmLines.style.display  = state.viewMode === 'A' ? '' : 'none';
  if (mmBLines) mmBLines.style.display = state.viewMode === 'B' ? '' : 'none';

  if (state.viewMode === 'A') {
    renderStageTabs();                         // 现有，不改
    renderCanvas();                            // 现有，不改
  } else if (state.viewMode === 'B') {
    renderBSidePanel();                        // Phase 3 新增
    renderCanvas();                            // 复用，画布结构不变
    // renderBLines 在 renderCanvas 末帧回调中调用（见 Phase 4）
  }

  if (typeof _notifyDataChange === 'function') _notifyDataChange();
}
```

**Mode B 只读保护**（在 `renderCard` 和 `renderFeatureWrap` 内部 guard）：

```js
// renderCard() 中，卡片操作按钮区域：
if (state.viewMode !== 'B') {
  // 渲染 add/del 按钮、绑定双击编辑事件
}

// renderFeatureWrap() 中：
if (state.viewMode !== 'B') {
  wrap.draggable = true;
  // 绑定 dblclick 编辑事件
  // 绑定 priority 切换事件
}
```

**验收标准**：
- 点击三个 Tab 能切换，`state.viewMode` 正确更新
- Mode B 下画布卡片不显示 add/del 按钮，功能节点不可编辑
- Mode A 功能完全不受影响

---

### Phase 3 — Mode B 左侧面板

**目标**：Mode B 下左侧面板替换为「Stage → Goal Loops」两级折叠列表，点击 Stage 展开/折叠，点击 Loop 触发高亮。

**新增 `renderBSidePanel()` 函数**：

```js
function renderBSidePanel() {
  const el = document.getElementById('stageList');
  el.innerHTML = '';

  // 顶部标题（替换「阶段管理」按钮，Mode B 下不需要编辑入口）
  const mainBtn = document.getElementById('stageAddBtn');
  mainBtn.className = 'mm-stage-add';
  mainBtn.innerHTML = `
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <circle cx="6" cy="6" r="4" stroke="currentColor" stroke-width="1.3"/>
      <path d="M6 4V8M4 6H8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
    </svg>
    行为路径`;
  mainBtn.onclick = null; // Mode B 下无点击行为

  for (const stage of mockData.stages) {
    const loops = getLoopsByStage(stage.id);
    const isExpanded = state.expandedStageIds.has(stage.id);

    // ── Stage 行 ──
    const stageItem = document.createElement('div');
    stageItem.className = 'mm-b-stage-item' +
      (stage.id === state.activeStageId ? ' active' : '');
    stageItem.innerHTML = `
      <span class="mm-b-stage-arrow">${isExpanded ? '▼' : '▶'}</span>
      <span class="mm-b-stage-label">${stage.label}</span>
      ${loops.length > 0
        ? `<span class="mm-b-loop-count">${loops.length}</span>`
        : '<span class="mm-b-loop-empty">—</span>'}
    `;
    stageItem.addEventListener('click', () => {
      state.activeStageId = stage.id;
      state.selectedLoopId = null;
      if (isExpanded) state.expandedStageIds.delete(stage.id);
      else            state.expandedStageIds.add(stage.id);
      render();
    });
    el.appendChild(stageItem);

    // ── Loop 列表（展开时渲染）──
    if (isExpanded && loops.length > 0) {
      const loopList = document.createElement('div');
      loopList.className = 'mm-b-loop-list';

      for (const loop of loops) {
        const loopItem = document.createElement('div');
        loopItem.className = 'mm-b-loop-item' +
          (loop.id === state.selectedLoopId ? ' active' : '');
        loopItem.dataset.loopId = loop.id;
        loopItem.innerHTML = `
          <span class="mm-b-loop-dot ${loop.type === 'happy_path' ? 'happy' : 'edge'}"></span>
          <span class="mm-b-loop-title">${loop.title}</span>
        `;
        loopItem.addEventListener('click', (e) => {
          e.stopPropagation();
          state.selectedLoopId =
            state.selectedLoopId === loop.id ? null : loop.id; // 点击已选中则取消
          // 仅更新高亮，不重渲整个画布
          applyLoopHighlight(state.selectedLoopId);
          // 同步 Loop 行 active 状态
          document.querySelectorAll('.mm-b-loop-item')
            .forEach(el => el.classList.toggle('active', el.dataset.loopId === state.selectedLoopId));
        });
        loopList.appendChild(loopItem);
      }
      el.appendChild(loopList);
    }

    // ── 无 loops 时的空状态 ──
    if (isExpanded && loops.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'mm-b-loop-empty-state';
      empty.textContent = '暂无行为路径';
      el.appendChild(empty);
    }
  }
}
```

**新增 CSS**：

```css
/* ── Mode B 左侧面板 ── */
.mm-b-stage-item {
  display: flex; align-items: center; gap: 7px;
  padding: 7px 12px; cursor: pointer; user-select: none;
  font-size: 12px; color: #666666;
  transition: color 120ms ease, background 120ms ease;
  border-radius: 6px; margin: 0 4px;
}
.mm-b-stage-item:hover { color: #EBEBEB; background: #1e1e1e; }
.mm-b-stage-item.active { color: #EBEBEB; }

.mm-b-stage-arrow {
  font-size: 9px; color: #444; flex-shrink: 0;
  transition: transform 150ms ease;
}
.mm-b-stage-label { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.mm-b-loop-count {
  font-size: 10px; background: #2a2a2a; color: #666;
  border-radius: 8px; padding: 1px 5px; flex-shrink: 0;
}

.mm-b-loop-list { padding: 0 0 4px 0; }

.mm-b-loop-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 12px 6px 26px; cursor: pointer; user-select: none;
  font-size: 12px; color: #555555; border-radius: 6px; margin: 0 4px;
  transition: color 120ms ease, background 120ms ease;
}
.mm-b-loop-item:hover  { color: #EBEBEB; background: #1a1a1a; }
.mm-b-loop-item.active { color: #CCFF00; background: #1e2210; }

.mm-b-loop-dot {
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
  transition: opacity 120ms;
}
.mm-b-loop-dot.happy { background: rgba(100, 220, 100, 0.8); }
.mm-b-loop-dot.edge  { background: rgba(255, 100, 100, 0.7); }
.mm-b-loop-item.active .mm-b-loop-dot.happy { box-shadow: 0 0 5px rgba(100,220,100,0.6); }
.mm-b-loop-item.active .mm-b-loop-dot.edge  { box-shadow: 0 0 5px rgba(255,100,100,0.5); }

.mm-b-loop-title {
  flex: 1; min-width: 0; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap;
}

.mm-b-loop-empty-state {
  padding: 4px 12px 8px 26px;
  font-size: 11px; color: #333; user-select: none;
}
```

**验收标准**：
- Mode B 左侧面板完整渲染，Stage 行显示 loop 数量气泡
- 点击 Stage 可折叠 / 展开，不影响右侧画布渲染
- 点击 Loop 行高亮对应行，再次点击取消
- 无 loops 的 Stage 展开后显示空状态

---

### Phase 4 — Mode B 行为连线渲染引擎

**目标**：Mode B 激活时隐藏 `#mm-lines`（结构连线），显示 `#mm-b-lines`（行为连线）；选中 Goal Loop 后，按 `steps[]` 中 action 步骤的 `refFeature` 顺序，在对应 feature 节点间绘制行为连线；无关卡片压暗。

> **核心原则**：`#mm-b-lines` 与 `#mm-lines` 使用**完全相同的视觉样式、SVG 元素结构、CSS 类和交互反馈**。`renderBLines()` 是 `renderLines()` 的**数据源扩展**——唯一的差异是连线的来源从 `childModule` 父子关系改为 `steps[]` 流转序列。Loop 类型（happy/edge）仅通过 CSS modifier 做轻度色调区分，不引入任何新的视觉语言。

---

**前提：HTML 新增 `#mm-b-lines` SVG 层**

在画布 DOM 中，与 `#mm-lines` 同级新增一个 SVG 元素（初始隐藏）：

```html
<!-- 与 #mm-lines 同级，Mode B 专属行为连线层 -->
<svg id="mm-b-lines" style="display:none; position:absolute; top:0; left:0;
     width:100%; height:100%; pointer-events:none; overflow:visible;"></svg>
```

同时在 `renderCanvas()` 最内层帧回调末尾，Mode B 下自动触发行为连线渲染：

```js
requestAnimationFrame(() => {
  renderLines(stage, cardMap);           // Mode A 结构连线，不改
  if (state.viewMode === 'B') {
    renderBLines(state.selectedLoopId);  // 新增：Mode B 行为连线
  }
});
```

---

**工具函数 1 — `flattenActionSteps(steps)`**

将嵌套 steps[] 扁平化，按深度优先顺序提取所有 `kind === 'action'` 且有 `refFeature` 的步骤：

```js
function flattenActionSteps(steps) {
  const result = [];
  function walk(steps) {
    for (const step of (steps || [])) {
      if (step.kind === 'action' && step.refFeature) result.push(step);
      walk(step.children);
    }
  }
  walk(steps);
  return result;
}
```

---

**工具函数 2 — `getFeatureConnectPoints(featId)`**

获取 feature 节点相对于 `.mm-canvas` 的连接坐标（右边缘出发点 + 左边缘到达点）：

```js
function getFeatureConnectPoints(featId) {
  const featEl = document.querySelector(`.mm-feature[data-feature-id="${featId}"]`);
  if (!featEl) return null;
  const canvasEl = document.querySelector('.mm-canvas');
  const cr = canvasEl.getBoundingClientRect();
  const fr = featEl.getBoundingClientRect();
  return {
    rx: fr.right  - cr.left,                       // 右边缘中点 X（出发）
    lx: fr.left   - cr.left,                       // 左边缘中点 X（到达）
    cy: fr.top    - cr.top  + fr.height / 2        // 垂直中点 Y
  };
}
```

---

**工具函数 3 — `cardHasCoveredFeature(moduleId, coveredSet, stage)`**

判断某张卡片是否包含被 coveredFeatures 覆盖的节点（用于卡片压暗判断）：

```js
function cardHasCoveredFeature(moduleId, coveredSet, stage) {
  const cardMap = buildCardMap(stage);
  const entry = cardMap[moduleId];
  if (!entry) return false;
  function check(module) {
    for (const feat of (module.features || [])) {
      if (coveredSet.has(feat.id)) return true;
      if (feat.childModule && check(feat.childModule)) return true;
    }
    return false;
  }
  return check(entry.module);
}
```

---

**工具函数 4 — `buildBLineEdges(loop)`**

将 `steps[]` 中的 action 序列转换为连线边数组，与 `renderLines()` 的输入格式对齐：

```js
// 返回值格式：[{ fromFeatId, toFeatId, triggersLayer }, ...]
function buildBLineEdges(loop) {
  const actionSteps = flattenActionSteps(loop.steps);
  const edges = [];
  for (let i = 0; i < actionSteps.length - 1; i++) {
    edges.push({
      fromFeatId:    actionSteps[i].refFeature,
      toFeatId:      actionSteps[i + 1].refFeature,
      triggersLayer: actionSteps[i].triggersLayer || null
    });
  }
  return edges;
}
```

---

**核心函数 — `renderBLines(loopId)`**

复用 `renderLines()` 的 SVG 元素结构（`line-hit` / `line-path` / `line-dot` / `line-diamond`）和全部已有 CSS 类，仅将数据源从 `childModule` 替换为 `buildBLineEdges()` 返回的边数组。Loop 类型通过追加 CSS modifier 类做轻度区分：

```js
// 在 renderLines() 每条连线生成处，参照现有 line-path / line-hit / line-dot 创建流程，
// 将 feat → feat.childModule 的配对替换为 edges[i].fromFeatId → edges[i].toFeatId：

function renderBLines(loopId) {
  clearBLines();
  if (!loopId) return;

  const loop  = getLoopById(loopId);
  if (!loop) return;

  const svg     = document.getElementById('mm-b-lines');
  const covered = new Set(loop.coveredFeatures);
  const stage   = getActiveStage();
  // loop 类型 modifier：追加到每条连线元素的 class 上，用于轻度色调区分
  const loopMod = loop.type === 'happy_path' ? 'b-happy' : 'b-edge';

  // 1. 无关卡片压暗
  document.querySelectorAll('.mm-card').forEach(card => {
    const hasCovered = cardHasCoveredFeature(card.dataset.moduleId, covered, stage);
    if (!hasCovered) card.classList.add('dimmed');
  });

  // 2. 构建行为连线边序列
  const edges = buildBLineEdges(loop);

  // 3. 按 renderLines() 相同元素结构绘制每条边
  //    ⚠️ 以下为伪代码框架，具体坐标计算和元素创建逻辑
  //    直接参照 renderLines() 中 line-path / line-hit / line-dot 的创建方式复制实现：
  for (const edge of edges) {
    const from = getFeatureConnectPoints(edge.fromFeatId);
    const to   = getFeatureConnectPoints(edge.toFeatId);
    if (!from || !to) continue;

    // 按 renderLines() 同款贝塞尔曲线路径计算
    // const d = <复用 renderLines() 中的 d 字符串计算逻辑>

    // line-hit（透明加粗，用于点击 / hover 交互）
    const hitEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    hitEl.setAttribute('class', `line-hit ${loopMod}`);
    hitEl.setAttribute('d', d);
    // 绑定与 renderLines() 相同的 click / mouseenter / mouseleave 事件

    // line-path（可见连线，完全复用 .line-path CSS 样式）
    const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    pathEl.setAttribute('class', `line-path ${loopMod}`);
    pathEl.setAttribute('d', d);

    // line-dot（终点圆点，复用 .line-dot CSS 样式）
    const dotEl = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dotEl.setAttribute('class', `line-dot ${loopMod}`);
    // cx / cy = to 坐标

    // triggersLayer 时追加虚线样式（层级跃迁标识）
    if (edge.triggersLayer) {
      pathEl.classList.add('line-path--layer-jump');
    }

    svg.appendChild(hitEl);
    svg.appendChild(pathEl);
    svg.appendChild(dotEl);
  }

  // 4. Phase 5：渲染锚点徽章 + 幽灵节点
  renderAnchorBadges(loop);
  renderSupplementGhosts(loop);
}
```

**新增 CSS（仅 loop 类型色调微调 + 层级跃迁虚线，不覆盖 `.line-path` 基础样式）**：

```css
/* ── Mode B 连线 loop 类型色调微调 ── */
/* happy_path：在 Mode A 连线颜色基础上偏绿色调 */
#mm-b-lines .line-path.b-happy { stroke: rgba(100, 220, 100, 0.75); }
#mm-b-lines .line-dot.b-happy  { fill:   rgba(100, 220, 100, 0.75); }

/* edge_case：在 Mode A 连线颜色基础上偏红色调 */
#mm-b-lines .line-path.b-edge  { stroke: rgba(255, 100, 100, 0.65); }
#mm-b-lines .line-dot.b-edge   { fill:   rgba(255, 100, 100, 0.65); }

/* 层级跃迁（triggersLayer 非 null）虚线标识 */
#mm-b-lines .line-path--layer-jump { stroke-dasharray: 5 3; }
```

> ⚠️ **实现说明**：步骤 3 中标注「伪代码框架」的坐标计算和 SVG 元素创建部分，开发时**直接参照现有 `renderLines()` 函数中对应代码段复制**，确保与 Mode A 的连线渲染逻辑字面对齐，不独立重新实现。

---

**主渲染函数 — `renderBLines(loopId)`**

```js
function renderBLines(loopId) {
  clearBLines();
  if (!loopId) return;

  const loop = getLoopById(loopId);
  if (!loop) return;

  const svg     = document.getElementById('mm-b-lines');
  const color   = loop.type === 'happy_path' ? '#64DC64' : '#FF6464';
  const covered = new Set(loop.coveredFeatures);
  const stage   = getActiveStage();

  // 1. 无关卡片压暗
  document.querySelectorAll('.mm-card').forEach(card => {
    const hasCovered = cardHasCoveredFeature(card.dataset.moduleId, covered, stage);
    if (!hasCovered) card.classList.add('dimmed');
  });

  // 2. 提取有序 action 步骤序列
  const actionSteps = flattenActionSteps(loop.steps);

  // 3. 逐对绘制有向折角箭头连线
  for (let i = 0; i < actionSteps.length - 1; i++) {
    const from = getFeatureConnectPoints(actionSteps[i].refFeature);
    const to   = getFeatureConnectPoints(actionSteps[i + 1].refFeature);
    if (!from || !to) continue;
    drawBezierArrow(svg, from, to, color, actionSteps[i].triggersLayer);
  }

  // 4. Phase 5：渲染锚点徽章 + 幽灵节点
  renderAnchorBadges(loop);
  renderSupplementGhosts(loop);
}
```

---

**清除函数 — `clearBLines()`**

```js
function clearBLines() {
  // 清除行为连线 SVG 内容（保留 defs/markers）
  const svg = document.getElementById('mm-b-lines');
  if (svg) {
    Array.from(svg.children).forEach(child => {
      if (child.tagName.toLowerCase() !== 'defs') child.remove();
    });
  }
  // 还原卡片压暗
  document.querySelectorAll('.mm-card.dimmed').forEach(c => c.classList.remove('dimmed'));
  // 清除锚点徽章和幽灵节点（Phase 5）
  document.querySelectorAll('.mm-anchor-badge').forEach(el => el.remove());
  document.querySelectorAll('.mm-ghost-node').forEach(el => el.remove());
}
```

---

**点击画布空白区域取消选中**：

```js
// 初始化时绑定一次
document.querySelector('.mm-canvas').addEventListener('click', (e) => {
  if (state.viewMode !== 'B') return;
  if (e.target.closest('.mm-card') || e.target.closest('.mm-b-loop-item')) return;
  state.selectedLoopId = null;
  clearBLines();
  document.querySelectorAll('.mm-b-loop-item').forEach(el => el.classList.remove('active'));
});
```

---

**新增辅助 CSS**：

```css
/* Mode B 卡片过渡 */
.mm-card { transition: opacity 180ms ease; }
.mm-card.dimmed { opacity: 0.15; pointer-events: none; }
```

**验收标准**：
- Mode B 激活时 `#mm-lines` 隐藏，`#mm-b-lines` 显示
- 无 Loop 选中时 `#mm-b-lines` 为空，所有卡片正常亮度
- 选中 Loop 后，行为连线的视觉样式（粗细、曲率、端点圆点、hover 高亮、click 选中）与 Mode A 连线**视觉上无法区分**，仅颜色有轻度色调偏移（happy 偏绿 / edge 偏红）
- 层级跃迁步骤（`triggersLayer` 非 null）的连线以虚线标识
- 切换 Loop / 点击空白区域，行为连线和卡片压暗正确清除
- Mode A 切回后 `#mm-lines` 恢复显示，Mode A 所有功能完全正常

---

### Phase 5 — 锚点徽章 & 补全幽灵节点

**目标**：高亮态下在 `isAnchor: true` 节点上注入 🔗 徽章，`[✨流转补全]` 节点以幽灵虚线形式叠加到画布。

**新增 `renderAnchorBadges(loop)` 函数**：

```js
function renderAnchorBadges(loop) {
  const anchorIds = collectAnchorFeatureIds(loop);
  anchorIds.forEach(featId => {
    const featEl = document.querySelector(`.mm-feature[data-feature-id="${featId}"]`);
    if (!featEl) return;

    const badge = document.createElement('span');
    badge.className = 'mm-anchor-badge';
    badge.textContent = '🔗';
    attachTip(badge, '模式 D 接力点 — 点击查看交互规范');
    badge.addEventListener('click', (e) => {
      e.stopPropagation();
      // 预留 Mode D 唤起接口，当前版本仅 console.log
      console.log('[Mode D Anchor]', featId);
    });
    featEl.appendChild(badge);
  });
}
```

**新增 `renderSupplementGhosts(loop)` 函数**：

```js
function renderSupplementGhosts(loop) {
  for (const sup of (loop.supplements || [])) {
    const refFeatEl = document.querySelector(
      `.mm-feature[data-feature-id="${sup.refNearFeature}"]`
    );
    if (!refFeatEl) continue;
    const featuresContainer = refFeatEl.closest('.mm-card-features');
    if (!featuresContainer) continue;

    const ghost = document.createElement('div');
    ghost.className = 'mm-ghost-node';
    ghost.innerHTML = `
      <span class="mm-ghost-icon">✨</span>
      <span class="mm-ghost-text">${sup.text}</span>
    `;
    attachTip(ghost, `[流转补全] ${sup.reason}`);
    featuresContainer.appendChild(ghost);
  }
}
```

**新增 CSS**：

```css
/* ── 锚点徽章 ── */
.mm-anchor-badge {
  font-size: 11px; flex-shrink: 0;
  cursor: pointer; margin-left: 2px;
  opacity: 0.85; line-height: 1;
  transition: transform 150ms ease, opacity 150ms ease;
}
.mm-anchor-badge:hover { transform: scale(1.4); opacity: 1; }

/* ── 幽灵补全节点 ── */
.mm-ghost-node {
  display: flex; align-items: center; gap: 6px;
  height: 30px; padding: 0 8px 0 10px;
  border-radius: 5px;
  border: 1.5px dashed rgba(204, 255, 0, 0.45);
  background: rgba(204, 255, 0, 0.03);
  opacity: 0;
  animation: ghostFadeIn 220ms ease 80ms forwards;
  pointer-events: auto; cursor: default;
}
.mm-ghost-icon { font-size: 11px; flex-shrink: 0; }
.mm-ghost-text {
  font-size: 12px; color: #555; flex: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

@keyframes ghostFadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

**验收标准**：
- 选中含 `isAnchor: true` 步骤的 loop，对应 feature 节点出现 🔗 徽章
- 悬浮徽章显示 tooltip「模式 D 接力点」
- 选中含 `supplements` 的 loop，幽灵节点以虚线样式淡入到对应卡片末尾
- 取消选中 / 切换 loop 后，徽章和幽灵节点正确清除

---

### Phase 6 — 步骤展开与单节点聚焦（进阶）

**目标**：Loop 行展开后显示 steps 列表，鼠标悬浮步骤时单节点聚焦高亮，其余 covered 节点降至次级亮度。

**左侧面板 Loop 行下展开步骤列表**：

```js
// renderBSidePanel() 中，在 loop 点击后展开 steps 子列表
// 新增 state.expandedLoopId（当前展开 steps 的 loop ID）

function renderBStepList(loop, container) {
  function renderSteps(steps, depth) {
    for (const step of (steps || [])) {
      const stepEl = document.createElement('div');
      stepEl.className = `mm-b-step mm-b-step-${step.kind}`;
      stepEl.style.paddingLeft = `${26 + depth * 10}px`;

      const kindLabel = { validation: 'IF', action: '→', feedback: '↩' }[step.kind] || '';
      const text = step.condition ||
        (step.refFeature
          ? `[${step.kind === 'action' ? '流转' : '反馈'}] ← ${step.refFeature}`
          : `[${step.kind === 'action' ? '流转' : '反馈'}]`);

      stepEl.innerHTML = `
        <span class="mm-b-step-kind">${kindLabel}</span>
        <span class="mm-b-step-text">${text}</span>
        ${step.isAnchor ? '<span class="mm-b-step-anchor">🔗</span>' : ''}
      `;

      // 悬浮步骤 → 单节点聚焦
      if (step.refFeature) {
        stepEl.addEventListener('mouseenter', () => highlightSingleFeature(step.refFeature, loop));
        stepEl.addEventListener('mouseleave', () => applyLoopHighlight(state.selectedLoopId));
      }
      container.appendChild(stepEl);
      if (step.children && step.children.length > 0) {
        renderSteps(step.children, depth + 1);
      }
    }
  }
  renderSteps(loop.steps, 0);
}
```

**新增 `highlightSingleFeature(featId, loop)` 函数**：

```js
function highlightSingleFeature(featId, loop) {
  // 所有 covered features 降至次级亮度
  loop.coveredFeatures.forEach(fId => {
    const el = document.querySelector(`.mm-feature[data-feature-id="${fId}"]`);
    if (!el) return;
    el.style.opacity    = fId === featId ? '1'   : '0.25';
    el.style.boxShadow  = fId === featId ? '0 0 0 1.5px #CCFF00, 0 0 8px rgba(204,255,0,0.3)' : '';
    el.style.transition = 'opacity 120ms ease, box-shadow 120ms ease';
  });
}
```

**新增 CSS**：

```css
/* ── 步骤列表 ── */
.mm-b-step {
  display: flex; align-items: flex-start; gap: 6px;
  padding-top: 4px; padding-bottom: 4px; padding-right: 12px;
  font-size: 11px; line-height: 1.4; cursor: default;
  border-radius: 4px; margin: 0 4px;
  transition: background 100ms ease;
}
.mm-b-step:hover { background: #1a1a1a; }

.mm-b-step-kind {
  flex-shrink: 0; font-size: 10px; font-weight: 600;
  margin-top: 1px; min-width: 14px;
}
.mm-b-step-text { flex: 1; min-width: 0; }
.mm-b-step-anchor { flex-shrink: 0; font-size: 10px; }

.mm-b-step-validation .mm-b-step-kind { color: #888; }
.mm-b-step-validation .mm-b-step-text { color: #666; font-style: italic; }
.mm-b-step-action    .mm-b-step-kind  { color: #CCFF00; }
.mm-b-step-action    .mm-b-step-text  { color: #999; }
.mm-b-step-feedback  .mm-b-step-kind  { color: #555; }
.mm-b-step-feedback  .mm-b-step-text  { color: #444; }
```

**验收标准**：
- 选中 loop 展开后显示 steps 列表，validation / action / feedback 三种类型颜色区分
- 悬浮 action 步骤时，对应 feature 节点聚焦高亮，其余 covered 节点降至 0.25
- 离开步骤后恢复 loop 级整体高亮

---

## 五、开发顺序与依赖图

```
Phase 1（数据层）
  └─→ Phase 2（Tab 切换 + state 扩展 + 连线层互斥切换）
        ├─→ Phase 3（左侧 B 面板）──────────────────────┐
        └─→ Phase 4（行为连线渲染引擎）                  │
              ├─ 新增 #mm-b-lines SVG 层（HTML 改动）    │
              ├─ flattenActionSteps / drawBezierArrow    │
              ├─→ Phase 5（锚点徽章 + 幽灵节点）          │
              └─→ Phase 6（步骤展开）←───────────────────┘
                    依赖 Phase 3 面板 + Phase 4 renderBLines
```

**各阶段可独立验收，前一阶段完成后再开始下一阶段。**

---

## 六、工作量评估

| Phase | 描述 | 复用比例 | 新增代码量 | 优先级 |
|---|---|---|---|---|
| P1 数据层 | mockDataB + 工具函数 | 0% | ~80 行 | 🔴 必须先行 |
| P2 Tab 切换 | state 扩展 + render 分流 + 连线层互斥 | 70% | ~50 行 | 🔴 必须先行 |
| P3 左侧 B 面板 | renderBSidePanel + CSS | 30% | ~120 行 | 🔴 核心交互 |
| P4 行为连线引擎 | #mm-b-lines + flattenActionSteps + drawBezierArrow + renderBLines | 15% | ~140 行 | 🔴 核心交互 |
| P5 锚点+幽灵 | attachTip 复用 | 20% | ~60 行 | 🟡 体验增强 |
| P6 步骤展开 | P3 面板结构 + P4 renderBLines 复用 | 60% | ~100 行 | 🟢 进阶功能 |
| **合计** | | | **~550 行** | |

---

## 七、关键注意事项

1. **`#mm-b-lines` 与 `#mm-lines` 严格互斥，绝不同时操作**
   Phase 4 的 `renderBLines()` 只写 `#mm-b-lines`，绝不触碰 `#mm-lines` 的任何元素。连线层切换仅通过 `display` 属性控制，不删除 DOM。

2. **`renderBLines()` 不触发完整 `render()`**
   仅操作 `#mm-b-lines` SVG 内容和卡片 `dimmed` 类，不重绘画布。选中 / 取消选中响应目标 < 50ms。

3. **`clearBLines()` 必须保留 `defs` 中的 marker 定义**
   清除连线时只移除 `path` 元素，不移除 `defs`，避免每次重新注入 arrowhead marker。

4. **`renderBLines()` 必须在 `renderCanvas()` 的最内层帧回调末尾调用**
   由于 `renderCanvas()` 内有 `requestAnimationFrame` 嵌套，行为连线必须等 feature DOM 渲染完毕后才能获取正确坐标。

5. **`renderBLines()` 中 SVG 元素创建逻辑直接复制自 `renderLines()`**
   不独立重新实现贝塞尔路径计算和 SVG 元素创建，始终与 `renderLines()` 的实现保持字面对齐。若 `renderLines()` 日后更新视觉样式，`renderBLines()` 同步跟进。

5. **Mode B 只读保护覆盖所有编辑入口**
   `renderCard` 和 `renderFeatureWrap` 中的 guard（`if (state.viewMode !== 'B')`）确保卡片编辑按钮、双击事件、拖拽在 Mode B 下全部禁用。`#mm-lines` 的 `line-hit` 点击事件同样需要 Mode B 下禁用。

6. **`state.expandedStageIds` 跨 Stage 切换时保持**
   切换 `activeStageId` 时不清空 `expandedStageIds`，保留用户展开状态。仅在切换 `viewMode` 时重置：
   ```js
   state.expandedStageIds = new Set([state.activeStageId]);
   ```

7. **`getFeatureConnectPoints()` 依赖 DOM 布局完成**
   该函数通过 `getBoundingClientRect()` 获取坐标，必须在画布渲染完成后调用，不可在 `renderCanvas()` 同步阶段调用。
