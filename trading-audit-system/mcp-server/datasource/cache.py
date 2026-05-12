"""
A股数据 MCP Server - TTL 缓存层 + 后台预加载
避免高频重复请求数据源，保护数据源稳定性
支持后台定时刷新：用户查过的股票会被自动预加载，确保下次查询命中缓存
"""
import threading
import time
import logging
from collections import OrderedDict
from cachetools import TTLCache
from config.settings import (
    CACHE_TTL_REALTIME,
    CACHE_TTL_TECHNICAL,
    CACHE_TTL_FUNDAMENTAL,
    CACHE_TTL_EVENT,
    PRELOAD_ENABLED,
    PRELOAD_INTERVAL,
)

logger = logging.getLogger(__name__)

# 各模块独立缓存实例
realtime_cache = TTLCache(maxsize=500, ttl=CACHE_TTL_REALTIME)
technical_cache = TTLCache(maxsize=200, ttl=CACHE_TTL_TECHNICAL)
fundamental_cache = TTLCache(maxsize=100, ttl=CACHE_TTL_FUNDAMENTAL)
event_cache = TTLCache(maxsize=100, ttl=CACHE_TTL_EVENT)


def get_cached(cache: TTLCache, key: str):
    """获取缓存值，未命中返回 None"""
    return cache.get(key)


def set_cached(cache: TTLCache, key: str, value):
    """设置缓存值"""
    cache[key] = value


# ============================================================
# 后台预加载系统
# ============================================================

class PreloadManager:
    """
    后台预加载管理器
    - 记录用户查询过的股票代码（最近 20 只）
    - 每隔 PRELOAD_INTERVAL 秒自动刷新这些股票的实时行情缓存
    - 确保用户再次查询时直接命中缓存，零延迟
    """

    def __init__(self, max_stocks: int = 20):
        self._watched_stocks = OrderedDict()  # code -> last_query_time
        self._max_stocks = max_stocks
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def track(self, code: str):
        """记录用户查询的股票代码"""
        with self._lock:
            # 移到最新位置
            if code in self._watched_stocks:
                self._watched_stocks.move_to_end(code)
            else:
                self._watched_stocks[code] = time.time()
            # 超出上限则淘汰最旧的
            while len(self._watched_stocks) > self._max_stocks:
                self._watched_stocks.popitem(last=False)

    def get_watched_stocks(self) -> list:
        """获取当前监控的股票列表"""
        with self._lock:
            return list(self._watched_stocks.keys())

    def start(self):
        """启动后台预加载线程"""
        if not PRELOAD_ENABLED:
            logger.info("后台预加载已禁用")
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._preload_loop, daemon=True)
        self._thread.start()
        logger.info(f"后台预加载已启动，间隔 {PRELOAD_INTERVAL} 秒")

    def stop(self):
        """停止后台预加载"""
        self._running = False

    def _preload_loop(self):
        """预加载循环：定时刷新所有被监控股票的实时行情"""
        while self._running:
            try:
                stocks = self.get_watched_stocks()
                if stocks:
                    # 延迟导入避免循环引用
                    from datasource.akshare_adapter import get_realtime_quote
                    for code in stocks:
                        if not self._running:
                            break
                        try:
                            result = get_realtime_quote(code)
                            if result and "error" not in result:
                                cache_key = f"realtime:{code}"
                                set_cached(realtime_cache, cache_key, result)
                        except Exception as e:
                            logger.debug(f"预加载 {code} 失败: {e}")
                        time.sleep(0.5)  # 每只股票间隔 0.5 秒，避免请求过快
            except Exception as e:
                logger.error(f"预加载循环异常: {e}")

            # 等待下一轮
            time.sleep(PRELOAD_INTERVAL)


# 全局预加载管理器实例
preloader = PreloadManager(max_stocks=20)
