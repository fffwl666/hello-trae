"""天气查询 CLI —— 调用 OpenWeatherMap 免费 API 查询实时天气与未来预报。

================================ 环境变量设置 ================================
1) 先去 https://home.openweathermap.org/users/sign_up 注册，免费获取 API Key。
   （注册后到 "My API keys" 页面复制 Key，免费版即可用。）

2) 设置环境变量 OWM_API_KEY：

   Windows PowerShell（当前会话生效）:
       $env:OWM_API_KEY = "你的APIKey"

   Windows PowerShell（永久生效，需重开终端）:
       setx OWM_API_KEY "你的APIKey"

   Windows CMD（永久生效）:
       set OWM_API_KEY=你的APIKey

   macOS / Linux（当前会话）:
       export OWM_API_KEY="你的APIKey"

   macOS / Linux（永久，写入 shell 配置）:
       echo 'export OWM_API_KEY="你的APIKey"' >> ~/.bashrc && source ~/.bashrc

3) 验证是否设置成功：
   Windows:  echo $env:OWM_API_KEY
   macOS/Linux:  echo $OWM_API_KEY
============================================================================

用法示例：
    python weather.py beijing
    python weather.py "new york" --forecast
    python weather.py london --forecast 5 --units imperial
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# OpenWeatherMap 免费版接口
BASE_URL = "https://api.openweathermap.org/data/2.5"
CACHE_FILE = Path(__file__).with_name("weather_cache.json")
CACHE_TTL = 600  # 缓存有效期：10 分钟（秒）
TIMEOUT = 10  # 请求超时（秒）


# --------------------------------------------------------------------------
# 缓存
# --------------------------------------------------------------------------
def load_cache():
    """读取本地缓存文件，损坏或不存在时返回空字典。"""
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache):
    """把缓存写回本地 JSON 文件。"""
    try:
        CACHE_FILE.write_text(
            json.dumps(cache, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass  # 缓存写入失败不影响主流程


def get_cached(cache, key):
    """返回未过期的缓存数据；过期或不存在则返回 None。"""
    entry = cache.get(key)
    if entry and time.time() - entry.get("timestamp", 0) < CACHE_TTL:
        return entry.get("data")
    return None


def put_cache(cache, key, data):
    """写入一条缓存记录并落盘。"""
    cache[key] = {"timestamp": time.time(), "data": data}
    save_cache(cache)


# --------------------------------------------------------------------------
# API 请求
# --------------------------------------------------------------------------
def fetch(endpoint, params):
    """请求 OpenWeatherMap 接口，返回 JSON；出错时打印友好提示并退出。"""
    api_key = os.environ.get("OWM_API_KEY")
    if not api_key:
        sys.exit(
            "错误：未设置环境变量 OWM_API_KEY。\n"
            "请先设置 API Key（设置方法见脚本顶部注释），例如 PowerShell：\n"
            '  $env:OWM_API_KEY = "你的APIKey"'
        )

    params = {**params, "appid": api_key}
    try:
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        sys.exit(f"错误：请求超时（超过 {TIMEOUT} 秒），请检查网络后重试。")
    except requests.exceptions.ConnectionError:
        sys.exit("错误：网络连接失败，请检查网络或代理设置。")
    except requests.exceptions.RequestException as exc:
        sys.exit(f"错误：请求失败 —— {exc}")

    if resp.status_code == 404:
        sys.exit(f"错误：未找到城市「{params.get('q')}」，请检查拼写（建议用英文名）。")
    if resp.status_code == 401:
        sys.exit("错误：API Key 无效，请确认 OWM_API_KEY 是否填写正确。")
    if resp.status_code == 429:
        sys.exit("错误：请求过于频繁，已超出免费额度，请稍后再试。")
    if resp.status_code != 200:
        sys.exit(f"错误：接口返回状态码 {resp.status_code} —— {resp.text}")

    try:
        return resp.json()
    except json.JSONDecodeError:
        sys.exit("错误：接口返回内容无法解析。")


# --------------------------------------------------------------------------
# 获取数据（带缓存）
# --------------------------------------------------------------------------
def get_current(city, units):
    """获取实时天气，命中缓存则直接返回。"""
    cache = load_cache()
    key = f"{city.lower()}|{units}|current"
    data = get_cached(cache, key)
    if data is not None:
        return data, True
    data = fetch(
        "weather",
        {"q": city, "units": units, "lang": "zh_cn"},
    )
    put_cache(cache, key, data)
    return data, False


def get_forecast(city, units, days):
    """获取未来 days 天预报（免费版 3 小时粒度数据，按天聚合）。"""
    cache = load_cache()
    key = f"{city.lower()}|{units}|forecast|{days}"
    data = get_cached(cache, key)
    if data is not None:
        return data, True
    # 免费版 5 天 / 3 小时接口，每天 8 条，最多 40 条
    cnt = min(days * 8, 40)
    data = fetch(
        "forecast",
        {"q": city, "units": units, "lang": "zh_cn", "cnt": cnt},
    )
    put_cache(cache, key, data)
    return data, False


# --------------------------------------------------------------------------
# 格式化输出
# --------------------------------------------------------------------------
def unit_symbol(units):
    return "°C" if units == "metric" else "°F"


def wind_unit(units):
    return "m/s" if units == "metric" else "mph"


def local_time(ts, offset):
    """把 UTC 时间戳按城市时区偏移格式化为可读时间。"""
    return datetime.fromtimestamp(ts + offset, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def show_current(data, units, from_cache):
    symbol = unit_symbol(units)
    tz_offset = data.get("timezone", 0)
    main = data["main"]
    wind = data.get("wind", {})
    weather = data["weather"][0]

    tag = "（缓存）" if from_cache else ""
    print(f"城市：{data['name']}{tag}")
    print(f"温度：{main['temp']:.1f} {symbol}（体感 {main['feels_like']:.1f} {symbol}）")
    print(f"天气：{weather['description']}")
    print(f"湿度：{main['humidity']}%")
    print(f"风速：{wind.get('speed', 0):.1f} {wind_unit(units)}")
    print(f"更新时间：{local_time(data['dt'], tz_offset)}")


def show_forecast(data, units, days, from_cache):
    symbol = unit_symbol(units)
    # 预报接口的时区在 city 对象里，而非顶层
    tz_offset = data.get("city", {}).get("timezone", 0)
    tag = "（缓存）" if from_cache else ""

    # 按日期聚合 3 小时粒度数据
    daily = {}
    for item in data.get("list", []):
        date = (datetime.fromtimestamp(item["dt"] + tz_offset, tz=timezone.utc)).strftime("%Y-%m-%d")
        bucket = daily.setdefault(date, {"temps": [], "descs": []})
        bucket["temps"].append(item["main"]["temp_min"])
        bucket["temps"].append(item["main"]["temp_max"])
        bucket["descs"].append(item["weather"][0]["description"])

    print(f"未来 {days} 天预报：{data['city']['name']}{tag}")
    shown = 0
    for date in sorted(daily):
        if shown >= days:
            break
        bucket = daily[date]
        temps = bucket["temps"]
        # 取出现次数最多的天气描述
        desc = max(set(bucket["descs"]), key=bucket["descs"].count)
        print(f"{date}  {desc}  {min(temps):.1f} ~ {max(temps):.1f} {symbol}")
        shown += 1

    # 免费版最多提供 5 天数据，超出时给出提示
    available = len(daily)
    if days > available:
        print(f"提示：免费版预报最多 {available} 天，已展示全部。")


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="查询城市实时天气与未来预报")
    parser.add_argument("city", help="城市名（建议用英文，如 beijing / \"new york\"）")
    parser.add_argument(
        "--forecast",
        nargs="?",
        type=int,
        const=3,
        default=None,
        metavar="N",
        help="查询未来 N 天预报（默认 3 天）",
    )
    parser.add_argument(
        "--units",
        choices=["metric", "imperial"],
        default="metric",
        help="单位：metric=摄氏度(默认) / imperial=华氏度",
    )
    args = parser.parse_args()

    if args.forecast is not None:
        days = args.forecast
        if days < 1:
            parser.error("预报天数必须为正整数")
        data, from_cache = get_forecast(args.city, args.units, days)
        show_forecast(data, args.units, days, from_cache)
    else:
        data, from_cache = get_current(args.city, args.units)
        show_current(data, args.units, from_cache)


if __name__ == "__main__":
    main()
