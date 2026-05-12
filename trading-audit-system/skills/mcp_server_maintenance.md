# A股数据 MCP Server · 维护与扩展手册

> 本文档定义 MCP Server 的日常维护、故障恢复、工具扩展的标准操作流程。
> 适用场景：在任何 AI 平台（CodeMaker / CODX / Claude / Cursor）上指导 AI 协助你完成维护操作。
> 前置依赖：`mcp_server_connection.md`（连接信息）

---

## 一、服务器基本信息

| 项目 | 值 |
|---|---|
| IP | `124.221.128.190` |
| 登录用户 | `ubuntu`（需 `sudo su` 切 root） |
| 代码目录 | `/opt/stock-mcp-server/` |
| 容器名 | `stock-mcp-server` |
| Docker 编排 | `docker-compose.yml` |
| 运行端口 | `8000` |

---

## 二、日常运维命令速查

### 登录服务器

```bash
ssh ubuntu@124.221.128.190
sudo su
cd /opt/stock-mcp-server
```

### 查看状态

```bash
docker compose ps                    # 查看容器是否运行
docker compose logs --tail 50        # 查看最近50行日志
docker compose logs -f               # 实时跟踪日志（Ctrl+C 退出）
```

### 重启服务

```bash
docker compose restart               # 软重启（不重建镜像）
```

### 重建服务（代码改动后）

```bash
docker compose up -d --build         # 重新构建镜像并启动
```

### 停止服务

```bash
docker compose down                  # 停止并移除容器
```

### 查看 Token

```bash
cat /opt/stock-mcp-server/.env       # 查看所有环境变量含 Token
```

---

## 三、工具扩展标准流程

### 3.1 需求描述模板

当你需要 AI 帮你新增工具时，使用以下模板描述需求：

```
【MCP 工具扩展需求】

服务器: 124.221.128.190
代码目录: /opt/stock-mcp-server/
技术栈: Python 3.11 + FastMCP + AKShare

需求描述:
  我需要新增一个工具: [工具名称]
  功能: [具体要获取什么数据]
  入参: [需要什么输入参数]
  返回: [期望返回什么字段]
  数据源: [AKShare 的哪个接口 / 或让 AI 自行查找]

请输出:
  1. tools/ 目录下的新增/修改代码
  2. server.py 中的 @mcp.tool() 注册代码
  3. 服务器部署命令
```

### 3.2 代码结构规范

新增工具必须遵循以下结构：

```
tools/
├── realtime.py       # 行情模块 → stock_realtime_quote / stock_technical_indicator / stock_kline_data
├── fundamental.py    # 基本面   → stock_valuation / stock_profitability / stock_financial_report_date
├── event.py          # 事件面   → stock_unlock_schedule / stock_shareholder_change / stock_institutional_flow / stock_risk_event
└── sector.py         # 板块     → sector_overview / sector_realtime_quote / sector_ratio_calc / sector_resonance / sector_leaders / sector_turnover_history
```

**新工具归属规则：**

| 数据类型 | 放入文件 |
|---|---|
| 实时行情/技术指标类 | `tools/realtime.py` |
| 财务/估值/盈利类 | `tools/fundamental.py` |
| 事件/风险/资金流类 | `tools/event.py` |
| 板块/行业/概念类 | `tools/sector.py` |
| 全新类别 | 新建 `tools/新模块名.py` |

### 3.3 单个工具代码模板

```python
# 在对应 tools/xxx.py 文件中新增:

def tool_新工具名(参数: str) -> dict:
    """
    工具功能描述
    """
    cache_key = f"前缀:{参数}"
    cached = get_cached(对应缓存实例, cache_key)
    if cached:
        return cached

    code = _normalize_code(参数)  # 如果是股票代码
    result = {}

    try:
        _rate_limit()
        # 调用 AKShare 接口
        df = ak.对应接口函数(symbol=code)
        # 处理数据...
        result["字段名"] = 值
    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(对应缓存实例, cache_key, result)
    return result
```

```python
# 在 server.py 中注册:

@mcp.tool()
def 新工具名(参数: str) -> str:
    """
    工具功能描述（这段描述会展示给 AI，写清楚入参和返回值）

    参数:
        参数名: 参数说明

    返回:
        返回内容描述
    """
    from tools.对应模块 import tool_新工具名
    result = tool_新工具名(参数)
    return json.dumps(result, ensure_ascii=False, indent=2)
```

### 3.4 部署新工具

```bash
# SSH 进服务器后
cd /opt/stock-mcp-server

# 方式 A: 直接编辑文件（适合小改动）
nano tools/对应模块.py       # 添加函数
nano server.py              # 注册工具

# 方式 B: 本地修改后上传（适合大改动）
# 在本地电脑:
scp tools/对应模块.py ubuntu@124.221.128.190:/opt/stock-mcp-server/tools/
scp server.py ubuntu@124.221.128.190:/opt/stock-mcp-server/

# 重建容器
docker compose up -d --build

# 验证
docker compose ps            # 确认 running
docker compose logs --tail 20  # 确认无报错
```

### 3.5 新工具生效验证

重建成功后，**不需要修改任何客户端配置**。MCP 协议会自动暴露新工具给所有已连接的 AI 平台。

验证方法：在 AI 对话中问：
```
请列出 stock-data MCP Server 当前可用的所有工具
```

---

## 四、故障排查

### 4.1 常见问题

| 症状 | 原因 | 解决 |
|---|---|---|
| AI 提示"无法连接 MCP" | 容器挂了 / 端口没放行 | SSH 进去 `docker compose up -d` |
| 工具返回 `{"error": "..."}` | AKShare 接口变动 / 网络问题 | 查日志 → 更新 AKShare → 重建 |
| 构建失败 | 代码语法错误 / 依赖冲突 | `docker compose logs` 查错误 → 修改代码 → 重新 `up --build` |
| 数据不更新（返回旧值） | 缓存未过期 | 等 TTL 过期，或重启容器清缓存 |
| 新工具没出现 | 未在 server.py 注册 / 构建未成功 | 检查 server.py → 重建 |

### 4.2 查日志定位错误

```bash
# 查最近错误
docker compose logs --tail 100 | grep -i error

# 实时观察（触发一次调用后看输出）
docker compose logs -f
```

### 4.3 AKShare 升级

```bash
# 进入容器内部
docker compose exec stock-mcp bash
pip install --upgrade akshare
exit

# 或者直接重建（更干净）
# 先修改 requirements.txt 中的版本号，再:
docker compose up -d --build
```

---

## 五、数据源扩展指南

### 5.1 AKShare 可用接口参考

当你想增加新数据维度时，参考 AKShare 文档找到对应接口：

| 数据需求 | AKShare 函数 | 备注 |
|---|---|---|
| 北向资金持仓 | `ak.stock_hsgt_individual_em()` | 单只个股北向持仓 |
| 资金流向 | `ak.stock_individual_fund_flow()` | 主力/散户资金流 |
| 机构持仓 | `ak.stock_institute_hold_em()` | 基金/社保持仓 |
| 行业对比 | `ak.stock_board_industry_hist_em()` | 板块历史数据 |
| 可转债 | `ak.bond_cb_jsl()` | 可转债数据 |
| 港股通 | `ak.stock_hk_spot_em()` | 港股实时行情 |
| ETF 行情 | `ak.fund_etf_spot_em()` | ETF 实时数据 |
| 宏观经济 | `ak.macro_china_gdp()` | GDP/CPI/PMI |

> 完整文档：https://akshare.akfamily.xyz/

### 5.2 添加全新数据源（非 AKShare）

如需接入 Tushare、东方财富 HTTP、或其他 API：

1. 在 `datasource/` 目录新建适配器文件（如 `tushare_adapter.py`）
2. 在对应 tools 文件中 import 并调用
3. 若需 API Key，添加到 `.env` 文件中
4. 重建容器

---

## 六、版本管理（可选）

### 6.1 Git 初始化（一次性）

```bash
cd /opt/stock-mcp-server
git init
git add .
git commit -m "初始版本: 17个工具"

# 关联远程仓库（可选）
git remote add origin https://gitee.com/你的用户名/stock-mcp-server.git
git push -u origin main
```

### 6.2 更新流程（有 Git 后）

```bash
# 本地修改 → push → 服务器 pull
cd /opt/stock-mcp-server
git pull origin main
docker compose up -d --build
```

---

## 七、安全注意事项

| 事项 | 要求 |
|---|---|
| Token | 不要泄露给他人，不要上传到公开仓库 |
| SSH 密码 | 建议后续改为密钥登录 |
| .env 文件 | 加入 `.gitignore`，不要提交到 Git |
| 服务器 | 定期执行 `sudo apt update && sudo apt upgrade` |
