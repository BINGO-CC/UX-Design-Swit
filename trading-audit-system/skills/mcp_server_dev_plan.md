# A 股数据 MCP Server · 开发计划

> 目标：构建一台云端 MCP Server，为「个股审计引擎 v2.2+」及「板块审计引擎 v2.1」提供自动化数据拉取能力。
> 部署后，任何支持 MCP 协议的 AI 平台（CodeMaker / Cursor / Claude Desktop 等）均可直接调用。

---

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    云端 A 股数据 MCP Server                       │
│                   (轻量云服务器 · 公网可达)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐                │
│  │  行情模块  │    │ 基本面模块 │    │  事件模块  │                │
│  │ realtime  │    │ financial │    │   event   │                │
│  └─────┬─────┘    └─────┬─────┘    └─────┬─────┘                │
│        │                │                │                       │
│        └────────────────┼────────────────┘                       │
│                         │                                        │
│              ┌──────────▼──────────┐                             │
│              │    数据源适配层       │                             │
│              │  (AKShare + 缓存)    │                             │
│              └──────────┬──────────┘                             │
│                         │                                        │
│              ┌──────────▼──────────┐                             │
│              │   MCP 协议传输层     │                             │
│              │  (FastMCP · SSE)     │                             │
│              └─────────────────────┘                             │
│                                                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SSE / Streamable HTTP
              ┌────────────┼────────────┐
              │            │            │
         CodeMaker      Cursor     Claude Desktop
         (办公机)      (笔记本)     (任意设备)
```

---

## 二、技术栈选型

| 层面 | 技术选型 | 选型理由 |
|---|---|---|
| **语言** | Python 3.11+ | AKShare 原生 Python 生态，开发最快 |
| **MCP 框架** | FastMCP (mcp Python SDK) | 官方推荐，支持 SSE 传输，最少样板代码 |
| **数据源** | AKShare（主）+ 东方财富 HTTP（备） | AKShare 免费、覆盖全、无 API Key 限制 |
| **缓存** | Redis（可选）/ 内存 TTL 缓存 | 避免高频重复请求，行情缓存 5s，基本面缓存 4h |
| **部署** | 轻量云 + Docker | 一键部署、易迁移、可复现 |
| **传输协议** | SSE (Server-Sent Events) | MCP 远程标准协议，穿透防火墙 |
| **反向代理** | Nginx + HTTPS | 安全传输，支持 Token 鉴权 |

---

## 三、MCP 工具接口清单（4 大模块 · 12 个工具）

### 模块 1：实时行情 (Realtime)

| 工具名 | 入参 | 返回数据 | 用途 |
|---|---|---|---|
| `stock_realtime_quote` | `code: str` | 现价、涨跌幅、成交额、换手率、量比、振幅 | 行情基础数据 |
| `stock_technical_indicator` | `code: str, period: str` | MA5/10/20/60/120/250、RSI、MACD(DIF/DEA/柱)、VWAP、布林带 | 技术面审计 |
| `stock_kline_data` | `code: str, period: str, count: int` | 近 N 根 K 线 OHLCV 数据 | 量价关系分析 |
| `index_realtime_quote` | `index_code: str` | 指数现价、MA60、MACD 状态(金叉/死叉+天数) | 大盘环境过滤器 |

### 模块 2：基本面 (Fundamental)

| 工具名 | 入参 | 返回数据 | 用途 |
|---|---|---|---|
| `stock_valuation` | `code: str` | PE/PB(TTM)、PE/PB 历史分位(近5年)、PEG、市值 | 估值审计 |
| `stock_profitability` | `code: str` | ROE(近4季)、毛利率、净利率、营收YoY、扣非净利YoY | 盈利能力审计 |
| `stock_financial_report_date` | `code: str` | 下一财报披露日、距今交易日数、业绩预告摘要 | 业绩窗口期保护 |

### 模块 3：事件面 (Event)

| 工具名 | 入参 | 返回数据 | 用途 |
|---|---|---|---|
| `stock_unlock_schedule` | `code: str` | 未来90日解禁规模、解禁日期、占流通市值比例 | 抛压事件审计 |
| `stock_shareholder_change` | `code: str` | 大股东增减持记录(近30日)、质押率 | 股东行为审计 |
| `stock_institutional_flow` | `code: str` | 龙虎榜席位、北向持股变动(近5日)、融资余额变动 | 资金特殊席位 |
| `stock_risk_event` | `code: str` | ST状态、问询函/立案公告、重组预期、业绩预告(预减/预亏) | 监管与黑天鹅 |

### 模块 4：板块联动 (Sector) — 板块审计引擎专用

| 工具名 | 入参 | 返回数据 | 用途 |
|---|---|---|---|
| `sector_overview` | `code: str` | 标的所属板块、板块涨跌幅、板块成交额(近3日)、板块内排名 | 个股引擎：板块归属查询 |
| `sector_realtime_quote` | `sector_name: str` | 板块涨跌幅、成交额(亿)、上涨/下跌家数、涨停/跌停家数 | 板块实时行情 |
| `sector_ratio_calc` | `sector_name: str` | 板块成交额、全市场成交额、Ratio(%)、Ratio等级判定 | 流量持久性判定 |
| `sector_resonance` | `sector_name: str` | 成分股总数、站上MA20家数、共振度(%)、等级判定 | 共振度计算 |
| `sector_leaders` | `sector_name: str` | 龙头候选列表(代码/涨幅/换手/新高/健康度)、总体健康度判定 | 龙头识别+健康度 |
| `sector_turnover_history` | `sector_name: str, days: int` | 每日成交额序列、近3日重心、持久性判定(确定性/观察/脉冲) | 成交额持久性 |

---

## 四、开发分期计划

### Phase 1：最小可用版本（MVP）· 预计 2-3 天

> 目标：跑通核心链路，能在 CodeMaker 中被个股审计引擎调用

| 任务 | 具体内容 | 产出 |
|---|---|---|
| P1-1 | 初始化项目骨架：FastMCP + AKShare | `server.py` 基础框架 |
| P1-2 | 实现 `stock_realtime_quote` | 第 1 个可调用工具 |
| P1-3 | 实现 `stock_technical_indicator` | 技术指标拉取 |
| P1-4 | 实现 `index_realtime_quote` | 大盘环境数据 |
| P1-5 | 本地 stdio 模式测试通过 | CodeMaker 本地调通 |

**Phase 1 完成后：** 技术面 + 大盘环境两个维度可自动拉取，已能显著减少用户输入。

---

### Phase 2：基本面 + 事件面 · 预计 2-3 天

| 任务 | 具体内容 | 产出 |
|---|---|---|
| P2-1 | 实现 `stock_valuation` | PE/PB 分位数据 |
| P2-2 | 实现 `stock_profitability` | ROE/毛利率/营收增速 |
| P2-3 | 实现 `stock_financial_report_date` | 业绩窗口期 |
| P2-4 | 实现 `stock_unlock_schedule` | 解禁日历 |
| P2-5 | 实现 `stock_shareholder_change` | 股东+质押 |
| P2-6 | 实现 `stock_risk_event` | 风险事件 |
| P2-7 | 实现 `stock_institutional_flow` | 龙虎榜/北向 |

**Phase 2 完成后：** 6D 全维度数据均可自动拉取，F10 截图完全不再需要。

---

### Phase 3：云端部署 + 远程访问 · 预计 1-2 天

| 任务 | 具体内容 | 产出 |
|---|---|---|
| P3-1 | 编写 Dockerfile | 容器化 |
| P3-2 | 购买轻量云服务器 + 配置 | 线上环境就绪 |
| P3-3 | 部署 MCP Server（SSE 模式） | 公网可达 |
| P3-4 | 配置 Nginx 反向代理 + HTTPS | 安全传输 |
| P3-5 | 添加 Token 鉴权中间件 | 防止未授权访问 |
| P3-6 | 在 CodeMaker / Cursor / Claude 配置远程 MCP 连接 | 多平台验证 |

**Phase 3 完成后：** 任何设备、任何支持 MCP 的 AI 平台均可连接使用。

---

### Phase 4：生产加固 · 预计 1-2 天（可选）

| 任务 | 具体内容 | 产出 |
|---|---|---|
| P4-1 | 添加内存 TTL 缓存（行情 5s，基本面 4h） | 性能优化 |
| P4-2 | 添加 AKShare 请求限流（防封 IP） | 稳定性 |
| P4-3 | 数据源故障自动切换（AKShare → 东方财富 HTTP） | 高可用 |
| P4-4 | 添加日志 + 监控告警 | 运维可观测 |
| P4-5 | 编写 `sector_overview` 工具 | 板块引擎联动 |

---

## 五、你需要做的事情（按时间线）

### 🔴 开发前（准备阶段）· 约 30 分钟

| # | 事项 | 说明 | 参考 |
|---|---|---|---|
| 1 | **购买轻量云服务器** | 推荐腾讯云/阿里云轻量应用服务器，2C2G 即可 | 约 30-50 元/月 |
| 2 | **选择操作系统** | Ubuntu 22.04 LTS | — |
| 3 | **开放端口** | 在安全组中放行 443（HTTPS）+ 8000（MCP SSE） | — |
| 4 | **注册域名（可选）** | 如 `mcp.yourname.com`，方便记忆 | 非必须，用 IP 也行 |
| 5 | **准备 Python 环境** | 本地开发：Python 3.11+、pip | — |

### 🟡 开发中 · 你的参与点

| # | 事项 | 说明 |
|---|---|---|
| 1 | **确认数据字段需求** | 我列出的 12 个工具是否够用，是否有增删 |
| 2 | **验证 AKShare 字段可用性** | 部分冷门字段可能需要补充数据源 |
| 3 | **测试反馈** | 每个 Phase 完成后，在 CodeMaker 中实际调用测试 |

### 🟢 部署后 · 日常维护

| # | 事项 | 频率 | 工作量 |
|---|---|---|---|
| 1 | **续费云服务器** | 每月/每年 | 1 分钟 |
| 2 | **AKShare 版本升级** | 不定期（接口变动时） | `pip install --upgrade akshare` |
| 3 | **监控告警处理** | 偶发 | 检查日志，重启容器 |
| 4 | **MCP Client 配置** | 换设备时一次性 | 在新 AI 平台添加 MCP Server URL |

---

## 六、成本估算

| 项目 | 一次性 | 月度 | 备注 |
|---|---|---|---|
| 轻量云服务器（2C2G） | 0 | 30-50 元 | 腾讯云新用户首年更便宜 |
| 域名（可选） | 10-60 元/年 | — | `.com` / `.cn` |
| SSL 证书 | 0 | 0 | Let's Encrypt 免费 |
| AKShare 数据源 | 0 | 0 | 完全免费开源 |
| Tushare（备选） | 0 | 0 | 免费额度 500 次/日够用 |
| **合计** | **~50 元** | **~30-50 元/月** | — |

---

## 七、项目文件结构（预览）

```
stock-mcp-server/
├── server.py                    # MCP Server 入口
├── tools/
│   ├── __init__.py
│   ├── realtime.py              # 行情模块（4 个工具）
│   ├── fundamental.py           # 基本面模块（3 个工具）
│   ├── event.py                 # 事件面模块（4 个工具）
│   └── sector.py                # 板块联动模块（1 个工具）
├── datasource/
│   ├── __init__.py
│   ├── akshare_adapter.py       # AKShare 数据适配器
│   ├── eastmoney_adapter.py     # 东方财富 HTTP 备用
│   └── cache.py                 # TTL 缓存层
├── config/
│   ├── settings.py              # 服务器配置（端口、Token、缓存时间）
│   └── .env                     # 环境变量（Token、API Key）
├── Dockerfile                   # 容器化
├── docker-compose.yml           # 编排
├── nginx.conf                   # 反向代理配置
├── requirements.txt             # 依赖
└── README.md                    # 部署文档
```

---

## 八、MCP Client 配置示例（部署完成后）

### CodeMaker / Cursor (`mcp.json`)

```json
{
  "mcpServers": {
    "stock-data": {
      "type": "sse",
      "url": "https://mcp.yourname.com/sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "stock-data": {
      "type": "sse",
      "url": "https://mcp.yourname.com/sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}
```

> 配置一次后，该设备上所有对话自动拥有 A 股数据拉取能力。

---

## 九、风险与应对

| 风险 | 概率 | 影响 | 应对方案 |
|---|---|---|---|
| AKShare 接口变动 | 中 | 部分工具失效 | 数据源适配层隔离，切换备用源 |
| 云服务器宕机 | 低 | 数据不可用 | Skill 内建降级机制自动回退截图模式 |
| 交易所限流/封 IP | 低 | 请求失败 | 缓存 + 限流 + 多 IP 轮换 |
| MCP 协议升级 | 低 | 客户端不兼容 | FastMCP 框架跟进升级 |

---

## 十、里程碑时间线

```
Day 1-2:  ████████░░  Phase 1 (MVP: 行情+技术+大盘)
Day 3-5:  ████████░░  Phase 2 (基本面+事件面)
Day 5-6:  ████░░░░░░  Phase 3 (云端部署+多平台验证)
Day 7:    ██░░░░░░░░  Phase 4 (生产加固，可选)
          ──────────
          总计 ≈ 1 周（含测试）
```

---

## 下一步行动

当你准备好开始时，告诉我：
1. **"开始 Phase 1"** → 我直接开始写 `server.py` + 行情模块代码
2. **"先买服务器"** → 我给你具体的购买配置建议和初始化脚本
3. **"调整接口"** → 如果你想增删某些工具，先讨论再动手
