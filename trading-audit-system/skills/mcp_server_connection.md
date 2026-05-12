# A股数据 MCP Server · 连接配置

> 本文件记录 MCP Server 的连接信息，在任何新设备/AI平台上配置时参考。

---

## 服务器信息

| 项目 | 值 |
|---|---|
| 公网 IP | `124.221.128.190` |
| 端口 | `8000` |
| 传输协议 | SSE (Server-Sent Events) |
| 连接地址 | `http://124.221.128.190:8000/sse` |
| Token | `f9df73198415a1a83487d5212afec2e1e65c4b799fa0f665fb8b1a7cf7887db3` |
| 服务器地域 | 腾讯云 · 上海二区 |
| 到期时间 | 2027-05-12 |

---

## 各平台配置方法

### CodeMaker

文件路径：项目根目录 `.codemaker/mcp.json` 或全局 MCP 配置

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

---

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

---

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

---

### 其他支持 MCP 的平台

通用格式（参考各平台文档找到 MCP 配置入口）：

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

---

## 可用工具清单（17 个）

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

## 配套 Skill 文件

| 文件 | 用途 |
|---|---|
| `trading_audit_engine_v2.md` | 个股审计引擎（持仓/准入/观察三模式） |
| `sector_audit_engine_v2.md` | 板块审计引擎（确定性引擎） |

---

## 故障排查

| 问题 | 解决方法 |
|---|---|
| AI 平台提示连接不上 | 检查服务器是否运行：`ssh ubuntu@124.221.128.190` → `docker compose ps` |
| 工具调用返回错误 | 可能是 AKShare 接口变动，SSH 进去执行 `docker compose restart` |
| Token 忘了 | SSH 进去执行 `cat /opt/stock-mcp-server/.env` 查看 |
| 服务器到期 | 腾讯云控制台续费（已开自动续费则无需操作） |

---

## 快速恢复（服务器挂了/重启后）

```bash
ssh ubuntu@124.221.128.190
sudo su
cd /opt/stock-mcp-server
docker compose up -d
```
