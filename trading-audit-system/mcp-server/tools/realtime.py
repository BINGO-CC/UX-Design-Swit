"""
A股数据 MCP Server - 实时行情工具模块
提供: stock_realtime_quote / stock_technical_indicator / stock_kline_data / index_realtime_quote
"""
from datasource.akshare_adapter import (
    get_realtime_quote,
    calculate_technical_indicators,
    get_kline_data,
    get_index_quote,
)
from datasource.cache import (
    realtime_cache,
    technical_cache,
    get_cached,
    set_cached,
    preloader,
)


def tool_stock_realtime_quote(code: str) -> dict:
    """
    获取个股实时行情数据
    返回：现价、涨跌幅、成交额、换手率、量比、振幅等
    """
    cache_key = f"realtime:{code}"
    cached = get_cached(realtime_cache, cache_key)
    if cached:
        cached["_cache_hit"] = True
        return cached

    result = get_realtime_quote(code)
    if result and "error" not in result:
        set_cached(realtime_cache, cache_key, result)
        preloader.track(code)  # 加入后台预加载监控
    return result or {"error": f"未找到股票 {code}"}


def tool_stock_technical_indicator(code: str, period: str = "daily") -> dict:
    """
    获取个股技术指标
    返回：MA系列(5/10/20/60/120/250)、RSI_14、MACD(DIF/DEA/柱/金死叉)、VWAP、偏离度、均线排列状态
    """
    cache_key = f"technical:{code}:{period}"
    cached = get_cached(technical_cache, cache_key)
    if cached:
        return cached

    result = calculate_technical_indicators(code, period)
    if result and "error" not in result:
        set_cached(technical_cache, cache_key, result)
    return result or {"error": f"无法计算技术指标 {code}"}


def tool_stock_kline_data(code: str, period: str = "daily", count: int = 30) -> dict:
    """
    获取个股K线原始数据（近N根）
    返回：日期、开盘、收盘、最高、最低、成交量、成交额
    """
    df = get_kline_data(code, period, count=min(count, 120))
    if df is None or df.empty:
        return {"error": f"无法获取K线数据 {code}"}

    records = []
    for _, row in df.iterrows():
        records.append({
            "date": str(row.get("日期", "")),
            "open": float(row.get("开盘", 0)),
            "close": float(row.get("收盘", 0)),
            "high": float(row.get("最高", 0)),
            "low": float(row.get("最低", 0)),
            "volume": float(row.get("成交量", 0)),
            "turnover": float(row.get("成交额", 0)),
            "change_pct": float(row.get("涨跌幅", 0)),
        })
    return {"code": code, "period": period, "count": len(records), "klines": records}


def tool_index_realtime_quote(index_code: str = "000001") -> dict:
    """
    获取大盘指数行情及环境判定
    返回：指数现价、MA60、MACD状态、环境判定（健康/中性/系统级降级）
    支持代码：000001(上证) / 399001(深证) / 399006(创业板)
    """
    cache_key = f"index:{index_code}"
    cached = get_cached(realtime_cache, cache_key)
    if cached:
        return cached

    result = get_index_quote(index_code)
    if result and "error" not in result:
        set_cached(realtime_cache, cache_key, result)
    return result or {"error": f"无法获取指数数据 {index_code}"}
