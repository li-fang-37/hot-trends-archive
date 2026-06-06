import json, os, sys

data_dir = r"D:\Hermes\hot-trends-archive"

platforms = {
    "weibo": {"file": "_weibo.json", "name": "微博", "limit": 15},
    "zhihu": {"file": "_zhihu.json", "name": "知乎", "limit": 10},
    "bili": {"file": "_bili.json", "name": "B站", "limit": 10},
    "baidu": {"file": "_baidu.json", "name": "百度", "limit": 10},
    "douyin": {"file": "_douyin.json", "name": "抖音", "limit": 10},
    "toutiao": {"file": "_toutiao.json", "name": "头条", "limit": 10},
}

all_data = {}
for key, cfg in platforms.items():
    path = os.path.join(data_dir, cfg["file"])
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    items = raw.get("data", [])[:cfg["limit"]]
    all_data[key] = {"name": cfg["name"], "items": items}
    print(f"\n=== {cfg['name']} ===")
    for i, item in enumerate(items):
        title = item.get("title", "")
        hot = item.get("hot_value", 0)
        link = item.get("link", "")
        rank = i + 1
        print(f"#{rank} {title} | 热度:{hot}")

# Summary
print("\n\n=== 全平台分析 ===")
fire_items = []
hot_items = []
for key, data in all_data.items():
    for item in data["items"]:
        hot = item.get("hot_value", 0)
        title = item.get("title", "")
        if hot >= 1000000:
            fire_items.append((key, title, hot))
        elif hot >= 500000:
            hot_items.append((key, title, hot))

print(f"\n🔥 全民爆点(≥100万): {len(fire_items)}条")
for p, t, v in fire_items:
    print(f"  [{p}] {t} ({v})")
print(f"\n🟠 热门(50-100万): {len(hot_items)}条")
for p, t, v in hot_items:
    print(f"  [{p}] {t} ({v})")
