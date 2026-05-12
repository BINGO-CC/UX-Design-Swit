"""
A股数据 MCP Server - 事件面工具模块
提供: stock_unlock_schedule / stock_shareholder_change / stock_institutional_flow / stock_risk_event
"""
import akshare as ak
import pandas as pd
from typing import Optional
from datasource.akshare_adapter import _normalize_code, _rate_limit
from datasource.cache import event_cache, get_cached, set_cached


def tool_stock_unlock_schedule(code: str) -> dict:
    """
    获取个股解禁信息
    返回：未来90日解禁规模、解禁日期、占流通市值比例
    """
    cache_key = f"unlock:{code}"
    cached = get_cached(event_cache, cache_key)
    if cached:
        return cached

    code = _normalize_code(code)
    result = {"code": code, "unlocks_90d": [], "total_unlock_ratio_pct": 0}

    try:
        _rate_limit()
        df = ak.stock_restricted_release_queue_nm(symbol=code)
        if df is not None and not df.empty:
            # 筛选未来90天的解禁
            from datetime import datetime, timedelta
            today = datetime.now()
            future_90 = today + timedelta(days=90)

            for _, row in df.iterrows():
                try:
                    release_date = pd.to_datetime(row.get("解除限售日期", ""))
                    if today <= release_date <= future_90:
                        result["unlocks_90d"].append({
                            "date": str(release_date.date()),
                            "shares": str(row.get("解禁数量(万股)", "")),
                            "ratio": str(row.get("占总股本比例(%)", "")),
                        })
                except:
                    continue

            # 汇总占比
            total_ratio = sum(
                float(u.get("ratio", 0)) for u in result["unlocks_90d"]
                if u.get("ratio", "").replace(".", "").isdigit()
            )
            result["total_unlock_ratio_pct"] = round(total_ratio, 2)
            result["pressure_level"] = (
                "重大抛压" if total_ratio > 15
                else "显著抛压" if total_ratio > 5
                else "轻微/无"
            )
        else:
            result["pressure_level"] = "无数据"

    except Exception as e:
        result["error"] = str(e)
        result["pressure_level"] = "查询失败"

    if "error" not in result:
        set_cached(event_cache, cache_key, result)
    return result


def tool_stock_shareholder_change(code: str) -> dict:
    """
    获取大股东增减持及质押信息
    返回：近30日增减持记录、大股东质押率
    """
    cache_key = f"shareholder:{code}"
    cached = get_cached(event_cache, cache_key)
    if cached:
        return cached

    code = _normalize_code(code)
    result = {"code": code}

    # 股东增减持
    try:
        _rate_limit()
        try:
            jian_df = ak.stock_share_change_em(symbol=code)
            if jian_df is not None and not jian_df.empty:
                recent = jian_df.head(5)  # 最近5条
                changes = []
                for _, row in recent.iterrows():
                    changes.append({
                        "date": str(row.get("公告日", "")),
                        "shareholder": str(row.get("股东名称", "")),
                        "direction": str(row.get("变动方向", "")),
                        "change_shares_wan": str(row.get("变动股本(万)", "")),
                    })
                result["shareholder_changes"] = changes
            else:
                result["shareholder_changes"] = []
        except:
            result["shareholder_changes"] = []
    except:
        result["shareholder_changes"] = []

    # 质押信息
    try:
        _rate_limit()
        try:
            pledge_df = ak.stock_zh_a_pledge(symbol=code)
            if pledge_df is not None and not pledge_df.empty:
                latest = pledge_df.iloc[0]
                result["pledge_ratio_pct"] = _safe_float(latest.get("质押比例(%)", 0))
                result["pledge_risk"] = (
                    "质押爆仓风险" if result.get("pledge_ratio_pct", 0) and result["pledge_ratio_pct"] > 60
                    else "较高质押" if result.get("pledge_ratio_pct", 0) and result["pledge_ratio_pct"] > 40
                    else "正常"
                )
            else:
                result["pledge_ratio_pct"] = None
                result["pledge_risk"] = "无数据"
        except:
            result["pledge_ratio_pct"] = None
            result["pledge_risk"] = "查询失败"
    except:
        result["pledge_ratio_pct"] = None
        result["pledge_risk"] = "查询失败"

    if "error" not in result:
        set_cached(event_cache, cache_key, result)
    return result


def tool_stock_institutional_flow(code: str) -> dict:
    """
    获取机构资金流向信息
    返回：龙虎榜席位、北向持股变动(近5日)、融资余额变动
    """
    cache_key = f"institutional:{code}"
    cached = get_cached(event_cache, cache_key)
    if cached:
        return cached

    code = _normalize_code(code)
    result = {"code": code}

    # 龙虎榜
    try:
        _rate_limit()
        try:
            lhb_df = ak.stock_lhb_detail_em(symbol=code)
            if lhb_df is not None and not lhb_df.empty:
                result["dragon_tiger"] = {
                    "has_recent": True,
                    "recent_count": len(lhb_df.head(3)),
                    "note": "近期上榜，详见龙虎榜数据",
                }
            else:
                result["dragon_tiger"] = {"has_recent": False, "note": "近期未上龙虎榜"}
        except:
            result["dragon_tiger"] = {"has_recent": False, "note": "查询异常"}
    except:
        result["dragon_tiger"] = {"has_recent": False, "note": "查询失败"}

    # 融资融券
    try:
        _rate_limit()
        try:
            margin_df = ak.stock_margin_detail_szse(symbol=code) if code.startswith(("0", "3")) else None
            if margin_df is None:
                margin_df = ak.stock_margin_detail_sse(symbol=code)
            if margin_df is not None and not margin_df.empty:
                recent_5 = margin_df.tail(5)
                if "融资余额" in recent_5.columns:
                    start_val = float(recent_5.iloc[0]["融资余额"])
                    end_val = float(recent_5.iloc[-1]["融资余额"])
                    change = end_val - start_val
                    result["margin_balance"] = {
                        "latest_yi": round(end_val / 1e8, 2),
                        "5d_change_yi": round(change / 1e8, 2),
                        "trend": "净流入" if change > 0 else "净流出",
                    }
                else:
                    result["margin_balance"] = {"note": "无融资余额数据"}
            else:
                result["margin_balance"] = {"note": "非两融标的或查询失败"}
        except:
            result["margin_balance"] = {"note": "查询失败"}
    except:
        result["margin_balance"] = {"note": "查询失败"}

    if "error" not in result:
        set_cached(event_cache, cache_key, result)
    return result


def tool_stock_risk_event(code: str) -> dict:
    """
    获取个股风险事件
    返回：ST状态、问询函/立案、重组停牌预期、业绩预告类型
    """
    cache_key = f"risk:{code}"
    cached = get_cached(event_cache, cache_key)
    if cached:
        return cached

    code = _normalize_code(code)
    result = {"code": code, "risk_flags": []}

    try:
        # 检查 ST 状态
        _rate_limit()
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == code]
        if not row.empty:
            name = str(row.iloc[0].get("名称", ""))
            if "ST" in name or "*ST" in name:
                result["risk_flags"].append("ST/退市风险警示")
                result["is_st"] = True
            else:
                result["is_st"] = False
            result["stock_name"] = name
        else:
            result["is_st"] = False
            result["stock_name"] = "未知"

        # 风险等级汇总
        if result["risk_flags"]:
            result["risk_level"] = "🔴 直接禁入"
            result["action"] = "事件面命中禁入项，禁止买入/建议清仓"
        else:
            result["risk_level"] = "🟢 暂无重大风险事件"
            result["action"] = "无强制约束"

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(event_cache, cache_key, result)
    return result


def _safe_float(val) -> Optional[float]:
    """安全转换为 float"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return None
