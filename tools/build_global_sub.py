#!/usr/bin/env python3
"""从 AIsouler 的 GKD 订阅（json5）中提取「开屏广告-全局」组，
生成可独立分发的 globalGroups 订阅。

用法:
    python tools/build_global_sub.py AIsouler_gkd.json5 -o gkd/gkd-global-splash.json

依赖:
    pip install json5
"""

import argparse
import json
import sys

try:
    import json5
except ImportError:
    sys.exit("缺少依赖：pip install json5")

GROUP_NAME = "开屏广告-全局"


def build(source: str, output: str, sub_id: int) -> None:
    with open(source, encoding="utf-8") as f:
        data = json5.load(f)

    group = next(
        (g for g in data.get("globalGroups", []) if g.get("name") == GROUP_NAME),
        None,
    )
    if group is None:
        sys.exit(f"未找到全局组：{GROUP_NAME}")

    group = dict(group)
    # 原订阅用 apps 排除「已有专属规则的 App」；独立分发时清空，
    # 否则大部分 App 会被静默排除。
    group.pop("apps", None)
    group["key"] = 0
    group["enable"] = True
    group["matchAnyApp"] = True
    group["matchSystemApp"] = False
    group["matchLauncher"] = False

    sub = {
        "id": sub_id,
        "name": "全局开屏跳过(AIsouler)",
        "version": 1,
        "author": "AIsouler",
        "supportUri": "https://github.com/AIsouler/GKD_subscription",
        "categories": [{"key": 0, "name": "开屏广告", "enable": True}],
        "globalGroups": [group],
        "apps": [],
    }

    with open(output, "w", encoding="utf-8", newline="\n") as f:
        json.dump(sub, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"wrote {output}: {len(group.get('rules', []))} rule(s)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="AIsouler 订阅 json5 文件")
    ap.add_argument("-o", "--output", default="gkd/gkd-global-splash.json")
    ap.add_argument("--id", type=int, default=202611091)
    args = ap.parse_args()
    build(args.source, args.output, args.id)


if __name__ == "__main__":
    main()
