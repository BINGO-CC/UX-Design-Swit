"""
A股数据 MCP Server · 主入口
============================
为「个股审计引擎 v2.2+」及「板块审计引擎 v2.1」提供自动化数据拉取能力。
支持 stdio（本地）和 SSE（远程）两种传输模式。

启动方式:
  本地模式: python server.py
  远程模式: python server.py --transport sse --port 8000
"""
import sys
import os
import json
import argparse

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from config.settings import SERVER_NAME, SERVER_HOST, SERVER_PORT

# 初始化 MCP Server
mcp = FastMCP(
    SERVER_NAME,
    host="0.0.0.0",
    port=8000,
    instructions="""
    A股数据 MCP Server - 为交易审计双引擎（个股审计 + 板块审计）提供实时数据。
    支持 17 个工具，覆盖个股6D审计 + 板块确定性引擎全维度数据需求。
    个股模块: realtime_quote / technical_indicator / kline_data / valuation / profitability / financial_report_date / unlock_schedule / shareholder_change / institutional_flow / risk_event
    板块模块: sector_overview / sector_realtime_quote / sector_ratio_calc / sector_resonance / sector_leaders / sector_turnover_history
    大盘模块: index_realtime_quote
    """,
)


# ============================================================
# 模块 1：实时行情 (Realtime)
# ============================================================

@mcp.tool()
def stock_realtime_quote(code: str) -> str:
    """
    获取A股个股实时行情数据。

    参数:
        code: 股票代码（如 600519、000001、300750）

    返回:
        现价、涨跌幅、成交额、换手率、量比、振幅、市盈率、市净率、市值等
    """
    from tools.realtime import tool_stock_realtime_quote
    result = tool_stock_realtime_quote(code)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def stock_technical_indicator(code: str, period: str = "daily") -> str:
    """
    获取A股个股技术分析指标。

    参数:
        code: 股票代码（如 600519、000001、300750）
        period: K线周期，可选 daily(日线) / weekly(周线) / monthly(月线)，默认 daily

    返回:
        MA均线系列(5/10/20/60/120/250)、RSI_14、MACD(DIF/DEA/柱状体/金死叉状态)、
        VWAP、均线排列状态、MA250偏离度、MA20偏离度、近5日量比
    """
    from tools.realtime import tool_stock_technical_indicator
    result = tool_stock_technical_indicator(code, period)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def stock_kline_data(code: str, period: str = "daily", count: int = 30) -> str:
    """
    获取A股个股K线原始OHLCV数据。

    参数:
        code: 股票代码（如 600519、000001、300750）
        period: K线周期，可选 daily(日线) / weekly(周线) / monthly(月线)，默认 daily
        count: 获取K线根数，默认30，最大120

    返回:
        近N根K线的日期、开盘、收盘、最高、最低、成交量、成交额、涨跌幅
    """
    from tools.realtime import tool_stock_kline_data
    result = tool_stock_kline_data(code, period, count)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def index_realtime_quote(index_code: str = "000001") -> str:
    """
    获取大盘指数行情及环境判定（用于审计引擎协议1.5大盘环境过滤器）。

    参数:
        index_code: 指数代码，000001(上证指数) / 399001(深证成指) / 399006(创业板指)

    返回:
        指数现价、MA60、MACD状态(金叉/死叉+天数)、环境判定(健康/中性/系统级降级)
    """
    from tools.realtime import tool_index_realtime_quote
    result = tool_index_realtime_quote(index_code)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# 模块 2：基本面 (Fundamental)
# ============================================================

@mcp.tool()
def stock_valuation(code: str) -> str:
    """
    获取A股个股估值数据。

    参数:
        code: 股票代码（如 600519、000001、300750）

    返回:
        PE(TTM)、PB、PE历史分位(近5年)、PB历史分位(近5年)、PEG、总市值、流通市值
    """
    from tools.fundamental import tool_stock_valuation
    result = tool_stock_valuation(code)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def stock_profitability(code: str) -> str:
    """
    获取A股个股盈利能力指标。

    参数:
        code: 股票代码（如 600519、000001、300750）

    返回:
        ROE(%)、毛利率(%)、净利率(%)、营收同比增速(%)、扣非净利同比增速(%)
    """
    from tools.fundamental import tool_stock_profitability
    result = tool_stock_profitability(code)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def stock_financial_report_date(code: str) -> str:
    """
    获取个股业绩预告及财报披露日信息（用于业绩窗口期保护判定）。

    参数:
        code: 股票代码（如 600519、000001、300750）

    返回:
        业绩预告类型(预增/预减/预亏/无)、预告内容摘要
    """
    from tools.fundamental import tool_stock_financial_report_date
    result = tool_stock_financial_report_date(code)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# 模块 3：事件面 (Event)
# ============================================================

@mcp.tool()
def stock_unlock_schedule(code: str) -> str:
    """
    获取个股未来90日限售解禁信息。

    参数:
        code: 股票代码（如 600519、000001、300750）

    返回:
        未来90日解禁列表(日期/数量/比例)、总解禁占比、抛压等级判定
    """
    from tools.event import tool_stock_unlock_schedule
    result = tool_stock_unlock_schedule(code)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def stock_shareholder_change(code: str) -> str:
    """
    获取大股东增减持及股权质押信息。

    参数:
        code: 股票代码（如 600519、000001、300750）

    返回:
        近期股东增减持记录、大股东质押率(%)、质押风险等级
    """
    from tools.event import tool_stock_shareholder_change
    result = tool_stock_shareholder_change(code)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def stock_institutional_flow(code: str) -> str:
    """
    获取机构资金流向（龙虎榜、融资融券）。

    参数:
        code: 股票代码（如 600519、000001、300750）

    返回:
        龙虎榜近期上榜情况、融资余额(亿)及近5日变动趋势
    """
    from tools.event import tool_stock_institutional_flow
    result = tool_stock_institutional_flow(code)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def stock_risk_event(code: str) -> str:
    """
    获取个股风险事件扫描（ST/问询函/立案/重组等）。

    参数:
        code: 股票代码（如 600519、000001、300750）

    返回:
        ST状态、风险标记列表、风险等级(禁入/正常)、建议动作
    """
    from tools.event import tool_stock_risk_event
    result = tool_stock_risk_event(code)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# 模块 4：板块联动 (Sector)
# ============================================================

@mcp.tool()
def sector_overview(code: str) -> str:
    """
    获取个股所属板块概况及当日热门板块。

    参数:
        code: 股票代码（如 600519、000001、300750）

    返回:
        个股名称、所属板块信息、当日行业板块涨幅前10
    """
    from tools.sector import tool_sector_overview
    result = tool_sector_overview(code)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def sector_realtime_quote(sector_name: str) -> str:
    """
    获取指定行业/概念板块的实时行情数据。

    参数:
        sector_name: 板块名称（如 "半导体"、"光伏"、"白酒"、"人工智能"）

    返回:
        板块涨跌幅、成交额(亿)、上涨/下跌家数、涨停/跌停家数
    """
    from tools.sector import tool_sector_realtime_quote
    result = tool_sector_realtime_quote(sector_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def sector_ratio_calc(sector_name: str) -> str:
    """
    计算板块 Ratio（吸金强度）= 板块当日成交额 / 全市场总成交额 × 100%。
    用于板块审计引擎的流量持久性判定。

    参数:
        sector_name: 板块名称（如 "半导体"、"光伏"、"白酒"）

    返回:
        板块成交额(亿)、全市场成交额(亿)、Ratio(%)、Ratio等级判定
        等级: >30%历史峰值 / 20-30%高度集中 / 15-20%确定性吸金 / 8-15%观察期 / <8%低关注
    """
    from tools.sector import tool_sector_ratio_calc
    result = tool_sector_ratio_calc(sector_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def sector_resonance(sector_name: str) -> str:
    """
    计算板块共振度（板块内站上MA20的个股占比）。
    共振度 = 站上MA20个股数 / 板块成分股总数 × 100%

    参数:
        sector_name: 板块名称（如 "半导体"、"光伏"、"白酒"）

    返回:
        成分股总数、采样数、站上MA20家数、共振度(%)、共振度等级判定
        等级: ≥60%确定性共振 / 40-60%观察期 / <40%伪共振
    """
    from tools.sector import tool_sector_resonance
    result = tool_sector_resonance(sector_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def sector_leaders(sector_name: str) -> str:
    """
    识别板块龙头股并判定健康度。
    龙头标准: 涨幅前5 + 近5日新高≥3次 + 换手率∈[10%,25%]

    参数:
        sector_name: 板块名称（如 "半导体"、"光伏"、"白酒"）

    返回:
        龙头候选列表(代码/名称/涨幅/换手率/近5日新高次数/健康度)、健康龙头数量、总体健康度判定
    """
    from tools.sector import tool_sector_leaders
    result = tool_sector_leaders(sector_name)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def sector_turnover_history(sector_name: str, days: int = 5) -> str:
    """
    获取板块近N日成交额序列，用于流量持久性判定。
    自动计算成交额重心变化和持久性等级。

    参数:
        sector_name: 板块名称（如 "半导体"、"光伏"、"白酒"）
        days: 获取天数，默认5日

    返回:
        每日成交额(亿)序列、近3日重心(D-2/D-1/D0)、重心比值(D0/D-2)、持久性判定
        判定: 🟢确定性(温和上移) / 🟡观察期(波动) / 🔴阶段性脉冲(次日萎缩≥40%)
    """
    from tools.sector import tool_sector_turnover_history
    result = tool_sector_turnover_history(sector_name, days)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# 服务器启动
# ============================================================

if __name__ == "__main__":
    # 启动后台预加载
    from datasource.cache import preloader
    preloader.start()

    parser = argparse.ArgumentParser(description="A股数据 MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="传输模式: stdio(本地) 或 sse(远程)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=SERVER_PORT,
        help=f"SSE 模式端口号 (默认 {SERVER_PORT})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=SERVER_HOST,
        help=f"SSE 模式监听地址 (默认 {SERVER_HOST})",
    )

    args = parser.parse_args()

    if args.transport == "sse":
        print(f"🚀 A股数据 MCP Server 启动 (SSE 模式)")
        print(f"   地址: http://0.0.0.0:8000/sse")
        print(f"   工具数: 17")
        mcp.run(transport="sse")
    else:
        print("🚀 A股数据 MCP Server 启动 (stdio 模式)", file=sys.stderr)
        mcp.run(transport="stdio")
