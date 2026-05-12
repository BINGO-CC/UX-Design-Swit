"""
A股数据 MCP Server - 板块审计工具模块（扩展版）
提供:
  - sector_overview         → 个股所属板块概况
  - sector_realtime_quote   → 板块实时行情
  - sector_ratio_calc       → Ratio（吸金强度）计算
  - sector_resonance        → 共振度计算
  - sector_leaders          → 龙头识别 + 健康度判定
  - sector_turnover_history → 板块近N日成交额序列
"""
import akshare as ak
import pandas as pd
import numpy as np
from typing import Optional
from datasource.akshare_adapter import _normalize_code, _rate_limit, get_kline_data
from datasource.cache import realtime_cache, technical_cache, get_cached, set_cached


# ============================================================
# 原有工具：个股所属板块概况
# ============================================================

def tool_sector_overview(code: str) -> dict:
    """
    获取个股所属板块信息
    返回：所属行业板块、板块涨跌幅、当日行业板块涨幅前10
    """
    cache_key = f"sector:{code}"
    cached = get_cached(realtime_cache, cache_key)
    if cached:
        return cached

    code = _normalize_code(code)
    result = {"code": code}

    try:
        _rate_limit()
        spot_df = ak.stock_zh_a_spot_em()
        stock_row = spot_df[spot_df["代码"] == code]
        if not stock_row.empty:
            result["stock_name"] = str(stock_row.iloc[0].get("名称", ""))

        # 获取行业板块涨幅排行
        _rate_limit()
        board_df = ak.stock_board_industry_name_em()
        if board_df is not None and not board_df.empty:
            top_sectors = board_df.head(10)
            result["hot_sectors"] = [
                {
                    "name": str(row.get("板块名称", "")),
                    "change_pct": float(row.get("涨跌幅", 0)) if pd.notna(row.get("涨跌幅")) else 0,
                    "turnover_yi": round(float(row.get("成交额", 0)) / 1e8, 2) if pd.notna(row.get("成交额")) else 0,
                }
                for _, row in top_sectors.iterrows()
            ]
        else:
            result["hot_sectors"] = []

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(realtime_cache, cache_key, result)
    return result


# ============================================================
# 新增工具：板块实时行情
# ============================================================

def tool_sector_realtime_quote(sector_name: str) -> dict:
    """
    获取指定板块实时行情
    返回：板块涨跌幅、成交额(亿)、涨停家数、跌停家数、上涨/下跌家数
    """
    cache_key = f"sector_quote:{sector_name}"
    cached = get_cached(realtime_cache, cache_key)
    if cached:
        return cached

    result = {"sector_name": sector_name}

    try:
        _rate_limit()
        # 获取行业板块列表
        board_df = ak.stock_board_industry_name_em()
        if board_df is None or board_df.empty:
            return {"error": "无法获取板块列表"}

        # 模糊匹配板块名称
        matched = board_df[board_df["板块名称"].str.contains(sector_name, na=False)]
        if matched.empty:
            # 尝试概念板块
            _rate_limit()
            concept_df = ak.stock_board_concept_name_em()
            if concept_df is not None:
                matched = concept_df[concept_df["板块名称"].str.contains(sector_name, na=False)]

        if matched.empty:
            return {"error": f"未找到匹配板块: {sector_name}", "available_hint": "请检查板块名称是否正确"}

        row = matched.iloc[0]
        result["matched_name"] = str(row.get("板块名称", ""))
        result["change_pct"] = float(row.get("涨跌幅", 0)) if pd.notna(row.get("涨跌幅")) else 0
        result["turnover_yi"] = round(float(row.get("成交额", 0)) / 1e8, 2) if pd.notna(row.get("成交额")) else 0
        result["up_count"] = int(row.get("上涨家数", 0)) if pd.notna(row.get("上涨家数")) else 0
        result["down_count"] = int(row.get("下跌家数", 0)) if pd.notna(row.get("下跌家数")) else 0
        result["total_stocks"] = result["up_count"] + result["down_count"]

        # 获取板块成分股详情（用于涨停统计）
        _rate_limit()
        try:
            sector_code = str(row.get("板块代码", ""))
            cons_df = ak.stock_board_industry_cons_em(symbol=result["matched_name"])
            if cons_df is not None and not cons_df.empty:
                # 涨停统计（涨幅 >= 9.5% 近似为涨停）
                if "涨跌幅" in cons_df.columns:
                    zt_count = len(cons_df[cons_df["涨跌幅"].astype(float) >= 9.5])
                    dt_count = len(cons_df[cons_df["涨跌幅"].astype(float) <= -9.5])
                    result["limit_up_count"] = zt_count
                    result["limit_down_count"] = dt_count
                else:
                    result["limit_up_count"] = 0
                    result["limit_down_count"] = 0
        except:
            result["limit_up_count"] = 0
            result["limit_down_count"] = 0

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(realtime_cache, cache_key, result)
    return result


# ============================================================
# 新增工具：Ratio 计算
# ============================================================

def tool_sector_ratio_calc(sector_name: str) -> dict:
    """
    计算板块 Ratio（吸金强度）
    Ratio = 板块当日成交额 / 全市场当日总成交额 × 100%
    """
    cache_key = f"sector_ratio:{sector_name}"
    cached = get_cached(realtime_cache, cache_key)
    if cached:
        return cached

    result = {"sector_name": sector_name}

    try:
        # 获取板块成交额
        sector_data = tool_sector_realtime_quote(sector_name)
        if "error" in sector_data:
            return sector_data

        sector_turnover = sector_data.get("turnover_yi", 0)

        # 获取全市场成交额
        _rate_limit()
        market_df = ak.stock_zh_a_spot_em()
        if market_df is not None and not market_df.empty and "成交额" in market_df.columns:
            total_market_turnover = market_df["成交额"].astype(float).sum() / 1e8  # 转为亿
        else:
            total_market_turnover = 0

        if total_market_turnover > 0:
            ratio = sector_turnover / total_market_turnover * 100
        else:
            ratio = 0

        result["sector_turnover_yi"] = round(sector_turnover, 2)
        result["market_total_turnover_yi"] = round(total_market_turnover, 2)
        result["ratio_pct"] = round(ratio, 2)

        # Ratio 判定
        if ratio >= 30:
            result["ratio_level"] = "🔴 历史峰值区（> 30%）"
            result["ratio_warning"] = "极度集中，警惕板块见顶"
        elif ratio >= 20:
            result["ratio_level"] = "🟡 高度集中（20-30%）"
            result["ratio_warning"] = "关注持续性"
        elif ratio >= 15:
            result["ratio_level"] = "🟢 确定性吸金（15-20%）"
            result["ratio_warning"] = "无"
        elif ratio >= 8:
            result["ratio_level"] = "🟡 观察期（8-15%）"
            result["ratio_warning"] = "无"
        else:
            result["ratio_level"] = "⚪ 低关注度（< 8%）"
            result["ratio_warning"] = "无"

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(realtime_cache, cache_key, result)
    return result


# ============================================================
# 新增工具：共振度计算
# ============================================================

def tool_sector_resonance(sector_name: str) -> dict:
    """
    计算板块共振度（板块内站上MA20的个股占比）
    共振度 = 站上 MA20 个股数 / 板块成分股总数 × 100%
    """
    cache_key = f"sector_resonance:{sector_name}"
    cached = get_cached(technical_cache, cache_key)
    if cached:
        return cached

    result = {"sector_name": sector_name}

    try:
        # 先获取板块名（精确匹配）
        _rate_limit()
        board_df = ak.stock_board_industry_name_em()
        matched = board_df[board_df["板块名称"].str.contains(sector_name, na=False)]
        if matched.empty:
            _rate_limit()
            concept_df = ak.stock_board_concept_name_em()
            if concept_df is not None:
                matched = concept_df[concept_df["板块名称"].str.contains(sector_name, na=False)]

        if matched.empty:
            return {"error": f"未找到匹配板块: {sector_name}"}

        matched_name = str(matched.iloc[0].get("板块名称", ""))

        # 获取板块成分股
        _rate_limit()
        cons_df = ak.stock_board_industry_cons_em(symbol=matched_name)
        if cons_df is None or cons_df.empty:
            return {"error": f"无法获取板块 {matched_name} 的成分股"}

        total_count = len(cons_df)
        above_ma20_count = 0
        sampled_stocks = []

        # 遍历成分股判断是否站上 MA20（为效率，采样前 30 只）
        sample_df = cons_df.head(30)
        for _, stock_row in sample_df.iterrows():
            stock_code = str(stock_row.get("代码", ""))
            stock_name = str(stock_row.get("名称", ""))
            try:
                _rate_limit()
                kline_df = ak.stock_zh_a_hist(symbol=stock_code, period="日k", adjust="qfq")
                if kline_df is not None and len(kline_df) >= 20:
                    close = kline_df["收盘"].astype(float)
                    current_price = float(close.iloc[-1])
                    ma20 = float(close.rolling(20).mean().iloc[-1])
                    is_above = current_price > ma20
                    if is_above:
                        above_ma20_count += 1
                    sampled_stocks.append({
                        "code": stock_code,
                        "name": stock_name,
                        "price": current_price,
                        "ma20": round(ma20, 2),
                        "above_ma20": is_above,
                    })
            except:
                continue

        sampled_count = len(sampled_stocks)
        if sampled_count > 0:
            resonance = above_ma20_count / sampled_count * 100
        else:
            resonance = 0

        result["matched_name"] = matched_name
        result["total_stocks"] = total_count
        result["sampled_count"] = sampled_count
        result["above_ma20_count"] = above_ma20_count
        result["resonance_pct"] = round(resonance, 1)

        # 共振度判定
        if resonance >= 60:
            result["resonance_level"] = "🟢 确定性共振（≥ 60%）"
        elif resonance >= 40:
            result["resonance_level"] = "🟡 观察期（40-60%）"
        else:
            result["resonance_level"] = "🔴 伪共振 / 弱势（< 40%）"

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(technical_cache, cache_key, result)
    return result


# ============================================================
# 新增工具：龙头识别 + 健康度判定
# ============================================================

def tool_sector_leaders(sector_name: str) -> dict:
    """
    识别板块龙头并判定健康度
    龙头标准：涨幅前5 + 近5日新高≥3次 + 换手率∈[10%,25%]
    """
    cache_key = f"sector_leaders:{sector_name}"
    cached = get_cached(technical_cache, cache_key)
    if cached:
        return cached

    result = {"sector_name": sector_name, "leaders": []}

    try:
        # 获取板块成分股
        _rate_limit()
        board_df = ak.stock_board_industry_name_em()
        matched = board_df[board_df["板块名称"].str.contains(sector_name, na=False)]
        if matched.empty:
            _rate_limit()
            concept_df = ak.stock_board_concept_name_em()
            if concept_df is not None:
                matched = concept_df[concept_df["板块名称"].str.contains(sector_name, na=False)]

        if matched.empty:
            return {"error": f"未找到匹配板块: {sector_name}"}

        matched_name = str(matched.iloc[0].get("板块名称", ""))

        _rate_limit()
        cons_df = ak.stock_board_industry_cons_em(symbol=matched_name)
        if cons_df is None or cons_df.empty:
            return {"error": f"无法获取板块成分股"}

        # 按涨幅排序取前5
        if "涨跌幅" in cons_df.columns:
            cons_df["涨跌幅"] = pd.to_numeric(cons_df["涨跌幅"], errors="coerce")
            top5 = cons_df.nlargest(5, "涨跌幅")
        else:
            top5 = cons_df.head(5)

        healthy_count = 0

        for _, stock_row in top5.iterrows():
            stock_code = str(stock_row.get("代码", ""))
            stock_name = str(stock_row.get("名称", ""))
            change_pct = float(stock_row.get("涨跌幅", 0)) if pd.notna(stock_row.get("涨跌幅")) else 0
            turnover_rate = float(stock_row.get("换手率", 0)) if pd.notna(stock_row.get("换手率")) else 0

            leader_info = {
                "code": stock_code,
                "name": stock_name,
                "change_pct": round(change_pct, 2),
                "turnover_rate": round(turnover_rate, 2),
            }

            # 近5日新高判定
            try:
                _rate_limit()
                kline_df = ak.stock_zh_a_hist(symbol=stock_code, period="日k", adjust="qfq")
                if kline_df is not None and len(kline_df) >= 10:
                    recent_5 = kline_df.tail(5)
                    highs = recent_5["最高"].astype(float)
                    # 前20日最高价作为基准
                    prev_high = kline_df.tail(25).head(20)["最高"].astype(float).max()
                    new_high_days = sum(1 for h in highs if h >= prev_high)
                    leader_info["new_high_days_5d"] = int(new_high_days)
                else:
                    leader_info["new_high_days_5d"] = 0
            except:
                leader_info["new_high_days_5d"] = 0

            # 健康度判定
            is_healthy = (
                leader_info["new_high_days_5d"] >= 3
                and 10 <= turnover_rate <= 25
            )
            leader_info["is_healthy"] = is_healthy
            if is_healthy:
                healthy_count += 1

            # 异常信号
            if turnover_rate > 30:
                leader_info["warning"] = "🔴 换手率过高，疑似派发"
            elif turnover_rate < 5:
                leader_info["warning"] = "🟡 换手率偏低，流动性不足"
            else:
                leader_info["warning"] = "无"

            result["leaders"].append(leader_info)

        result["matched_name"] = matched_name
        result["healthy_leader_count"] = healthy_count
        result["total_leader_candidates"] = len(result["leaders"])

        # 龙头健康度总判定
        if healthy_count >= 2:
            result["leader_health_status"] = "🟢 龙头健康度满足（≥2只健康龙头）"
        elif healthy_count == 1:
            result["leader_health_status"] = "🟡 龙头健康度边缘（仅1只健康）"
        else:
            result["leader_health_status"] = "🔴 龙头健康度不满足"

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(technical_cache, cache_key, result)
    return result


# ============================================================
# 新增工具：板块近N日成交额序列
# ============================================================

def tool_sector_turnover_history(sector_name: str, days: int = 5) -> dict:
    """
    获取板块近N日成交额序列，用于流量持久性判定
    返回：每日成交额(亿)、成交额重心变化、Ratio趋势
    """
    cache_key = f"sector_turnover_hist:{sector_name}:{days}"
    cached = get_cached(technical_cache, cache_key)
    if cached:
        return cached

    result = {"sector_name": sector_name}

    try:
        # 获取板块历史行情
        _rate_limit()
        board_df = ak.stock_board_industry_name_em()
        matched = board_df[board_df["板块名称"].str.contains(sector_name, na=False)]

        if matched.empty:
            _rate_limit()
            concept_df = ak.stock_board_concept_name_em()
            if concept_df is not None:
                matched = concept_df[concept_df["板块名称"].str.contains(sector_name, na=False)]

        if matched.empty:
            return {"error": f"未找到匹配板块: {sector_name}"}

        matched_name = str(matched.iloc[0].get("板块名称", ""))

        # 获取板块历史K线
        _rate_limit()
        try:
            hist_df = ak.stock_board_industry_hist_em(
                symbol=matched_name,
                period="日k",
                adjust=""
            )
            if hist_df is not None and not hist_df.empty:
                recent = hist_df.tail(days)
                turnover_list = []
                for _, row in recent.iterrows():
                    turnover_list.append({
                        "date": str(row.get("日期", "")),
                        "turnover_yi": round(float(row.get("成交额", 0)) / 1e8, 2) if pd.notna(row.get("成交额")) else 0,
                        "change_pct": float(row.get("涨跌幅", 0)) if pd.notna(row.get("涨跌幅")) else 0,
                    })

                result["matched_name"] = matched_name
                result["turnover_sequence"] = turnover_list

                # 成交额重心分析（近3日）
                if len(turnover_list) >= 3:
                    last_3 = turnover_list[-3:]
                    d_minus_2 = last_3[0]["turnover_yi"]
                    d_minus_1 = last_3[1]["turnover_yi"]
                    d_0 = last_3[2]["turnover_yi"]

                    result["recent_3d"] = {
                        "D-2": d_minus_2,
                        "D-1": d_minus_1,
                        "D0": d_0,
                    }

                    if d_minus_2 > 0:
                        ratio_d0_d2 = d_0 / d_minus_2
                        result["turnover_gravity_ratio"] = round(ratio_d0_d2, 2)

                        if d_minus_2 < d_minus_1 < d_0 and 1.2 <= ratio_d0_d2 <= 2.0:
                            result["persistence_judgment"] = "🟢 确定性：温和上移（D-2<D-1<D0, 比值∈[1.2,2.0]）"
                        elif d_0 / max(d_minus_1, 0.01) < 0.6:
                            result["persistence_judgment"] = "🔴 阶段性脉冲：次日萎缩≥40%"
                        else:
                            result["persistence_judgment"] = "🟡 观察期：成交额波动但未创新低"
                    else:
                        result["turnover_gravity_ratio"] = None
                        result["persistence_judgment"] = "数据不足"
                else:
                    result["persistence_judgment"] = "数据不足（不足3日）"

            else:
                result["error"] = "无法获取板块历史行情"
        except Exception as e:
            result["error"] = f"获取板块历史数据失败: {str(e)}"

    except Exception as e:
        result["error"] = str(e)

    if "error" not in result:
        set_cached(technical_cache, cache_key, result)
    return result
