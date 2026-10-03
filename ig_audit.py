# -*- coding: utf-8 -*-
"""Buffer予約キューの重複を機械で点検する。書き込みはしない。"""
import json, sys, collections, urllib.request

QUEUE_URL = ("https://raw.githubusercontent.com/tatsuboy100-blip/"
             "type-lab-marketing-assets/main/ig-queue.json")

def head20(s):
    return "".join(s.split())[:20]

def audit(posts):
    """posts = [{"text":..., "image":...}, ...] 予約中のものだけ"""
    q = json.load(urllib.request.urlopen(QUEUE_URL, timeout=30))["queue"]
    issues = []
    # 1. 予約中どうしの重複
    c = collections.Counter(head20(p["text"]) for p in posts)
    for k, n in c.items():
        if n > 1:
            issues.append(f"予約中に同じ投稿が{n}件: {k}")
    ci = collections.Counter(p.get("image", "") for p in posts if p.get("image"))
    for k, n in ci.items():
        if n > 1:
            issues.append(f"予約中に同じ画像が{n}件: {k.split('/')[-1]}")
    # 2. queued:true なのに予約にない（＝公開済み or 消えた）
    booked = {head20(p["text"]) for p in posts}
    # 3. queued:false なのに予約に入っている（台帳のズレ）
    for x in q:
        if not x["queued"] and head20(x["caption"]) in booked:
            issues.append(f"台帳がズレています（未投入のはずが予約にある）: {x['file']}")
    done = sum(1 for x in q if x["queued"])
    return {
        "予約中": len(posts),
        "空き枠": max(0, 10 - len(posts)),
        "台帳: 投入済み": done,
        "台帳: 未投入": len(q) - done,
        "問題": issues or "なし",
    }

if __name__ == "__main__":
    posts = json.load(open(sys.argv[1], encoding="utf-8"))
    for k, v in audit(posts).items():
        print(f"{k}: {v}")
