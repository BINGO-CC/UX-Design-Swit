# UX 设计交互编辑器 — 项目续接文档

> **文档版本**：v4.3.0（2026-03-30 更新）
> **用途**：在新对话中快速恢复项目上下文，确保迭代连续性
> ⚠️ **视觉规范**：所有 UI 新增/修改必须遵守 `UI_REDESIGN.md`（Notion Dark 设计系统 v1.3.0）

---

## 一、项目概述

### 1.1 项目目标
构建一个**单文件 HTML 可视化编辑器**，用于管理和编辑 UX 设计分析的四类产出物：
- **模式 A**：策划案分析（目标拆解 + 功能模块）
- **模式 B**：行为路径（泳道图 + 状态机）
- **模式 C**：信息架构（树状图）
- **模式 D**：交互稿（可见层 + 交互层 + 边界层）

### 1.2 核心文件清单

| 文件路径 | 说明 | 状态 |
|---------|------|------|
| `f:\codemake\ux-design-editor.html` | 统一交互编辑器（主文件） | ✅ 已完成 v4.0 |
| `f:\codemake\.codemaker\skills\ux-design.md` | UX设计 Skill 指令 | ✅ 已更新（含JSON输出） |
| `f:\codemake\PROJECT_RESUME.md` | 本文档 | ✅ 当前文件 |
| `f:\codemake\behavior-path-editor.html` | 早期原型（仅模式B） | 🔒 已废弃 |
| `f:\codemake\index.html` | 部署入口（跳转到编辑器） | ✅ |
| `f:\codemake\.codemaker\rules` | 项目规则（自动保存+推送） | ✅ |
| `f:\codemake\.gitignore` | Git 忽略配置 | ✅ |

---

## 二、技术架构

### 2.1 数据结构（核心）

```javascript
// 主数据存储
let store = {
  A: {
    goals: { main: [...], hidden: [...] },
    modules: [{ id, name, priority, features: [...], suggestions: [...] }]
  },
  B: [{ id, title, startPoint, refs: { A: [...] }, stages: [...] }],  // keyPoint 已移除
  C: [{ id, pageName, nodes: [{ id, icon, label, note, children: [...] }] }],
  D: [{ id, specName, refs: { B: [...], C: [...] }, elements: [...], flows: [...], boundaries: [...] }]
};

// 批注存储（独立于主数据）
let annotations = {}; // { nodeId: "批注内容" }

// LocalStorage 键名
const STORAGE_KEY = 'ux_design_editor_data';
const ANNO_STORAGE_KEY = 'ux_design_editor_annotations';
```

### 2.2 已实现功能

| 功能类别 | 具体功能 | 实现方式 |
|---------|---------|---------|
| **编辑** | 内联编辑（contenteditable） | `onBlur` 统一处理 |
| **编辑** | 新增/删除节点 | 各模式独立函数 |
| **编辑** | 撤销/重做（80步） | `hist[]` 数组 + `hIdx` 指针 |
| **排序** | 拖拽调整顺序 | HTML5 Drag & Drop API |
| **批注** | 添加/编辑/删除批注 | `annotations` 对象 |
| **持久化** | 自动保存到浏览器 | LocalStorage |
| **导入导出** | JSON 导入/导出 | `JSON.parse/stringify` |
| **导入导出** | JSON 模块级导出（全部/仅修改） | 下拉菜单 + `importSnapshot` 对比 |
| **导入导出** | Markdown 导出 | 自定义格式化函数 |
| **分享** | 🔗 分享文件导出（下载 .uxshare 文件） | LZ-String 压缩 + Blob 下载 |
| **分享** | 📥 分享文件导入（点击选择 + 全局拖拽） | FileReader + 自动格式检测 |
| **分享** | 兼容旧版 URL hash 分享链接 | `loadFromShareLink()` |
| **引用** | 模式间数据引用（D→B、D→C、B→A） | `refs` 字段 + `refIndex` 反向索引 |
| **引用** | 引用管理浮层（🔗按钮 + checkbox选择） | `openRefModal()` + `saveRefs()` |
| **引用** | 正向引用标签（可点击跳转） | `renderRefTags()` + `jumpToRef()` |
| **引用** | 反向引用标签（📍被引用 + 可点击跳转） | `renderBackRefTags()` + `refIndex` |
| **引用** | 变更检测（⚠️橙色标签 + 内容指纹） | `fingerprint()` + `hasRefChanged()` |
| **引用** | 变更详情弹窗 + 标记已读 | `showRefChangeDetail()` + `ackRefChange()` |
| **引用** | 📊 覆盖率报告（进度条 + 孤立节点） | `showCoverageReport()` + `generateCoverageReport()` |
| **引用** | 覆盖率报告 Markdown 导出 | `exportCoverageReportMd()` |
| **UI** | 四模式 Tab 切换 | `switchMode()` |
| **UI** | 卡片折叠/展开 | `collapsed` 属性 |
| **UI** | 模式B阶段"反馈与边界条件"浮层（v3.4） | `fb-popover-btn` + `openFbPopover()` + 阶段切换Tab |
| **UI** | 优先级切换（模式A） | `aCyclePriority()` |
| **UI** | 存储状态指示 | 工具栏绿色圆点 |
| **UI** | 空状态引导 | 📭 图标 + 可点击导入链接 |
| **UI** | Toast 提示（顶部居中） | `toast()` 函数 |
| **复制** | ⎘ 复制模块内容到剪贴板（A/B/C/D各模式） | `copyRichText()` 富文本+纯文本双格式 |
| **复制** | 标题自动加粗（粘贴至富文本编辑器） | `ClipboardItem` + `text/html` `<strong>` |
| **复制** | 输出过滤 emoji + 防前缀重复 | `stripEmoji()` + `safePrefix()` |
| **UI** | 全局新增按钮仅显示 ＋ 图标 | CSS `font-size:0` + `::before` |
| **UI** | 删除按钮全局统一红色无底样式 | `.step-del` 全局基础 + 各父容器 hover 显隐 |
| **UI** | 反馈与边界浮层黄色配色系 | `.fb-popover-btn` / `.fb-popover` / `.fb-stage-tab` |

### 2.3 代码结构（ux-design-editor.html）

```
行 1-202:    CSS 样式（含引用标签、覆盖率报告、高亮动画、下拉菜单、反馈与边界条件折叠容器样式）
行 196-260:  HTML 结构（工具栏含下拉导出菜单+覆盖率入口 + Tab + 容器）
行 261-390:  核心工具函数 + 引用网络数据层（refs/refIndex/fingerprint/ensureRefs/resolveRefTarget）
行 390-570:  引用UI层（renderRefTags/renderBackRefTags/jumpToRef/openRefModal/saveRefs）
行 570-650:  变更检测（showRefChangeDetail/computeRefChangeSummary/ackRefChange）
行 650-845:  覆盖率报告（generateCoverageReport/renderProgressBar/showCoverageReport/exportCoverageReportMd）
行 845-920:  LocalStorage + History + Tab切换 + 编辑绑定
行 920-960:  批注 + 拖拽排序
行 960-1040: 空状态判断 + 模式 A 渲染（含反向引用标签）
行 1040-1280:模式 B 渲染（含🔗按钮+引用标签+反向引用标签+反馈与边界条件折叠容器）
行 1260-1510:模式 C 渲染（含data-page属性+反向引用标签）
行 1510-1820:模式 D 渲染（含🔗按钮+引用标签+data-spec属性）
行 1820-1930:onBlur 统一编辑处理
行 1930-2120:导入/导出功能（含模块级导出、diff对比、下拉菜单、有实质内容才覆盖逻辑）
行 2120-2200:LZ-String 官方 v1.5.0 库
行 2200-2410:分享文件系统（openShareCodeManager/doExportShareFile/handleShareFileSelect/loadShareFileContent/applyShareData）
行 2410-2500:兼容旧版URL hash分享链接 + 初始化逻辑（含fingerprint加载+ensureRefs+全局拖拽监听）
```

### 2.4 关键新增数据结构

```javascript
// 导入快照（用于对比修改内容）
let importSnapshot = { A: {}, B: [], C: [], D: [] };
const SNAPSHOT_STORAGE_KEY = 'ux_design_editor_snapshot';

// 模式标签映射
const MODE_LABELS = { A: '策划案分析', B: '行为路径', C: '信息架构', D: '交互稿' };

// LZ-String 官方 v1.5.0（MIT License，内联完整版）
var LZString = { compress, decompress, compressToBase64, decompressFromBase64, compressToEncodedURIComponent, decompressFromEncodedURIComponent, ... };

// 引用网络相关（v3.0 新增）
const FINGERPRINT_STORAGE_KEY = 'ux_design_editor_fingerprints';
let refIndex = {};         // 运行时反向索引（不持久化）
let refFingerprints = {};  // 引用指纹（持久化，用于变更检测）
```

---

## 三、v2.1 新增功能详情

### 3.0.1 空状态引导
- **触发条件**：首次进入（无 LocalStorage）或点击"清除数据"
- **表现**：所有 TAB 显示 📭 大图标 + "点击此处 📥 导入 JSON"（可点击，触发导入弹窗）
- **关键函数**：`isStoreEmpty()`, `renderEmptyState()`

### 3.0.2 模块级 JSON 导出
- **入口**：工具栏"📤 导出 JSON ▾"下拉菜单
- **选项1 — 导出该模块修改内容**：对比 `importSnapshot` 与当前 `store[activeMode]`，仅导出变化部分（标记 `_diff: added/modified/deleted`）。无修改时按钮置灰，点击提示"当前未存在任何修改"
- **选项2 — 导出该模块全部JSON**：导出当前 TAB 的完整数据
- **关键函数**：`exportJsonModDiff()`, `exportJsonModFull()`, `computeDiff()`, `isModuleDirty()`, `toggleExportDropdown()`

### 3.0.3 分享文件功能（v3.1 重构）
- **入口**：工具栏"🔗 分享"按钮
- **导出方式**：下载 .uxshare 文件（LZ-String compressToBase64 压缩）
  - 可自定义文件名（留空以日期自动命名）
  - 可选仅导出当前模式
  - 文件内含 `_format: 'uxshare'`, `_version: '1.0'`, `_created`, `_modes`, `data` 元信息
- **导入方式**（三种）：
  1. 点击分享面板中的文件选择区域
  2. **全局拖拽**：直接拖 .uxshare / .json 文件到页面任何位置
  3. 兼容旧版 URL hash 分享链接（`#data=` 格式）
- **格式兼容**：自动检测压缩 .uxshare / 纯 JSON / 旧版 URL hash 三种格式
- **安全覆盖**：使用"有实质内容才覆盖"逻辑，空数组不会清除已有数据
- **关键函数**：`openShareCodeManager()`, `doExportShareFile()`, `handleShareFileSelect()`, `loadShareFileContent()`, `applyShareData()`, `loadFromShareLink()`
- **依赖库**：LZ-String 官方 v1.5.0（MIT License，内联完整版）

### 3.0.4 控件布局调整（v2.3）
- **标题栏**：仅保留标题 + 🔗 分享 + 🗑️ 清除缓存
- **TAB 行**：左侧为 ABCD 四个 Tab，右侧为操作控件（已保存 / ↩↪ / 📥 导入 / 📤 导出 ▾）
- **导出菜单合并**：原"导出 MD"独立按钮合并进"📤 导出 ▾"下拉菜单，四个选项：导出该模块修改部分JSON / 导出全部JSON / 导出MarkDown / 📊 引用覆盖率报告

### 3.0.5 导入修复（v3.0）
- **问题**：导入只含部分模式的 JSON 时，空数组 `[]`（truthy）会覆盖已有数据
- **修复**：改为检查"有实质内容"（A 检查 goals/modules 非空，B/C/D 检查数组长度 > 0）才覆盖
- **增强**：导入快照改为增量更新，Toast 显示具体导入了哪些模式

### 3.0.6 LZ-String 库修复（v3.0）
- **问题**：内联的 LZ-String 压缩版存在未声明变量 `t2` 的 bug，导致分享功能静默失败
- **修复**：替换为官方 v1.5.0 完整版
- TAB 行 `position:sticky;top:43px` 保持置顶

### 3.0.7 模式B"反馈与边界条件"交互演进

**v3.2 折叠容器方案**（已被 v3.4 浮层替代，CSS 类保留但不再使用）
- 原方案将反馈/分支包裹在可折叠 `.fb-wrapper` 容器中，`stage.fbCollapsed` 控制展开态

**v3.4 浮层方案（当前）**
- **入口**：每个阶段的 ` 反馈与边界` 按钮（`.fb-popover-btn`，紫色样式）
- **表现**：点击弹出全局居中浮层，顶部有所有阶段的 Tab 切换，可直接编辑反馈/分支
- **浮层内容**：系统反馈列表 + 分支条件列表，支持新增/删除/编辑
- **新增 CSS 类**：`.fb-popover-overlay` / `.fb-popover` / `.fb-stage-tabs` / `.fb-stage-tab` / `.fb-popover-body`
- **新增函数**：`openFbPopover()` / `closeFbPopover()` / `renderFbPopover()` / `switchFbPopoverStage()` / `bAddStepInPopover()` / `bAddBranchInPopover()` / `bAddBItemInPopover()` / `bindEditableInPopover()`
- **状态变量**：`fbPopoverState = { pid, sid }`（模块级，不持久化）

### 3.0.5 Toast 提示位置
- 从页面底部移至**顶部居中**，边距 20px

---

## 三（续）、部署信息

### 部署方式
- **平台**：GitHub Pages
- **仓库**：[https://github.com/BINGO-CC/UX-Design-Swit](https://github.com/BINGO-CC/UX-Design-Swit)
- **网页地址**：[https://bingo-cc.github.io/UX-Design-Swit/](https://bingo-cc.github.io/UX-Design-Swit/)
- **分支**：`main`，根目录 `/`
- **入口**：`index.html`（自动跳转到 `ux-design-editor.html`）

### Git 配置
- Git 路径：`"C:\Program Files\Git\cmd\git.exe"`
- 远程地址：`https://github.com/BINGO-CC/UX-Design-Swit.git`
- 本地目录：`f:\codemake`

### 更新流程
代码修改后执行：`git add -A` → `git commit` → `git push`，GitHub Pages 1-2 分钟内自动更新

---

## 四、UX设计 Skill 更新说明

更新后的 Skill（`.codemaker/skills/ux-design.md`）新增了：

1. **全局准则第6条**：双格式输出（Markdown + JSON）
2. **第八章**：JSON 数据输出规范
   - 数据结构定义（ABCD四模式）
   - ID 生成规则（n1000起/n2000起/n3000起/n4000起）
   - 字段映射规则

用户使用 `/UX` 或 `/FLOWER` 等触发词分析策划案后，AI 会输出：
1. Markdown 格式的分析结果
2. 可直接导入编辑器的 JSON 数据块

---

## 五、待开发功能（P3）

| 优先级 | 功能 | 说明 |
|-------|------|------|
| ~~P3-1~~ | ~~模式间数据引用~~ | ✅ **已完成 v3.0** — D→B、D→C、B→A 完整引用网络+变更检测+覆盖率报告 |
| P3-2 | 批注导出 | 导出 Markdown/JSON 时包含批注 |
| P3-3 | 数据版本控制 | 支持保存/切换多个版本快照 |
| P3-4 | 主题切换 | 支持亮色/暗色主题 |
| P3-5 | 协作功能 | 多人实时编辑（需后端支持） |
| ~~P3-6~~ | ~~Skill 续接生成指令~~ | ✅ **已完成 v4.2.0** — Skill 新增 `/UX-NEXT B` 和 `/UX-NEXT D` 增量续接指令执行规范，含输入格式、执行逻辑、refs 自动关联、输出规则 |
| ~~P3-7~~ | ~~编辑器"复制为 Prompt"按钮~~ | ✅ **已完成 v4.2.0** — 导出菜单首位新增"复制为 Prompt"（A→`/UX-NEXT B`、B→`/UX-NEXT D`、D置灰），删除原"导出该模块修改部分JSON" |

---

## 六、常见迭代需求模板

### 7.1 新增编辑器功能
```
请阅读 f:\codemake\PROJECT_RESUME.md 和 f:\codemake\ux-design-editor.html，
然后为编辑器新增 [功能名称] 功能，要求：
- [具体需求1]
- [具体需求2]
```

### 7.2 修复编辑器 Bug
```
请阅读 f:\codemake\ux-design-editor.html，
修复以下问题：[问题描述]
复现步骤：[步骤]
```

### 7.3 更新 UX设计 Skill
```
请阅读 f:\codemake\.codemaker\skills\ux-design.md，
更新 Skill 指令，新增/修改：[具体需求]
```

### 7.4 扩展数据内容
```
请阅读 f:\codemake\ux-design-editor.html 中的 initB()/initC()/initD() 函数，
新增以下数据：[数据描述]
```

---

## 七、新对话启动指令

**推荐使用以下指令开启新对话：**

---

> 我正在迭代一个"UX设计交互编辑器"项目。
> 
> 请按顺序完成以下准备步骤，**不得跳过**：
> 1. 阅读项目强制执行规则：`f:\codemake\.codemaker\rules`
> 2. 阅读项目续接文档：`f:\codemake\PROJECT_RESUME.md`，了解项目背景、技术架构和已实现功能
> 3. 阅读视觉设计规范：`f:\codemake\UI_REDESIGN.md`，了解 Notion Dark 设计系统与组件规范（**所有 UI 新增/修改必须遵守此规范**）
> 4. 阅读主代码文件：`f:\codemake\ux-design-editor.html`，了解当前实现
> 
> 准备完成后，请帮我完成：[你的具体需求]

---

## 八、JSON 数据结构参考

### 模式A（策划案分析）
```json
{
  "A": {
    "goals": {
      "main": [{ "id": "n1001", "text": "主目标描述" }],
      "hidden": [{ "id": "n1002", "text": "隐性需求描述" }]
    },
    "modules": [{
      "id": "n1003", "name": "模块名称", "priority": "high|mid|low",
      "collapsed": false,
      "features": [{ "id": "n1004", "text": "功能描述" }],
      "suggestions": [{ "id": "n1005", "text": "建议内容", "reason": "设计依据" }]
    }]
  }
}
```

### 模式B（行为路径）
```json
{
  "B": [{
    "id": "n2001", "title": "路径标题",
    "startPoint": "起点描述", "keyPoint": "体验关键点",
    "collapsed": false,
    "refs": { "A": ["n1003"] },
    "stages": [{
      "id": "n2002", "title": "阶段标题",
      "actions": [{ "id": "n2003", "text": "用户操作步骤" }],
      "feedbacks": [{ "id": "n2004", "text": "系统反馈内容" }],
      "branches": [{
        "id": "n2005", "label": "分支条件",
        "items": [{ "id": "n2006", "text": "分支内容" }]
      }]
    }]
  }]
}
```

### 模式C（信息架构）
```json
{
  "C": [{
    "id": "n3001", "pageName": "页面名称", "collapsed": false,
    "nodes": [{
      "id": "n3002", "icon": "📌", "label": "节点名称",
      "note": "设计依据/备注",
      "children": [{ "id": "n3003", "icon": "", "label": "子节点", "note": "", "children": [] }]
    }]
  }]
}
```

### 模式D（交互稿 · 终极交付物）
```json
{
  "D": [{
    "id": "n4001", "specName": "交互说明名称", "collapsed": false,
    "refs": { "B": ["n2001"], "C": ["n3001"] },
    "elements": [{
      "id": "n4002", "area": "区域名称",
      "items": [
        { "id": "n4003", "label": "展示内容", "desc": "具体字段、控件类型描述" },
        { "id": "n4004", "label": "规则分类名", "desc": "底层硬性限制描述" }
      ]
    }],
    "flows": [{
      "id": "n4010", "action": "操作名称",
      "trigger": "玩家物理动作", "validation": "系统校验逻辑",
      "steps": [{ "id": "n4011", "desc": "UI反馈描述" }],
      "exceptions": [{
        "id": "n4013", "scenario": "操作级异常场景名",
        "trigger": "触发条件", "defense": "防错设计", "recovery": "流程反馈"
      }]
    }],
    "boundaries": [{
      "id": "n4020", "scenario": "系统级异常场景名",
      "trigger": "系统侧触发条件", "defense": "防错设计", "recovery": "流程反馈"
    }]
  }]
}
```
> ✅ 模式 D v4.0 重构为三层：`elements[]`（元素状态与基础逻辑，按区域分组）+ `flows[]`（核心场景交互流，含内嵌操作级异常 `exceptions[]`）+ `boundaries[]`（系统级边界），与 SKILLS JSON 输出完全对应。B→D 关系从"平行映射"升级为"吸收与升华"。

---

## 九、版本历史

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| v1.0 | 2026-03-25 | 初始版本，4模式编辑器基础功能 |
| v2.0 | 2026-03-25 | 新增拖拽排序、批注、LocalStorage、完整数据填充、Skill JSON输出 |
| v2.1 | 2026-03-25 | 空状态引导页、模块级JSON导出（全部/仅修改）、Toast移至顶部、导入快照对比机制 |
| v2.2 | 2026-03-25 | 🔗 分享链接功能（LZ-String压缩 + URL hash），支持带数据分享给他人 |
| v2.3 | 2026-03-25 | 控件移至TAB行右侧、导出菜单合并、GitHub Pages部署、Git自动推送规则 |
| v3.0 | 2026-03-25 | 🔗 引用网络系统：D→B/D→C/B→A 三条引用链路、双向导航、变更检测、覆盖率报告 |
| v3.0.1 | 2026-03-26 | 修复导入覆盖bug + LZ-String库替换为官方v1.5.0 |
| v3.1 | 2026-03-26 | 分享重构为文件模式(.uxshare)：导出下载/点击导入/全局拖拽/自动格式检测 |
| v3.1.1 | 2026-03-26 | 分享面板精简（移除导入区）、勾选单模式导出时自动填充模式名为文件名 |
| v3.2 | 2026-03-26 | 模式B阶段新增"🔄 反馈与边界条件"可折叠父级容器（默认收起），包裹系统反馈+分支条件 |
| v3.2.1 | 2026-03-26 | 工具栏"清除缓存"改为"清除数据"，新增二次确认弹窗（覆盖A/B/C/D四模式全部数据） |
| v3.2.2 | 2026-03-26 | 拖拽热区精准化：仅 ⠿ drag-handle 图标响应拖动，非该区域不触发；新增 `bindHandleDrag()` 工具函数统一管理五个拖拽场景 |
| v3.3 | 2026-03-26 | 模式D结构重构：删除交互层（`interactions[]`），改为「界面规格」+「系统边界」两层结构，与 UX设计 Skill B+D 整合模式对齐 |
| v3.2.3 | 2026-03-26 | 修复清除数据弹窗确认后卡死问题：调换 remove() 与 doClearStorage() 执行顺序，先关弹窗再渲染 |
| v3.3.0 | 2026-03-27 | SKILLS对齐迭代：模式B删除 keyPoint 字段渲染；模式D恢复交互层（interactions[]）渲染区块；ux-design-rules.md 删除规则四；Skill Markdown模板同步更新 |
| v3.4.0 | 2026-03-27 | 全局UI重构：删除按钮移至 actions 区域（收起左侧）；添加按钮移至标题右侧（inline 样式）；所有新增操作点击后自动聚焦；B阶段拖拽支持跨路径；B阶段新增复制按钮(⎘)；反馈与边界条件改为浮层形式（fb-popover），支持阶段切换Tab；去除箭头字符元素 |
| v3.5.0 | 2026-03-27 | A.删除按钮全局统一红色+统一尺寸（step-del/del-btn/branch-header/node-actions）；B.复制(⎘)功能改为"复制模块内容到剪贴板"（纯文本，区分标题与正文），A/B/C/D各模块均支持；C1.新增操作后输入框内容清空（不再显示"请填写"等默认文本）；C2.模式D添加按钮从父级移至对应区块标题右侧（界面规格/交互层/系统边界各自 inline btn），删除原底部 add-btn；D.反馈与边界浮层固定高度（75vh），内容区自动换行不裁切 |
| v3.5.1 | 2026-03-27 | 反馈与边界按钮及浮层配色改为黄色系（`.fb-popover-btn`/`.fb-popover`边框/标题/`.fb-stage-tab` active 态） |
| v3.5.3 | 2026-03-27 | 条目级删除按钮样式全局统一（`.step-del` 基础样式提升至全局选择器，各父容器仅控制 opacity 显隐）；模式A「＋功能」「＋建议」按钮从父级 actions 移至对应区块标题右侧（包含功能/UX补充建议各自 inline btn），删除原底部 add-btn；`.sug-item`/`.bound-item` 预留 padding-right 防止按钮遮挡文本；浮层宽度 560→760px；阶段 Tab 区支持鼠标滚轮横滑（`wheel` 事件绑定）；浮层内分支标题删除按钮统一为 `.step-del` + `.branch-header:hover` 显隐 |
| v3.5.4 | 2026-03-27 | 全局新增按钮（`add-inline-btn`/`add-btn`）仅显示 ＋ 图标，隐藏文字（CSS `font-size:0` + `::before` 伪元素） |
| v3.5.5 | 2026-03-27 | `.step-del` 基础样式（background:none/border:none/color:red/opacity:0）提升至全局，`.step-item`/`.sug-item`/`.bound-item`/`.branch-header`/`.branch-item` 各自仅控制 hover opacity:1 |
| v3.5.6 | 2026-03-27 | 复制输出新增 `stripEmoji()` 过滤所有 emoji；修复 `bCopyStageToClipboard` 中"阶段"标题重复；`cCopyPage` 节点 icon 不再导出 emoji 改为统一 `├─` |
| v3.5.7 | 2026-03-27 | 复制输出支持富文本格式：`copyRichText()` 同时写入 `text/html`（标题 `<strong>` 加粗）+ `text/plain`（纯文本降级），兼容 Word/Google Docs/Notion/飞书；旧浏览器自动降级 `_copyPlainFallback()` |
| v3.5.8 | 2026-03-27 | 修复复制输出前缀重复问题：新增 `safePrefix()` 工具函数，检测字段内容是否已包含前缀避免重复拼接；分支标签改用 `↳` 前缀替代 `分支：`；`bCopyPath`/`bCopyStageToClipboard`/`dCopySpec` 中起点/阶段/触发/反馈/恢复字段全部走 safePrefix |
| v4.0.0 | 2026-03-28 | **模式D架构重构**：①Skill更新——D定位为终极交付物(SSoT)，B→D关系从"平行映射"升级为"吸收与升华"；新增四条生成法则（名词具象化/动词物理化/黑箱透明化/防御性设计）+输出粒度规则（多项目通用）②数据结构重构——`visible[]`→`elements[]`（按区域分组，含area+items[{label,desc}]）、`interactions[]`→`flows[]`（含action/trigger/validation/steps[]+内嵌exceptions[]）、`boundaries[]`字段名升级（type→scenario, feedback→defense）③编辑器UI全面适配——三个区块独立渲染子组件（renderDArea/renderDFlow/renderDException/renderDBoundary）④旧数据自动迁移函数`migrateD()`⑤复制/导出Markdown同步更新 |
| v4.1.0 | 2026-03-28 | **模式D交互优化**：①三大区块（元素/交互流/边界）支持独立折叠收起（`dToggleSec()`+`_colElem`/`_colFlow`/`_colBound` 运行时状态）②三大区块标题栏新增 ⎘ 复制按钮（`dCopyElements`/`dCopyFlows`/`dCopyBoundaries`）③交互流中每个操作卡片新增 ⎘ 复制按钮（`dCopyFlow`）④模块D内所有新增按钮统一右对齐（`justify-content:flex-end`/`sec-actions margin-left:auto`） |
| v4.1.1 | 2026-03-28 | **模式D BUG修复**：①区块收起按钮响应区域修正——移除 `spec-section-header` 的 `onclick`，仅 `sec-toggle-btn` 按钮本身可触发折叠/展开；移除 header 的 `cursor:pointer`；简化 `dToggleSec()` 去除 event 参数 ②收起箭头方向修正——移除 CSS `.spec-section.collapsed .sec-toggle-btn{transform:rotate(-90deg)}`，箭头字符自身已正确（收起▶/展开▼）③UI反馈条目删除按钮修复——`.bound-item .step-del` 改为 `.bound-item > .step-del`（直接子元素选择器），避免嵌套在 `step-item` 内的删除按钮被强制 `position:absolute` 飞到卡片右上角 ④UI反馈条目字体统一——`.step-item .step-content` 新增 `font-size:13px`，与触发条件/系统校验等保持一致 |
| v4.1.2 | 2026-03-30 | **模式D复制输出Emoji修复**：移除复制函数中硬编码的 emoji（🧩/🖱️/🚧/⚠️），统一输出纯文本标题（元素状态与基础逻辑/核心场景交互流/系统级边界/异常分支） |
| v4.1.3 | 2026-03-30 | **模式D渲染Emoji修复**：①移除异常分支标题 `⚠️` emoji ②移除每个异常情境卡片标题前的 `⚠️` emoji ③修复异常卡片间距（`margin:4px 0 4px` → `margin:4px 0 0`）消除多余空行 |
| v4.1.4 | 2026-03-30 | **模式D复制格式优化**：核心场景交互流复制输出时，每个操作（flow）之间增加空行分隔，便于浏览（`dCopySpec`/`dCopyFlows` 两处） |
| v4.1.5 | 2026-03-30 | **模式D布局修复**：异常分支和系统级边界的描述字段（触发条件/防错设计/流程反馈）改用 `display:flex;align-items:flex-start` 布局，标签与内容顶对齐，多行内容不再从标签下方换行 |
| v4.1.6 | 2026-03-30 | **隐藏模式C TAB**：信息架构模块 TAB 添加 `style="display:none"` 暂时隐藏，代码保留便于后续恢复 |
| v4.1.7 | 2026-03-30 | **模式D异常分支删除按钮修复**：删除按钮从绝对定位改为与标题同行 flex 布局，右对齐 + 常驻显示（opacity:0.6） |
| v4.1.8 | 2026-03-30 | **TAB精简**：移除顶部 TAB 的 A/B/C/D 前缀，仅保留中文名称（策划案分析/行为路径/信息架构/交互稿） |
| v4.2.0 | 2026-03-30 | **增量工作流 + 复制为 Prompt**：①Skill 新增 `/UX-NEXT B` 和 `/UX-NEXT D` 增量续接指令执行规范（含输入格式、执行逻辑、refs 自动关联、输出规则）②编辑器导出菜单删除"导出该模块修改部分JSON"，新增"复制为 Prompt"（首位）——模式A生成 `/UX-NEXT B` + A数据，模式B生成 `/UX-NEXT D` + B数据，模式D置灰③清理 `exportJsonModDiff`/`computeDiff`/`isModuleDirty` 等废弃函数 |
| v4.2.1 | 2026-03-30 | **视觉色系修复（一）**：模式D三区块底板颜色与标题同色系——visible(蓝)/interact(绿)/boundary(红)，使用CSS相邻选择器 `.spec-section-header.X + .spec-section-body` 实现 |
| v4.2.2 | 2026-03-30 | **视觉色系修复（二）**：模式B `action-block` 蓝底透明度从0.14统一降至0.04，与模式D元素区块色调一致 |
| v4.2.3 | 2026-03-30 | **视觉色系修复（三）**：模式D操作卡片（`d-flow-block`）颜色跟随所在区块色系——flows区绿色/boundaries区红色，去除硬编码蓝色 |
| v4.2.4 | 2026-03-30 | **色系对换**：交互稿模块 visible(元素状态)↔interact(交互流) 色系互换——元素状态改为绿色系，核心场景交互流改为蓝色系 |
| v4.2.5 | 2026-03-30 | **图标统一**：全部4处父级卡片删除按钮（`del-btn`）从 🗑 emoji 改为 `ICONS.x` SVG，与子级条目删除图标统一 |
| v4.3.0 | 2026-03-30 | **UX Pro Max 全面优化**：①`contenteditable:focus` 新增蓝底+底部蓝线聚焦态 ②`.step-del`/`add-inline-btn` 触控区扩大至min-height:28px ③`.card-header` 加 cursor:pointer ④卡片增加 box-shadow 层次感 + border-left 色条 ⑤新增 `@keyframes fadeSlideIn` 条目淡入动画 ⑥Toolbar重构：TAB内嵌品牌行（绝对居中）/操作栏三组分隔/撤销重做独立样式 ⑦Undo Toast替换confirm()——底部悬浮+3s红色进度条倒计时+可取消（5处父级删除全覆盖）⑧品牌图标从星形改为Layout线框图 ⑨TAB active态改为accent蓝底+蓝字+inset描边，彻底消除切换位移 ⑩模式A「核心目标拆解」独立为section标题（紫色系），新增按钮移至主目标/隐性需求子标题右侧；「功能模块拆解」标题改蓝色系，双模块色彩拉开感官 ⑪自定义滚动条（5px overlay悬浮，不占额外宽度） ⑫品牌icon加 display:inline-flex 修复垂直对齐 |
