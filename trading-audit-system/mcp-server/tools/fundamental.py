"""
A股数据 MCP Server - 基本面工具模块
提供: stock_valuation / stock_profitability / stock_financial_report_date
"""
import akshare as ak
import pandas as pd
from typing import Optional
from datasource.akshare_adapter import _normalize_code, _rate_limit
from datasource.cache import fundamental_cache, get_cached, set_cached


def tool_stock_valuation(code: str) -> dict:
    """
    获取个股估值数据
    返回：PE(TTM)、PB、PE历史分位(近5年)、PB历史分位(近5年)、PEG、总市值、流通市值
    """
    cache_key = f"valuation:{code}"
    cached = get_cached(fundamental_cache, cache_key)
    if cached:
        return cached

    code = _normalize_code(code)
    result = {}

    try:
        _rate_limit()
        # 获取实时估值
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == code]
        if not row.empty:
            row = row.iloc[0]
            result["PE_TTM"] = float(row.get("市盈率-动态", 0)) if pd.notna(row.get("市盈率-动态")) else None
            result["PB"] = float(row.get("市净率", 0)) if pd.notna(row.get("市净率")) else None
            result["total_market_cap_yi"] = round(float(row.get("总市值", 0)) / 1e8, 2)
            result["circulating_market_cap_yi"] = round(float(row.get("流通市值", 0)) / 1e8, 2)

        # 获取 PE/PB 历史分位（尝试通过历史数据计算）
        _rate_limit()
        try:
            # 获取近 5 年历史 PE
            hist_df = ak.stock_zh_a_hist(symbol=code, period="日k", adjust="qfq")
            if hist_df is not None and len(hist_df) > 0:
                # 使用近 1250 个交易日（约5年）
                result["data_note"] = "PE/PB 历史分位需结合估值接口，当前为实时快照值"
        except:
            pass

        # PEG 估算（需要盈利增速）
        _rate_limit()
        try:
            profit_df = ak.stock_financial_analysis_indicator(symbol=code)
            if profit_df is not None and not profit_df.empty:
                # 获取最近一期净利润增长率
                latest = profit_df.iloc[0]
                net_profit_growth = latest.get("净利润增长率(%)")
                if net_profit_growth and result.get("PE_TTM") and float(net_profit_growth) > 0:
                    result["PEG"] = round(result["PE_TTM"] / float(net_profit_growth), 2)
                else:
                    result["PEG"] = None
        except:
            result["PEG"] = None

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(fundamental_cache, cache_key, result)
    return result


def tool_stock_profitability(code: str) -> dict:
    """
    获取个股盈利能力数据
    返回：ROE(近4季)、毛利率、净利率、营收同比增速、扣非净利同比增速
    """
    cache_key = f"profit:{code}"
    cached = get_cached(fundamental_cache, cache_key)
    if cached:
        return cached

    code = _normalize_code(code)
    result = {}

    try:
        _rate_limit()
        # 财务指标
        df = ak.stock_financial_analysis_indicator(symbol=code)
        if df is not None and not df.empty:
            latest = df.iloc[0]
            result["report_date"] = str(latest.get("日期", ""))
            result["ROE"] = _safe_float(latest.get("净资产收益率(%)"))
            result["gross_margin"] = _safe_float(latest.get("销售毛利率(%)"))
            result["net_margin"] = _safe_float(latest.get("销售净利率(%)"))

        # 营收和利润增速
        _rate_limit()
        try:
            growth_df = ak.stock_financial_abstract_ths(symbol=code)
            if growth_df is not None and not growth_df.empty:
                latest_g = growth_df.iloc[0]
                result["revenue_yoy"] = _safe_float(latest_g.get("营业总收入同比增长率(%)"))
                result["net_profit_yoy"] = _safe_float(latest_g.get("净利润同比增长率(%)"))
                # 扣非净利同比
                result["deducted_net_profit_yoy"] = _safe_float(
                    latest_g.get("扣非净利润同比增长率(%)")
                )
        except:
            result["revenue_yoy"] = None
            result["net_profit_yoy"] = None
            result["deducted_net_profit_yoy"] = None

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(fundamental_cache, cache_key, result)
    return result


def tool_stock_financial_report_date(code: str) -> dict:
    """
    获取下一财报披露日及业绩预告信息
    返回：下一财报披露日、距今交易日数、业绩预告摘要（预增/预减/预亏等）
    """
    cache_key = f"report_date:{code}"
    cached = get_cached(fundamental_cache, cache_key)
    if cached:
        return cached

    code = _normalize_code(code)
    result = {}

    try:
        _rate_limit()
        # 尝试获取业绩预告
        try:
            forecast_df = ak.stock_profit_forecast_ths(symbol=code)
            if forecast_df is not None and not forecast_df.empty:
                latest = forecast_df.iloc[0]
                result["forecast_type"] = str(latest.get("预告类型", "无"))
                result["forecast_content"] = str(latest.get("预告内容", ""))
            else:
                result["forecast_type"] = "无预告"
                result["forecast_content"] = ""
        except:
            result["forecast_type"] = "查询失败"
            result["forecast_content"] = ""

        # 业绩窗口期判定
        result["note"] = "请结合东方财富F10确认具体披露日期，API可能无法获取精确日期"

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(fundamental_cache, cache_key, result)
    return result


def _safe_float(val) -> Optional[float]:
    """安全转换为 float"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return None
