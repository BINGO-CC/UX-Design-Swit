# A股数据 MCP Server · 主文档

> **定位：** 本文件是交易审计系统的总入口文档。任何新设备、新平台、新场景下，AI 首先阅读本文件即可理解系统全貌并路由到正确操作。
> **文档体系：** 本文件为主文档，下辖两个子文档按需调用。
> **代码仓库：** `https://github.com/BINGO-CC/UX-Design-Swit/tree/main/trading-audit-system`

---

## 文档路由（AI 必读）

| 用户意图 | AI 应该做什么 | 参考文档 |
|---|---|---|
| **日常使用**（执行个股/板块审计） | 配好 MCP 连接 + 加载 Skill MD → 直接执行 | 本文件 + Skill 引擎 |
| **新增数据维度 / 修改工具** | 查阅子文档生成代码 + 指导用户 SSH 部署 | → `mcp_server_maintenance.md` |
| **理解系统架构 / 查看工具全景** | 查阅子文档了解设计背景 | → `mcp_server_dev_plan.md` |
| **服务器故障 / 连不上** | 按本文件"故障排查"章节处理 | 本文件 |
| **换新电脑 / 换新平台** | 按本文件"各平台配置"章节配置连接 | 本文件 |

> **AI 行为规范：** 当用户需求涉及代码修改或扩展时，AI 应主动查阅 `mcp_server_maintenance.md` 获取代码模板和部署流程，而非凭记忆生成。

---

## 一、系统概述

```
┌─────────────────────────────────────────────────┐
│            交易审计双引擎系统                      │
├─────────────────────────────────────────────────┤
│  Skill 层:                                       │
│  ├── trading_audit_engine_v2.md (个股审计引擎)   │
│  └── sector_audit_engine_v2.md  (板块审计引擎)   │
├─────────────────────────────────────────────────┤
│  数据层 (云端 MCP Server):                       │
│  ├── 17 个工具（行情/基本面/事件面/板块）        │
│  ├── 数据源：新浪财经(主) + 腾讯财经(备)        │
│  └── 后台预加载 + TTL 缓存                      │
├─────────────────────────────────────────────────┤
│  基础设施:                                       │
│  └── 腾讯云上海二区 · Docker · SSE 协议          │
└─────────────────────────────────────────────────┘
```

---

## 二、服务器连接信息

| 项目 | 值 |
|---|---|
| 公网 IP | `124.221.128.190` |
| 端口 | `8000` |
| 传输协议 | SSE (Server-Sent Events) |
| 连接地址 | `http://124.221.128.190:8000/sse` |
| Token | `f9df73198415a1a83487d5212afec2e1e65c4b799fa0f665fb8b1a7cf7887db3` |
| 服务器地域 | 腾讯云 · 上海二区 |
| 到期时间 | 2027-05-12 |
| SSH 登录 | `ssh ubuntu@124.221.128.190`（需密码） |
| 代码目录 | `/opt/stock-mcp-server/` |

---

## 三、标准操作流程

### 场景 A：日常使用（执行审计）

```
1. 确认 MCP 连接已配好（见第四章"各平台配置"）
2. 在对话中加载 Skill MD（粘贴或设为 Project Knowledge）
3. 用自然语言触发：
   "个股审计 + 600519 + 准入 + [截图] + 波段"
   或
   "主升板块 + 半导体 + [截图] + 波段"
4. AI 自动调用 MCP 工具拉取数据 + 解析截图 + 输出审计看板
```

### 场景 B：新增数据维度 / 修改工具

```
1. 打开子文档 mcp_server_maintenance.md
2. 把维护手册内容粘贴给 AI
3. 用自然语言描述需求："我要加一个获取北向资金持仓的工具"
4. AI 按手册模板生成代码 + 部署命令
5. 你 SSH 到服务器粘贴代码 → docker compose up -d --build
6. 完成，新工具全平台立即可用
```

### 场景 C：服务器故障

```
1. 检查本文件第七章"故障排查"
2. SSH 登录 → docker compose ps 查状态
3. 若容器挂了 → docker compose up -d
4. 若代码有问题 → 查阅 mcp_server_maintenance.md 修复
```

### 场景 D：换新电脑 / 新平台

```
1. git clone https://github.com/BINGO-CC/UX-Design-Swit.git
2. 打开 trading-audit-system/skills/ 目录
3. 按第四章配置 MCP 连接
4. 把 Skill MD 加载到 AI 对话中
5. 开始使用
```

---

## 四、各平台 MCP 配置方法

### CodeMaker

文件路径：项目根目录 `.codemaker/mcp.json`

```json
{
  "mcpServers": {
    "stock-data": {
      "type": "sse",
      "url": "http://124.221.128.190:8000/sse"
    }
  }
}
```

### Cursor

文件路径：项目根目录 `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "stock-data": {
      "type": "sse",
      "url": "http://124.221.128.190:8000/sse"
    }
  }
}
```

### Claude Desktop

文件路径：
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "stock-data": {
      "type": "sse",
      "url": "http://124.221.128.190:8000/sse"
    }
  }
}
```

### CODX / 其他 MCP 平台

通用格式（找到该平台的 MCP 配置入口，填入）：

```json
{
  "mcpServers": {
    "stock-data": {
      "type": "sse",
      "url": "http://124.221.128.190:8000/sse"
    }
  }
}
```

### 不支持 MCP 的平台

无需配置。Skill MD 内建降级机制：AI 会自动退化为"纯截图模式"，用户多提供 F10 截图即可。

---

## 五、可用工具清单（17 个）

### 个股模块（10 个）

| 工具名 | 功能 |
|---|---|
| `stock_realtime_quote` | 实时行情（现价/涨跌幅/换手率/量比） |
| `stock_technical_indicator` | 技术指标（MA/RSI/MACD/VWAP） |
| `stock_kline_data` | K线原始数据（OHLCV） |
| `stock_valuation` | 估值（PE/PB/分位/PEG） |
| `stock_profitability` | 盈利能力（ROE/毛利率/营收增速） |
| `stock_financial_report_date` | 业绩预告/财报日 |
| `stock_unlock_schedule` | 解禁日历 |
| `stock_shareholder_change` | 股东增减持/质押 |
| `stock_institutional_flow` | 龙虎榜/融资余额 |
| `stock_risk_event` | 风险事件（ST/问询函） |

### 板块模块（6 个）

| 工具名 | 功能 |
|---|---|
| `sector_overview` | 个股所属板块 + 热门板块 |
| `sector_realtime_quote` | 板块实时行情 |
| `sector_ratio_calc` | Ratio（吸金强度）计算 |
| `sector_resonance` | 共振度计算 |
| `sector_leaders` | 龙头识别 + 健康度判定 |
| `sector_turnover_history` | 板块成交额序列 + 持久性判定 |

### 大盘模块（1 个）

| 工具名 | 功能 |
|---|---|
| `index_realtime_quote` | 大盘指数 + 环境判定 |

---

## 六、配套文件清单

| 文件 | 用途 | 何时需要 |
|---|---|---|
| `trading_audit_engine_v2.md` | 个股审计引擎 Skill | 执行个股审计时加载 |
| `sector_audit_engine_v2.md` | 板块审计引擎 Skill | 执行板块审计时加载 |
| `mcp_server_maintenance.md` | 维护与扩展手册（子文档） | 新增工具/修改代码/排障时查阅 |
| `mcp_server_dev_plan.md` | 开发计划与架构（子文档） | 理解系统设计/新开发者入门时查阅 |

---

## 七、故障排查

| 问题 | 解决方法 |
|---|---|
| AI 平台提示连接不上 | SSH 进去执行 `sudo su && cd /opt/stock-mcp-server && docker compose ps` 查看是否 running |
| 容器状态 Restarting | `docker compose logs --tail 30` 查报错 → 修复 → `docker compose up -d --build` |
| 工具返回 error | 可能数据源限流，执行 `docker compose restart` 等待几分钟 |
| Token 忘了 | `ssh ubuntu@124.221.128.190` → `sudo cat /opt/stock-mcp-server/.env` |
| 服务器到期 | 腾讯云控制台续费（已开自动续费则无需操作） |
| 想加新工具但不知道怎么做 | 把 `mcp_server_maintenance.md` 丢给 AI，说明需求即可 |

---

## 八、快速恢复

```bash
ssh ubuntu@124.221.128.190
sudo su
cd /opt/stock-mcp-server
docker compose up -d
```

---

## 九、代码仓库

```
GitHub: https://github.com/BINGO-CC/UX-Design-Swit
路径:   trading-audit-system/
├── skills/              ← Skill 引擎 + 本文件 + 子文档
└── mcp-server/          ← MCP Server 完整源码
```

如需在新服务器重新部署，clone 仓库后参考 `mcp_server_maintenance.md` 或 `mcp_server_dev_plan.md`。
