"""
平台集成：把「专业关键词 + 城市」拼进各平台真实搜索 URL（deep link）。
模板可在 UI 中编辑；占位符 {kw}{city}{boss}{58} 由 profile 填充。
城市码/拼音按 profile.province + profile.city_name 从四省市州表自动映射。
"""
import urllib.parse
from .db import list_platforms, get_user_profile, PROVINCE_CITIES, PROVINCE_ORDER


def city_codes(profile: dict) -> tuple:
    """返回 (boss_code, 58_pinyin)，按所选省份+城市自动映射；缺省回退该省省会。"""
    prov = profile.get("province") or "云南"
    cities = PROVINCE_CITIES.get(prov, PROVINCE_CITIES["云南"])
    name = (profile.get("city_name") or "").strip()
    if name not in cities:
        name = next(iter(cities))  # 省会（字典第一项）
    m = cities.get(name, next(iter(cities.items()))[1])
    return m["boss"], m["58"]


def build_search_url(platform: dict, profile: dict, keyword: str = None) -> str:
    # 显式关键词优先；无关键词时仅回退到"用户自己设置"的关键词（中性默认关键词为空，不会泄漏他人专业）
    if keyword:
        kw = keyword.split(",")[0].strip()
    else:
        kw = (profile.get("keywords") or "").split(",")[0].strip()
        if not kw:
            # 无简历/未设关键词时，用「手动背景」的专业作为搜索词，保证一键搜有内容
            kw = (profile.get("manual_major") or "").strip()
    boss, p58 = city_codes(profile)
    city_name = profile.get("city_name") or next(iter(PROVINCE_CITIES.get(profile.get("province") or "云南", PROVINCE_CITIES["云南"])))
    tpl = platform.get("search_template", "")
    url = (tpl
           .replace("{kw}", urllib.parse.quote(kw))
           .replace("{city}", urllib.parse.quote(city_name))
           .replace("{boss}", boss)
           .replace("{58}", p58))
    return url


def all_search_links(profile: dict = None, keyword: str = None, category: str = None) -> list:
    profile = profile or get_user_profile()
    out = []
    for p in list_platforms(category=category):
        if not p.get("enabled"):
            continue
        out.append({
            "key": p["key"], "name": p["name"], "color": p["color"],
            "icon": p["icon"], "category": p.get("category", "求职"),
            "url": build_search_url(p, profile, keyword),
        })
    return out
