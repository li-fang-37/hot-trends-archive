#!/usr/bin/env python3
"""热搜抓取脚本 - 由 GitHub Actions 每30分钟调用"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

CST = timezone(timedelta(hours=8))

# 支持的平台
PLATFORMS = {
    "weibo":   {"name": "微博热搜",  "url": "https://60s.viki.moe/v2/weibo"},
    "zhihu":   {"name": "知乎热榜",  "url": "https://60s.viki.moe/v2/zhihu"},
    "baidu":   {"name": "百度热点",  "url": "https://60s.viki.moe/v2/baidu/hot"},
    "douyin":  {"name": "抖音热门",  "url": "https://60s.viki.moe/v2/douyin"},
    "bili":    {"name": "B站热门",   "url": "https://60s.viki.moe/v2/bili"},
    "toutiao": {"name": "今日头条",  "url": "https://60s.viki.moe/v2/toutiao"},
}

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def fetch_json(url: str, timeout: int = 20):
    """请求并解析 JSON"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_weibo_detail(keyword: str) -> dict | None:
    """尝试抓取微博搜索结果的原文摘要"""
    import urllib.parse
    try:
        q = urllib.parse.quote(keyword)
        url = f"https://s.weibo.com/weibo?q={q}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # 尝试提取卡片内容
        snippets = []
        for keyword in ["card-wrap", "txt", "content"]:
            idx = html.find(keyword)
            if idx >= 0:
                break
        return {"keyword": keyword, "url": url, "detail_fetched": True}
    except Exception:
        return None

def save_platform(key: str, info: dict, items: list, now: datetime):
    """保存单平台数据到按日期-时间组织的文件"""
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")
    plat_dir = DATA_DIR / key / date_str
    plat_dir.mkdir(parents=True, exist_ok=True)
    
    # 每半小时的快照
    snapshot = {
        "platform": key,
        "platform_name": info["name"],
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "items": []
    }
    
    for item in items:
        entry = {
            "title": item.get("title", ""),
            "hot_value": item.get("hot_value", 0),
            "link": item.get("link", ""),
            "rank": len(snapshot["items"]) + 1,
        }
        snapshot["items"].append(entry)
    
    path = plat_dir / f"{time_str}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    
    return snapshot

def update_index(snapshots: dict, now: datetime):
    """更新全局索引文件，前端用来加载数据"""
    date_str = now.strftime("%Y-%m-%d")
    index_path = DATA_DIR / "index.json"
    
    index = {"dates": {}, "latest": {}}
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    
    if date_str not in index["dates"]:
        index["dates"][date_str] = {"platforms": {}}
    
    for key, snap in snapshots.items():
        time_str = now.strftime("%H%M")
        if key not in index["dates"][date_str]["platforms"]:
            index["dates"][date_str]["platforms"][key] = []
        if time_str not in index["dates"][date_str]["platforms"][key]:
            index["dates"][date_str]["platforms"][key].append(time_str)
            index["dates"][date_str]["platforms"][key].sort()
    
    # 最新快照
    index["latest"] = {
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": date_str,
        "platforms": {k: v["items"][:5] for k, v in snapshots.items()}
    }
    
    # 紧凑存储
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    
    # 每日摘要
    summary_path = DATA_DIR / date_str / "_summary.json"
    summary = {"date": date_str, "platforms": {}}
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
    
    for key, snap in snapshots.items():
        if key not in summary["platforms"]:
            summary["platforms"][key] = {"snapshots": 0, "total_items": set()}
        summary["platforms"][key]["snapshots"] += 1
        summary["platforms"][key]["last_time"] = now.strftime("%H:%M")
    
    with open(summary_path, "w", encoding="utf-8") as f:
        # Convert set to list for JSON
        summary_clean = json.loads(json.dumps(summary))
        json.dump(summary_clean, f, ensure_ascii=False, separators=(",", ":"))

def main():
    now = datetime.now(CST)
    print(f"[{now.strftime('%Y-%m-%d %H:%M')}] 开始抓取热搜...")
    
    snapshots = {}
    successes = 0
    
    for key, info in PLATFORMS.items():
        try:
            data = fetch_json(info["url"])
            items = data.get("data", [])
            if not items:
                print(f"  ⚠ {info['name']}: 返回数据为空")
                continue
            snapshots[key] = save_platform(key, info, items, now)
            print(f"  ✓ {info['name']}: {len(items)} 条")
            successes += 1
        except Exception as e:
            print(f"  ✗ {info['name']}: {e}")
    
    if snapshots:
        update_index(snapshots, now)
    
    print(f"[完成] {successes}/{len(PLATFORMS)} 平台抓取成功")
    return successes > 0

if __name__ == "__main__":
    main()
