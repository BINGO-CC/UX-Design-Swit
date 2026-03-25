# UX 设计交互编辑器 — 项目续接文档

> **文档版本**：v2.3（2026-03-25 更新）  
> **用途**：在新对话中快速恢复项目上下文，确保迭代连续性

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
| `f:\codemake\ux-design-editor.html` | 统一交互编辑器（主文件） | ✅ 已完成 v2.3 |
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
  B: [{ id, title, startPoint, keyPoint, stages: [...] }],
  C: [{ id, pageName, nodes: [{ id, icon, label, note, children: [...] }] }],
  D: [{ id, specName, visible: [...], interactions: [...], boundaries: [...] }]
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
| **分享** | 🔗 生成分享链接（URL 携带压缩数据） | LZ-String 压缩 + URL hash |
| **UI** | 四模式 Tab 切换 | `switchMode()` |
| **UI** | 卡片折叠/展开 | `collapsed` 属性 |
| **UI** | 优先级切换（模式A） | `aCyclePriority()` |
| **UI** | 存储状态指示 | 工具栏绿色圆点 |
| **UI** | 空状态引导 | 📭 图标 + 可点击导入链接 |
| **UI** | Toast 提示（顶部居中） | `toast()` 函数 |

### 2.3 代码结构（ux-design-editor.html）

```
行 1-170:    CSS 样式（含空状态、下拉菜单样式）
行 171-210:  HTML 结构（工具栏含下拉导出菜单 + Tab + 容器）
行 211-310:  核心工具函数（nid, toast, save, undo, redo, LocalStorage, clearStorage）
行 310-520:  拖拽排序 + 批注功能
行 520-620:  空状态判断 + 模式 A 渲染
行 620-910:  模式 B 渲染
行 910-1160: 模式 C 渲染
行 1160-1420:模式 D 渲染
行 1420-1570:onBlur 统一编辑处理
行 1570-1740:导入/导出功能（含模块级导出、diff对比、下拉菜单）
行 1740-1800:初始化逻辑（含快照加载）
```

### 2.4 关键新增数据结构

```javascript
// 导入快照（用于对比修改内容）
let importSnapshot = { A: {}, B: [], C: [], D: [] };
const SNAPSHOT_STORAGE_KEY = 'ux_design_editor_snapshot';

// 模式标签映射
const MODE_LABELS = { A: '策划案分析', B: '行为路径', C: '信息架构', D: '交互稿' };

// LZ-String 压缩库（内联，用于分享链接）
var LZString = { compressToEncodedURIComponent, decompressFromEncodedURIComponent, ... };
```

---

## 三、v2.1 新增功能详情

### 3.0.1 空状态引导
- **触发条件**：首次进入（无 LocalStorage）或点击"清除缓存"
- **表现**：所有 TAB 显示 📭 大图标 + "点击此处 📥 导入 JSON"（可点击，触发导入弹窗）
- **关键函数**：`isStoreEmpty()`, `renderEmptyState()`

### 3.0.2 模块级 JSON 导出
- **入口**：工具栏"📤 导出 JSON ▾"下拉菜单
- **选项1 — 导出该模块修改内容**：对比 `importSnapshot` 与当前 `store[activeMode]`，仅导出变化部分（标记 `_diff: added/modified/deleted`）。无修改时按钮置灰，点击提示"当前未存在任何修改"
- **选项2 — 导出该模块全部JSON**：导出当前 TAB 的完整数据
- **关键函数**：`exportJsonModDiff()`, `exportJsonModFull()`, `computeDiff()`, `isModuleDirty()`, `toggleExportDropdown()`

### 3.0.3 分享链接功能
- **入口**：工具栏"🔗 分享链接"按钮
- **原理**：使用 LZ-String 将 `store` 压缩为 URL-safe 字符串，拼接到 URL hash 中
- **打开流程**：对方打开链接 → 自动解压加载数据 → 存入各自 LocalStorage → 清除 URL hash
- **冲突处理**：若本地已有数据，弹窗询问是否覆盖
- **关键函数**：`generateShareLink()`, `copyShareLink()`, `loadFromShareLink()`
- **依赖库**：LZ-String（MIT License，内联压缩版）

### 3.0.4 控件布局调整（v2.3）
- **标题栏**：仅保留标题 + 🔗 分享链接 + 🗑️ 清除缓存
- **TAB 行**：左侧为 ABCD 四个 Tab，右侧为操作控件（已保存 / ↩↪ / 📥 导入 / 📤 导出 ▾）
- **导出菜单合并**：原"导出 MD"独立按钮合并进"📤 导出 ▾"下拉菜单，三个选项：导出该模块修改部分JSON / 导出全部JSON / 导出MarkDown
- TAB 行 `position:sticky;top:43px` 保持置顶

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

## 四、已填充的数据（科技2.0策划案）

### 4.1 模式 A — 策划案分析
- 2 条主目标 + 3 条隐性需求
- 4 个功能模块（文明遗产投放、逆向研究、科技发明、科技等级）

### 4.2 模式 B — 7 条行为路径
1. 文明遗产获取
2. 逆向研究（单个）
3. 逆向研究（批量）
4. 科技发明
5. 科技等级提升
6. 科技碎片加点（科技强化）
7. 拆解台特殊分支（文明遗产拦截）

### 4.3 模式 C — 9 个信息架构
1. 科技研究台 — 主界面
2. 逆向研究子页面
3. 道具选择列表
4. 研究结果面板
5. 科技发明子页面
6. 发明结果面板
7. 科技主界面
8. 科技强化界面
9. 拆解台拦截弹窗

### 4.4 模式 D — 10 份交互稿
1. 科技研究台 — 主界面
2. 逆向研究子页面
3. 道具选择列表
4. 研究结果面板
5. 科技发明子页面
6. 发明结果面板
7. 科技主界面
8. 科技强化界面
9. 科技等级升级演出
10. 拆解台拦截弹窗

---

## 五、UX设计 Skill 更新说明

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

## 六、待开发功能（P3）

| 优先级 | 功能 | 说明 |
|-------|------|------|
| P3-1 | 模式间数据引用 | 模式D交互稿引用模式B路径编号 |
| P3-2 | 批注导出 | 导出 Markdown/JSON 时包含批注 |
| P3-3 | 数据版本控制 | 支持保存/切换多个版本快照 |
| P3-4 | 主题切换 | 支持亮色/暗色主题 |
| P3-5 | 协作功能 | 多人实时编辑（需后端支持） |

---

## 七、常见迭代需求模板

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

## 八、新对话启动指令

**推荐使用以下指令开启新对话：**

---

> 我正在迭代一个"UX设计交互编辑器"项目。
> 
> 请先阅读项目续接文档 `f:\codemake\PROJECT_RESUME.md`，了解项目背景、技术架构和已实现功能。
> 
> 然后阅读主代码文件 `f:\codemake\ux-design-editor.html`，了解当前实现。
> 
> 接下来，请帮我完成：[你的具体需求]

---

## 九、JSON 数据结构参考

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

### 模式D（交互稿）
```json
{
  "D": [{
    "id": "n4001", "specName": "交互说明名称", "collapsed": false,
    "visible": [{ "id": "n4002", "text": "可见层条目" }],
    "interactions": [{ "id": "n4003", "text": "交互层条目" }],
    "boundaries": [{
      "id": "n4004", "type": "异常类型",
      "trigger": "触发条件", "feedback": "反馈内容", "recovery": "恢复路径"
    }]
  }]
}
```

---

## 十、版本历史

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| v1.0 | 2026-03-25 | 初始版本，4模式编辑器基础功能 |
| v2.0 | 2026-03-25 | 新增拖拽排序、批注、LocalStorage、完整数据填充、Skill JSON输出 |
| v2.1 | 2026-03-25 | 空状态引导页、模块级JSON导出（全部/仅修改）、Toast移至顶部、导入快照对比机制 |
| v2.2 | 2026-03-25 | 🔗 分享链接功能（LZ-String压缩 + URL hash），支持带数据分享给他人 |
| v2.3 | 2026-03-25 | 控件移至TAB行右侧、导出菜单合并、GitHub Pages部署、Git自动推送规则 |
