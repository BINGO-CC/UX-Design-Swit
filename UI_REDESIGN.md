
# UX 设计交互编辑器 — 视觉重构文档

> **文档版本**：v1.0.0（2026-03-30）
> **用途**：记录 UI/UX 全面重构的设计决策、规范与实施计划，独立于主项目文档
> **范围**：仅修改 CSS + HTML 模板部分，**所有 JS 逻辑、函数名、DOM class 名保持不变**

---

## 一、重构背景

### 1.1 发起原因

基于 `ui-ux-pro-max-skill` 对编辑器进行专业级视觉升级，目标是从"功能可用"迈向"专业工具级视觉体验"。

### 1.2 重构范围

| 文件 | 修改内容 | 是否影响功能 |
|-----|---------|------------|
| `ux-design-editor.html` | 重写 `<style>` 段（行 10-418）+ `<body>` HTML 模板（行 420-467） | ❌ 不影响 |
| `PROJECT_RESUME.md` | **不修改** | — |

### 1.3 设计决策记录

| 决策项 | 选择 | 原因 |
|-------|------|------|
| 主题 | Dark Mode | 专业感强，减少长时间使用的视觉疲劳 |
| 风格参考 | Notion Dark | 轻盈、碬研感，操作流畅，信息层次清晰 |
| 重构范围 | 全面重构（视觉 + 布局 + 交互） | 彻底重写 CSS + HTML 模板，保留所有 JS |

---

## 二、设计系统规范

### 2.1 色彩系统（Notion Dark Token）

```css
:root {
  /* === 背景层级（5层） === */
  --bg:          #191919;   /* 全局背景 —— Notion 标准深色底 */
  --surface:     #202020;   /* 卡片/面板表面 */
  --surface2:    #2b2b2b;   /* 次级表面（悬浮、输入框背景） */
  --surface3:    #333333;   /* 三级表面（hover 高亮） */
  --surface4:    #3d3d3d;   /* 四级（选中态、激活态） */

  /* === 边框（极细，低对比） === */
  --border:      rgba(255,255,255,0.07);  /* 默认边框 */
  --border2:     rgba(255,255,255,0.12);  /* 强调边框（hover） */
  --border3:     rgba(255,255,255,0.18);  /* 最强边框（focus/active） */

  /* === 文字（4级层次） === */
  --text:        rgba(255,255,255,0.87);  /* 主文字 */
  --text2:       rgba(255,255,255,0.50);  /* 次要文字 */
  --text3:       rgba(255,255,255,0.28);  /* 弱化文字（占位/禁用） */
  --text4:       rgba(255,255,255,0.15);  /* 极弱文字 */

  /* === 强调色（单一蓝色，低饱和） === */
  --accent:      #5f7fff;                 /* 主强调 —— Notion 风格蓝 */
  --accent-dim:  rgba(95,127,255,0.14);   /* 强调色背景 */
  --accent-glow: rgba(95,127,255,0.22);   /* 强调色 hover 背景 */

  /* === 语义色 === */
  --green:       #4caf89;
  --green-dim:   rgba(76,175,137,0.12);
  --orange:      #e8a048;
  --orange-dim:  rgba(232,160,72,0.12);
  --red:         #e06b6b;
  --red-dim:     rgba(224,107,107,0.12);
  --yellow:      #d4a017;
  --yellow-dim:  rgba(212,160,23,0.14);
  --purple:      #9b87d4;
  --purple-dim:  rgba(155,135,212,0.12);

  /* === 尺寸规范 === */
  --radius:      8px;
  --radius-sm:   5px;
  --radius-xs:   3px;

  /* === 阴影 === */
  --shadow-sm:   0 1px 2px rgba(0,0,0,0.3);
  --shadow-md:   0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg:   0 8px 28px rgba(0,0,0,0.55);
  --shadow-xl:   0 16px 48px rgba(0,0,0,0.65);

  /* === 动效时长 === */
  --dur-fast:    120ms;
  --dur-base:    180ms;
  --dur-slow:    280ms;
  --ease:        cubic-bezier(0.16, 1, 0.3, 1);  /* ease-out-expo */
}
```

---

### 2.2 字体规范

```css
/* 字体栈 */
font-family: 'Inter', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;

/* 字号层级 */
--text-xs:   11px;   /* 标签、角标、元信息 */
--text-sm:   12px;   /* 次要正文、说明文字 */
--text-base: 13px;   /* 主正文 */
--text-md:   14px;   /* 卡片标题、列表标题 */
--text-lg:   15px;   /* 模块标题 */
--text-xl:   16px;   /* 页面级标题 */

/* 字重 */
--weight-regular: 400;
--weight-medium:  500;
--weight-semi:    600;
--weight-bold:    700;

/* 行高 */
body: line-height: 1.65;
标题: line-height: 1.3;
```

---

### 2.3 间距规范

```
4px   — 组件内微间距（图标与文字）
6px   — 小型间距（按钮内边距纵向）
8px   — 基础间距（行内元素间距）
12px  — 中等间距（列表项间距）
16px  — 标准间距（卡片内边距、section 间距）
20px  — 大间距（容器横向 padding）
24px  — 特大间距（卡片上下 padding）
32px  — 模块间距（card margin-bottom）
```

---

## 三、组件规范

### 3.1 Toolbar（顶部标题栏）

**设计目标**：极简导航栏，Notion 风格的低存在感

```
┌─────────────────────────────────────────────────────────────┐
│  ◆ UX 设计交互编辑器              [分享]  [清除数据]          │
└─────────────────────────────────────────────────────────────┘

高度: 44px
背景: rgba(25,25,25,0.92) + backdrop-filter:blur(16px)
边框底部: 1px solid var(--border)
标题: font-size:14px, font-weight:600, letter-spacing:0.02em
Logo 图标: SVG 菱形（替换 emoji 🎨）
按钮: ghost 风格，仅文字 + 微边框，hover 时白底黑字
```

**按钮样式规范（Toolbar）**

```css
.toolbar-btn {
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border2);
  background: transparent;
  color: var(--text2);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease);
}
.toolbar-btn:hover {
  background: var(--surface3);
  border-color: var(--border3);
  color: var(--text);
}
```

---

### 3.2 Tab Bar（模式切换栏）

**设计目标**：Notion 风格的内联 Tab，胶囊式 active 态

```
┌─────────────────────────────────────────────────────────────┐
│  [策划案分析]  [行为路径]  [交互稿]   ·  ↩↪  |  📥  [导出▾] │
└─────────────────────────────────────────────────────────────┘

高度: 40px
背景: rgba(25,25,25,0.88) + backdrop-filter:blur(16px)
```

**Tab 激活态**：胶囊背景而非下划线

```css
.mode-tab {
  padding: 5px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  color: var(--text2);
  cursor: pointer;
  transition: all var(--dur-fast);
  margin: 6px 2px;
}
.mode-tab:hover { background: var(--surface2); color: var(--text); }
.mode-tab.active {
  background: var(--surface3);
  color: var(--text);
  font-weight: 600;
}
```

---

### 3.3 Card（内容卡片）

**设计目标**：轻盈卡片，极细边框，悬浮时微阴影提升

```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 10px;
  transition: border-color var(--dur-base), box-shadow var(--dur-base);
}
.card:hover {
  border-color: var(--border2);
  box-shadow: var(--shadow-md);
}
.card-header {
  padding: 12px 16px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.card-body { padding: 0 16px 14px; }
```

---

### 3.4 按钮规范

| 类型 | 使用场景 | 样式描述 |
|-----|---------|---------|
| **Ghost** | 工具栏操作 | 透明背景 + 细边框，hover 微填充 |
| **Text** | 卡片内操作 | 无背景无边框，hover 时浅背景 |
| **Danger Text** | 删除操作 | 红色文字，hover 红色浅背景 |
| **Dashed** | 新增操作 | 虚线边框，＋ 图标，hover 强调色 |
| **Tag** | 标签/引用 | 胶囊形，极小 padding，多种颜色变体 |

**Delete 按钮**（全局统一）
```css
.step-del {
  background: none;
  border: none;
  color: var(--red);
  cursor: pointer;
  font-size: 12px;
  padding: 2px 5px;
  border-radius: var(--radius-xs);
  opacity: 0;
  transition: opacity var(--dur-fast), background var(--dur-fast);
  line-height: 1;
}
.step-del:hover { opacity: 1; background: var(--red-dim); }
```

---

### 3.5 Editable 内联编辑

```css
.editable {
  cursor: text;
  padding: 2px 4px;
  border-radius: var(--radius-xs);
  transition: background var(--dur-fast);
  outline: none;
  min-height: 1.65em;
}
.editable:hover { background: var(--surface2); }
.editable:focus {
  background: var(--surface2);
  box-shadow: 0 0 0 1.5px var(--accent);
}
```

---

### 3.6 Toast 通知

```css
.toast {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
  background: var(--surface3);
  border: 1px solid var(--border2);
  padding: 7px 18px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.01em;
  color: var(--text);
  box-shadow: var(--shadow-lg);
  z-index: 400;
  opacity: 0;
  transition: opacity var(--dur-base) var(--ease), 
              transform var(--dur-base) var(--ease);
  pointer-events: none;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
```

---

### 3.7 Modal 弹窗

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.65);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}
.modal {
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: 12px;
  padding: 22px;
  width: 90%;
  max-width: 640px;
  max-height: 82vh;
  overflow-y: auto;
  box-shadow: var(--shadow-xl);
}
```

---

### 3.8 FB Popover（反馈与边界浮层）

**配色调整**：从黄色系改为紫色系（更专业、更少突兀感）

```css
.fb-popover-btn {
  background: var(--purple-dim) !important;
  border: 1px solid rgba(155,135,212,0.35) !important;
  color: var(--purple) !important;
  font-size: 12px;
  padding: 3px 9px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--dur-fast);
}
.fb-popover-btn:hover {
  background: rgba(155,135,212,0.22) !important;
  border-color: var(--purple) !important;
}
.fb-stage-tab.active {
  background: var(--purple-dim);
  border-color: var(--purple);
  color: var(--purple);
  font-weight: 600;
}
```

---

## 四、布局规范

### 4.1 页面整体布局

```
┌──────────────────────────── Toolbar (44px sticky) ──────────┐
├──────────────────────────── Tab Bar (40px sticky) ──────────┤
│                                                               │
│   ┌─────────────────────── Container (max-w: 900px) ──────┐  │
│   │                                                        │  │
│   │   [Card]                                               │  │
│   │   [Card]                                               │  │
│   │   ...                                                  │  │
│   └────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 容器宽度

```css
.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 20px 60px;
}
```

### 4.3 Z-Index 层级

```
10   — sticky 工具栏、Tab 栏
50   — Dropdown 菜单
100  — Context Menu
200  — Modal 遮罩
210  — Modal 内容
250  — FB Popover 遮罩
260  — FB Popover 内容
300  — Toast
```

---

## 五、SVG 图标规范

> **原则**：全局使用 SVG 内联图标替代 emoji，保持视觉一致性

| 使用位置 | 图标类型 | 来源 |
|---------|---------|------|
| 工具栏品牌 Logo | 菱形/星形 | 自定义 SVG |
| 删除按钮 | X 图标 | Heroicons `x-mark` |
| 折叠/展开 | Chevron | Heroicons `chevron-right/down` |
| 复制按钮 | 复制图标 | Heroicons `document-duplicate` |
| 拖拽手柄 | 网格点 | Heroicons `squares-2x2` 变体 |
| 撤销/重做 | 旋转箭头 | Heroicons `arrow-uturn-left/right` |
| 导入 | 箭头向下盒子 | Heroicons `arrow-down-tray` |
| 导出 | 箭头向上盒子 | Heroicons `arrow-up-tray` |
| 分享 | 链接 | Heroicons `link` |
| 清除 | 垃圾桶 | Heroicons `trash` |
| 存储状态 | 圆点（动态） | CSS 实现 |

---

## 六、实施计划

### Phase 1：CSS 变量与基础样式重构（必须先完成）

- [ ] 重写 `:root` 色彩 Token
- [ ] 重写 `body` 基础样式
- [ ] 重写 `Toolbar` 样式
- [ ] 重写 `Tab Bar` 样式（含 active 态改为胶囊式）
- [ ] 重写 `Card` 样式（减轻厚重感）
- [ ] 重写 `Editable` 内联编辑样式

### Phase 2：组件样式升级

- [ ] 重写所有 `button` 变体（ghost/text/danger/dashed）
- [ ] 统一 `step-del` / `del-btn` 删除按钮
- [ ] 重写 `Branch` / `Stage` 样式（模式B）
- [ ] 重写 `Spec Section` 样式（模式D）
- [ ] 重写 `add-btn` / `add-inline-btn`
- [ ] 重写 `annotation` 批注样式
- [ ] 重写 `ref-tag` / `back-ref-tag` 引用标签

### Phase 3：浮层与弹窗

- [ ] 重写 `Modal` 弹窗（增加 backdrop-filter）
- [ ] 重写 `FB Popover`（配色改为紫色系）
- [ ] 重写 `Dropdown Menu`
- [ ] 重写 `Context Menu`
- [ ] 重写 `Toast` 通知

### Phase 4：HTML 模板优化

- [ ] Toolbar 中 emoji 替换为 SVG 图标
- [ ] 工具栏按钮添加 `aria-label`
- [ ] 调整按钮顺序和分组（提升操作逻辑性）

### Phase 5：微交互与动效

- [ ] 统一所有 `transition` 使用 `--ease` 缓动函数
- [ ] 卡片 hover 阴影动效
- [ ] Tab 切换动效
- [ ] 添加 `@media (prefers-reduced-motion: reduce)` 优化

---

## 七、版本记录

| 版本 | 日期 | 内容 |
|-----|------|------|
| v1.0.0 | 2026-03-30 | 创建文档，完成设计系统规范定义 |
| v1.1.0 | 2026-03-30 | Phase 1-5 全面重构：Notion Dark 主题、CSS Token、SVG 图标替换 Emoji、组件样式升级 |
| v1.2.0 | 2026-03-30 | Icon System 统一：新增 `ICONS` JS 对象（Heroicons Outline 规范），替换全局 ⠿/▶▼/⎘/✕/🔗/📍/⚠️/✅/📭/🧩 共 40+ 处 |

---

## 八、新对话续接指南

> 下次开启新对话想继续迭代视觉，只需在对话开头说：

```
我正在迭代"UX设计交互编辑器"项目的视觉重构。
请先阅读 UI_REDESIGN.md，了解已完成的设计系统与当前进度，然后继续迭代。
```

### 当前已完成内容（截至 v1.2.0）

| Phase | 状态 | 内容 |
|-------|------|------|
| Phase 1：CSS Token | ✅ 完成 | Notion Dark 色彩系统，5级背景，4级文字，动效变量 |
| Phase 2：组件升级 | ✅ 完成 | Toolbar/TabBar/Card/Button/Editable 全部重写 |
| Phase 3：浮层弹窗 | ✅ 完成 | Modal/Toast/FB Popover(紫色系)/Dropdown |
| Phase 4：HTML模板 | ✅ 完成 | emoji→SVG，aria-label，按钮结构优化 |
| Phase 5：微交互 | ✅ 完成 | cubic-bezier 缓动，hover 反馈，prefers-reduced-motion |
| Icon System | ✅ 完成 | `ICONS` JS对象(Heroicons Outline)，全局40+处替换 |
| Mode B 风格对齐 | ✅ 完成 | action-block 与 Mode D flow 背景色统一，阶段/操作 SVG 图标 |

### 待迭代方向（可选项）

| 优先级 | 方向 | 说明 |
|-------|------|------|
| 🔴 高 | 暗色主题可读性精调 | 扫描所有硬编码颜色，统一替换为 CSS Token |
| 🔴 高 | Mode D 交互稿 inline style 清理 | 大量 `style=""` 内联样式改为 CSS class |
| 🟡 中 | FB Popover 视觉优化 | 弹窗内 feedback/branch 区块视觉层次提升 |
| 🟡 中 | 卡片拖拽视觉反馈 | `.drag-over` 样式更精细，拖拽时阴影动效 |
| 🟢 低 | 空状态插画 | 各模式定制化空状态（目前共用同一 SVG） |
| 🟢 低 | 亮色主题支持 | `@media (prefers-color-scheme: light)` |

### 关键文件速查

| 文件 | 说明 |
|-----|------|
| `ux-design-editor.html` | 主文件，CSS 在行 10-430，ICONS 对象在行 ~547 |
| `UI_REDESIGN.md` | **本文档**，视觉设计系统规范 |
| `PROJECT_RESUME.md` | 主项目续接文档（功能迭代用） |

---

## 九、预交付检查清单

> 参考 `ui-ux-pro-max-skill` Pre-Delivery Checklist

### 视觉质量
- [ ] 工具栏 emoji 全部替换为 SVG 图标
- [ ] 所有图标来自统一图标集（Heroicons）
- [ ] Hover 状态不引起布局位移
- [ ] 直接使用 CSS 变量，不使用 `var()` 嵌套包装

### 交互
- [ ] 所有可点击元素有 `cursor: pointer`
- [ ] Hover 状态有明确视觉反馈
- [ ] 过渡动效 120-280ms，使用 cubic-bezier 缓动
- [ ] 键盘导航 focus 状态可见

### 对比度与可读性
- [ ] 主要文字对比度 ≥ 4.5:1（`rgba(255,255,255,0.87)` 在 `#191919` 上约 12:1 ✅）
- [ ] 次要文字对比度 ≥ 3:1（`rgba(255,255,255,0.50)` 在 `#191919` 上约 6:1 ✅）
- [ ] 边框在深色背景上可见

### 无障碍
- [ ] 图标按钮有 `aria-label`
- [ ] 表单元素有关联 label
- [ ] `prefers-reduced-motion` 媒体查询已实现
- [ ] Tab 键顺序与视觉顺序一致
