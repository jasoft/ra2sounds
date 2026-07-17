# -*- coding: utf-8 -*-
"""
build_manifest.py
================

扫描 sounds/ 目录，生成浏览器用的 sounds.json 编目。

归类规则：
  - Taunts/tau<side><n>.wav  -> 嘲讽语音，按阵营分：
        am=苏军(soviet), ko=尤里(yuri), br=盟军(allied),
        ir=尤里剧情?, li=苏军?, ge=苏军?, fr=盟军?, cu=尤里?, ru=苏军?, yu=尤里?
    （前缀映射见 TAUNT_SIDES）
  - bgm/unknown_*.wav         -> 背景音乐 / 界面音效（无原名，归 other）

生成结构（供 index.html 消费）：
{
  "generated": "...",
  "sides": [ {id, name_zh, items:[{file,label,side,...}]}, ... ],
  "items": [ {file, side, category, label, ...} ]
}
"""

import os
import json
import subprocess
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SOUNDS = os.path.join(ROOT, "sounds")

# Taunts 前缀 -> 阵营（红警原版对战嘲讽语音的阵营代码）
TAUNT_SIDES = {
    "am": ("soviet", "苏军"),
    "ko": ("yuri",   "尤里"),
    "br": ("allied", "盟军"),
    "ir": ("yuri",   "尤里"),
    "li": ("soviet", "苏军"),
    "ge": ("soviet", "苏军"),
    "fr": ("allied", "盟军"),
    "cu": ("yuri",   "尤里"),
    "ru": ("soviet", "苏军"),
    "yu": ("yuri",   "尤里"),
}

SIDE_ORDER = [
    ("soviet", "苏军"),
    ("allied", "盟军"),
    ("yuri",   "尤里"),
    ("other",  "背景音乐 / 系统音效"),
]


def probe(path):
    """返回 (duration, sample_rate, channels) 或 None。"""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "stream=duration,sample_rate,channels",
             "-of", "json", path],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode != 0:
            return None
        info = json.loads(out.stdout)
        st = info.get("streams", [{}])[0]
        dur = float(st.get("duration", 0) or 0)
        sr = int(st.get("sample_rate", 0) or 0)
        ch = int(st.get("channels", 0) or 0)
        return (round(dur, 3), sr, ch)
    except Exception:
        return None


def build():
    items = []

    # ---- Taunts ----
    taunt_dir = os.path.join(SOUNDS, "taunts")
    if os.path.isdir(taunt_dir):
        for fn in sorted(os.listdir(taunt_dir)):
            if not fn.lower().endswith(".wav"):
                continue
            # tau<side><n>.wav
            code = fn[3:5].lower()  # 去掉 "tau"
            side, side_zh = TAUNT_SIDES.get(code, ("other", "未知"))
            num = fn[5:-4]
            meta = probe(os.path.join(taunt_dir, fn))
            items.append({
                "file": f"taunts/{fn}",
                "side": side,
                "category": "taunt",
                "label": f"{side_zh}嘲讽语音 · 第{num}句",
                "raw": fn,
                "duration": (meta[0] if meta else None),
                "sample_rate": (meta[1] if meta else None),
            })

    # ---- BGM / 系统音效 ----
    bgm_dir = os.path.join(SOUNDS, "bgm")
    if os.path.isdir(bgm_dir):
        for fn in sorted(os.listdir(bgm_dir)):
            if not fn.lower().endswith(".wav"):
                continue
            meta = probe(os.path.join(bgm_dir, fn))
            items.append({
                "file": f"bgm/{fn}",
                "side": "other",
                "category": "bgm",
                "label": f"背景音乐 / 系统音效 ({fn})",
                "raw": fn,
                "duration": (meta[0] if meta else None),
                "sample_rate": (meta[1] if meta else None),
            })

    # ---- 聚合成 sides ----
    sides = []
    by_side = {sid: [] for sid, _ in SIDE_ORDER}
    for it in items:
        by_side.setdefault(it["side"], []).append(it)

    for sid, name_zh in SIDE_ORDER:
        lst = by_side.get(sid, [])
        if not lst:
            continue
        sides.append({
            "id": sid,
            "name_zh": name_zh,
            "count": len(lst),
            "items": lst,
        })

    manifest = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "total": len(items),
        "sides": sides,
        "items": items,
    }

    out_path = os.path.join(ROOT, "sounds.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[done] 生成 {out_path}: {len(items)} 个音效，{len(sides)} 个分类")
    for s in sides:
        print(f"  - {s['name_zh']}: {s['count']}")


if __name__ == "__main__":
    build()
