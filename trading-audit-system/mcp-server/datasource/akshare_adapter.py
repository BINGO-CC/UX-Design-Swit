"""
A股数据 MCP Server - AKShare 数据适配器
封装 AKShare 调用，统一异常处理和数据格式化
"""
import time
import akshare as ak
import pandas as pd
import numpy as np
from typing import Optional
from config.settings import AKSHARE_RATE_LIMIT

# 请求限流：记录上次请求时间
_last_request_time = 0.0


def _rate_limit():
    """简易限流：确保请求间隔不低于设定值"""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < AKSHARE_RATE_LIMIT:
        time.sleep(AKSHARE_RATE_LIMIT - elapsed)
    _last_request_time = time.time()


def _normalize_code(code: str) -> str:
    """
    标准化股票代码
    支持输入格式：600519、sh600519、SH600519、600519.SH
    统一输出：6位纯数字
    """
    code = code.strip().upper()
    # 去掉交易所前缀
    for prefix in ["SH", "SZ", "BJ"]:
        code = code.replace(prefix, "")
    # 去掉点号后缀
    if "." in code:
        code = code.split(".")[0]
    return code


def _get_market_prefix(code: str) -> str:
    """根据代码判断市场前缀"""
    code = _normalize_code(code)
    if code.startswith(("6", "9")):
        return "sh"
    elif code.startswith(("0", "2", "3")):
        return "sz"
    elif code.startswith(("4", "8")):
        return "bj"
    return "sh"


# ============================================================
# 实时行情
# ============================================================

def get_realtime_quote(code: str) -> Optional[dict]:
    """
    获取个股实时行情（使用新浪财经 API，秒级返回，无限流风险）
    备用：腾讯财经 API
    """
    _rate_limit()
    code = _normalize_code(code)
    market = _get_market_prefix(code)
    symbol = f"{market}{code}"

    # ---- 主数据源：新浪财经 ----
    try:
        import requests
        url = f"https://hq.sinajs.cn/list={symbol}"
        headers = {
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "gbk"
        text = resp.text.strip()

        # 解析: var hq_str_sh600519="名称,今开,昨收,当前价,最高,最低,买一,卖一,成交量(股),成交额,...";
        if '="' not in text or text.endswith('="";'):
            return _get_realtime_quote_tencent(code, market)  # 降级到腾讯

        data_str = text.split('="')[1].rstrip('";')
        fields = data_str.split(",")

        if len(fields) < 32:
            return _get_realtime_quote_tencent(code, market)

        name = fields[0]
        open_price = float(fields[1]) if fields[1] else 0
        prev_close = float(fields[2]) if fields[2] else 0
        current_price = float(fields[3]) if fields[3] else 0
        high = float(fields[4]) if fields[4] else 0
        low = float(fields[5]) if fields[5] else 0
        volume = float(fields[8]) if fields[8] else 0  # 股
        turnover = float(fields[9]) if fields[9] else 0  # 元

        # 计算涨跌幅
        change_pct = round((current_price - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0
        change_amount = round(current_price - prev_close, 2) if prev_close > 0 else 0
        amplitude = round((high - low) / prev_close * 100, 2) if prev_close > 0 else 0

        return {
            "code": code,
            "name": name,
            "current_price": current_price,
            "change_pct": change_pct,
            "change_amount": change_amount,
            "volume": volume,
            "turnover": turnover,
            "turnover_rate": None,  # 新浪接口不含换手率，需额外计算
            "volume_ratio": None,
            "amplitude": amplitude,
            "high": high,
            "low": low,
            "open": open_price,
            "prev_close": prev_close,
            "pe_ttm": None,
            "pb": None,
            "total_market_cap": None,
            "circulating_market_cap": None,
            "data_source": "sina",
        }
    except Exception as e:
        # 降级到腾讯
        try:
            return _get_realtime_quote_tencent(code, market)
        except Exception as e2:
            return {"error": f"新浪和腾讯均失败: sina={str(e)}, tencent={str(e2)}"}


def _get_realtime_quote_tencent(code: str, market: str) -> Optional[dict]:
    """
    备用数据源：腾讯财经 API
    """
    import requests
    symbol = f"{market}{code}"
    url = f"http://qt.gtimg.cn/q={symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.encoding = "gbk"
    text = resp.text.strip()

    if '="' not in text:
        return {"error": "腾讯财经无数据"}

    data_str = text.split('="')[1].rstrip('";')
    fields = data_str.split("~")

    if len(fields) < 45:
        return {"error": "腾讯财经数据格式异常"}

    name = fields[1]
    current_price = float(fields[3]) if fields[3] else 0
    prev_close = float(fields[4]) if fields[4] else 0
    open_price = float(fields[5]) if fields[5] else 0
    volume = float(fields[6]) * 100 if fields[6] else 0  # 手→股
    high = float(fields[33]) if len(fields) > 33 and fields[33] else 0
    low = float(fields[34]) if len(fields) > 34 and fields[34] else 0
    turnover_str = fields[37] if len(fields) > 37 else "0"
    turnover = float(turnover_str) * 10000 if turnover_str and turnover_str != "" else 0

    change_pct = round((current_price - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0
    change_amount = round(current_price - prev_close, 2)
    amplitude = round((high - low) / prev_close * 100, 2) if prev_close > 0 else 0

    # 腾讯数据含换手率等
    turnover_rate = float(fields[38]) if len(fields) > 38 and fields[38] else None
    pe_ttm = float(fields[39]) if len(fields) > 39 and fields[39] else None

    return {
        "code": code,
        "name": name,
        "current_price": current_price,
        "change_pct": change_pct,
        "change_amount": change_amount,
        "volume": volume,
        "turnover": turnover,
        "turnover_rate": turnover_rate,
        "volume_ratio": None,
        "amplitude": amplitude,
        "high": high,
        "low": low,
        "open": open_price,
        "prev_close": prev_close,
        "pe_ttm": pe_ttm,
        "pb": None,
        "total_market_cap": None,
        "circulating_market_cap": None,
        "data_source": "tencent",
    }


# ============================================================
# 技术指标
# ============================================================

def get_kline_data(code: str, period: str = "daily", count: int = 250) -> Optional[pd.DataFrame]:
    """
    获取K线数据
    period: daily / weekly / monthly
    count: 获取根数
    """
    _rate_limit()
    try:
        code = _normalize_code(code)
        period_map = {"daily": "日k", "weekly": "周k", "monthly": "月k"}
        ak_period = period_map.get(period, "日k")

        df = ak.stock_zh_a_hist(symbol=code, period=ak_period, adjust="qfq")
        if df is None or df.empty:
            return None
        # 取最近 count 根
        df = df.tail(count).reset_index(drop=True)
        return df
    except Exception as e:
        return None


def calculate_technical_indicators(code: str, period: str = "daily") -> Optional[dict]:
    """
    计算技术指标：MA系列、RSI、MACD、VWAP
    """
    df = get_kline_data(code, period, count=250)
    if df is None or df.empty:
        return {"error": "无法获取K线数据"}

    close = df["收盘"].astype(float)
    high = df["最高"].astype(float)
    low = df["最低"].astype(float)
    volume = df["成交量"].astype(float)
    turnover = df["成交额"].astype(float) if "成交额" in df.columns else None

    result = {}

    # --- 均线 ---
    for ma_period in [5, 10, 20, 60, 120, 250]:
        if len(close) >= ma_period:
            ma_val = close.rolling(ma_period).mean().iloc[-1]
            result[f"MA{ma_period}"] = round(float(ma_val), 2)
        else:
            result[f"MA{ma_period}"] = None

    # --- 均线排列判定 ---
    ma20 = result.get("MA20")
    ma60 = result.get("MA60")
    ma120 = result.get("MA120")
    ma250 = result.get("MA250")
    if all([ma20, ma60, ma120, ma250]):
        if ma20 > ma60 > ma120 > ma250:
            result["ma_arrangement"] = "多头排列"
        elif ma20 < ma60 < ma120 < ma250:
            result["ma_arrangement"] = "空头排列"
        else:
            result["ma_arrangement"] = "缠绕/过渡"
    else:
        result["ma_arrangement"] = "数据不足"

    # --- RSI (14日) ---
    if len(close) >= 15:
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        result["RSI_14"] = round(float(rsi.iloc[-1]), 2) if pd.notna(rsi.iloc[-1]) else None
    else:
        result["RSI_14"] = None

    # --- MACD (12, 26, 9) ---
    if len(close) >= 35:
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        macd_hist = 2 * (dif - dea)

        result["MACD_DIF"] = round(float(dif.iloc[-1]), 4)
        result["MACD_DEA"] = round(float(dea.iloc[-1]), 4)
        result["MACD_HIST"] = round(float(macd_hist.iloc[-1]), 4)

        # 金叉/死叉判定
        if dif.iloc[-1] > dea.iloc[-1]:
            # 寻找最近一次金叉发生的天数
            cross_days = 0
            for i in range(len(dif) - 1, 0, -1):
                if dif.iloc[i] > dea.iloc[i] and dif.iloc[i-1] <= dea.iloc[i-1]:
                    cross_days = len(dif) - 1 - i
                    break
                if dif.iloc[i] <= dea.iloc[i]:
                    cross_days = len(dif) - 1 - i
                    break
            result["MACD_status"] = f"金叉({cross_days}日)"
        else:
            cross_days = 0
            for i in range(len(dif) - 1, 0, -1):
                if dif.iloc[i] < dea.iloc[i] and dif.iloc[i-1] >= dea.iloc[i-1]:
                    cross_days = len(dif) - 1 - i
                    break
                if dif.iloc[i] >= dea.iloc[i]:
                    cross_days = len(dif) - 1 - i
                    break
            result["MACD_status"] = f"死叉({cross_days}日)"
    else:
        result["MACD_DIF"] = None
        result["MACD_DEA"] = None
        result["MACD_HIST"] = None
        result["MACD_status"] = "数据不足"

    # --- VWAP (当日) ---
    if turnover is not None and len(volume) > 0 and volume.iloc[-1] > 0:
        # 使用最后一日数据估算（精确 VWAP 需要分时数据）
        vwap = turnover.iloc[-1] / volume.iloc[-1] / 100  # 成交额/成交量/100
        result["VWAP"] = round(float(vwap), 2)
    else:
        result["VWAP"] = None

    # --- 偏离度 ---
    current_price = float(close.iloc[-1])
    result["current_price"] = current_price
    if ma250:
        result["deviation_MA250_pct"] = round((current_price - ma250) / ma250 * 100, 2)
    if ma20:
        result["deviation_MA20_pct"] = round((current_price - ma20) / ma20 * 100, 2)

    # --- 近5日量比 ---
    if len(volume) >= 6:
        avg_vol_5 = volume.iloc[-6:-1].mean()
        if avg_vol_5 > 0:
            result["volume_ratio_5d"] = round(float(volume.iloc[-1] / avg_vol_5), 2)
        else:
            result["volume_ratio_5d"] = None
    else:
        result["volume_ratio_5d"] = None

    return result


# ============================================================
# 大盘指数
# ============================================================

def get_index_quote(index_code: str = "000001") -> Optional[dict]:
    """
    获取大盘指数行情 + 技术状态
    index_code: 000001(上证) / 399001(深证) / 399006(创业板) / HSI(恒指)
    """
    _rate_limit()
    try:
        # 获取指数K线
        df = ak.stock_zh_index_daily_em(symbol=f"sh{index_code}" if index_code.startswith("0") else f"sz{index_code}")
        if df is None or df.empty:
            # 尝试上证指数
            df = ak.stock_zh_index_daily_em(symbol="sh000001")

        if df is None or df.empty:
            return {"error": "无法获取指数数据"}

        df = df.tail(120).reset_index(drop=True)
        close = df["close"].astype(float)

        current = float(close.iloc[-1])

        # MA60
        ma60 = float(close.rolling(60).mean().iloc[-1]) if len(close) >= 60 else None

        # MACD
        macd_status = "数据不足"
        macd_days = 0
        if len(close) >= 35:
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()

            if dif.iloc[-1] > dea.iloc[-1]:
                status = "金叉"
            else:
                status = "死叉"

            # 计算持续天数
            for i in range(len(dif) - 2, -1, -1):
                if status == "金叉" and dif.iloc[i] <= dea.iloc[i]:
                    macd_days = len(dif) - 1 - i
                    break
                elif status == "死叉" and dif.iloc[i] >= dea.iloc[i]:
                    macd_days = len(dif) - 1 - i
                    break

            macd_status = f"{status}({macd_days}日)"

        # 大盘环境判定（协议 1.5 逻辑）
        environment = "正常"
        if ma60 and current < ma60 and "死叉" in macd_status and macd_days >= 5:
            environment = "🔴 系统级降级：大盘处于下行通道"
        elif ma60 and current > ma60:
            environment = "🟢 大盘健康"
        else:
            environment = "🟡 大盘中性/震荡"

        return {
            "index_code": index_code,
            "current_price": current,
            "MA60": ma60,
            "MACD_status": macd_status,
            "environment_judgment": environment,
            "price_vs_MA60": "上方" if (ma60 and current > ma60) else "下方" if ma60 else "未知",
        }
    except Exception as e:
        return {"error": str(e)}
