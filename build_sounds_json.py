# -*- coding: utf-8 -*-
"""
build_sounds_json.py
====================

为 sounds/ 目录下的 2293 个真实红警2/YR 音效（已由 XCC Mixer 从 .aud 解出，
文件名即原始游戏音效代码，如 abirj01a / vwaratta / acri01a …）生成浏览器
用的 sounds.json 编目。

★ 本脚本使用权威对照模块 ra2_sound_map.classify() 进行解析。
  ra2_sound_map.py 的数据来源（按可信度）：
    1. OpenRA ra2 mod 的 audio/voices.yaml「逐兵种语音组」（原版 Westwood 代码）
    2. 实际提取的原版 sounds/ 文件
    3. 社区 RA2 idcode 对照表交叉验证
  凡无法高置信度确认的代码，一律以官方代码本身展示（不臆造中文名）。

命名规则（Westwood 官方）：
  [前缀 1 字母][兵种代码 2~3 字母][语音类型 2~3 字母][序号字母 a~g]
  前缀: i=步兵  v=载具/空军  a=环境/动物  u=界面/系统  b=建筑  g=建筑/通用
        s=超级武器  x/t/c=资料片/音乐/剧情语音
"""

import os
import json
import glob
import datetime
import subprocess

import ra2_sound_map as SMAP

ROOT = os.path.dirname(os.path.abspath(__file__))
SOUNDS = os.path.join(ROOT, "sounds")

# 前缀 proto 代码 -> 中文大类
PROTO_ZH = {
    "infantry": "步兵",
    "vehicle": "载具 / 空军",
    "building": "建筑",
    "ambient": "环境 / 动物",
    "ui": "界面 / 系统",
    "support": "超级武器 / 支援",
    "other": "其他",
    "expansion": "资料片",
}

# 阵营 side -> 中文
SIDE_ZH = {
    "soviet": "苏军",
    "allied": "盟军",
    "yuri": "尤里",
    "other": "系统 / 环境 / 中立",
}

# 战场阵营分组顺序
SIDE_ORDER = ["soviet", "allied", "yuri", "other"]


def probe(path):
    """ffprobe 取时长/采样率/声道，失败返回 None。"""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "stream=duration,sample_rate,channels",
             "-of", "json", path],
            capture_output=True, text=True, timeout=30)
        if out.returncode != 0:
            return None
        info = json.loads(out.stdout)
        st = info.get("streams", [{}])[0]
        return (round(float(st.get("duration", 0) or 0), 3),
                int(st.get("sample_rate", 0) or 0),
                int(st.get("channels", 0) or 0))
    except Exception:
        return None


def build():
    items = []
    for fn in sorted(glob.glob(os.path.join(SOUNDS, "*.wav"))):
        base = os.path.basename(fn)
        name = os.path.splitext(base)[0]
        r = SMAP.classify(name)

        pre = r["pre"]
        known = r["known"]

        # proto 代码：已知项直接用 U 里的 proto；未知项按前缀推导
        if known:
            proto_code = r["proto"]
        else:
            proto_code = SMAP.PREFIX.get(pre, ("other", "其他"))[0]

        # side：已知项取 U 里的 side；未知项归为 other（中立）
        side = r["side"] if known else "other"
        if side not in SIDE_ZH:
            side = "other"

        proto_zh = PROTO_ZH.get(proto_code,
                                SMAP.PREFIX.get(pre, ("other", "其他"))[1])
        vtype = r["vtype"] or ""
        vtype_zh = r["vtype_zh"]

        meta = probe(fn)
        items.append({
            "file": base,
            "name": name,
            "faction": proto_code,
            "faction_zh": proto_zh,
            "side": side,
            "side_zh": SIDE_ZH.get(side, "其他"),
            "proto": proto_code,
            "proto_zh": proto_zh,
            "code": r["code"],
            "unit_zh": r["unit_zh"],
            "unit_en": r["unit_en"],
            "action": vtype,
            "action_zh": vtype_zh,
            "status_zh": vtype_zh,
            "status_desc": "",
            "label": r["label"],
            "known": known,
            "duration": (meta[0] if meta else None),
            "sample_rate": (meta[1] if meta else None),
            "channels": (meta[2] if meta else None),
        })

    # 聚合为 阵营(苏/盟/尤里/系统) -> 兵种 -> 动作 的三级树（顶层按 side 分组）
    by_side = {}
    for it in items:
        by_side.setdefault(it["side"], []).append(it)

    sides = []
    for sid in SIDE_ORDER:
        lst = by_side.get(sid)
        if not lst:
            continue
        sides.append({
            "id": sid,
            "name_zh": SIDE_ZH.get(sid, "其他"),
            "count": len(lst),
            "items": lst,
        })

    manifest = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "total": len(items),
        "factions": sides,
        "items": items,
    }
    out_path = os.path.join(ROOT, "sounds.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    known_n = sum(1 for it in items if it["known"])
    print(f"[done] {out_path}: {len(items)} 条，{len(sides)} 个阵营分组")
    for s in sides:
        print(f"  - {s['name_zh']}: {s['count']}")
    print(f"[stat] 已识别兵种: {known_n}/{len(items)} "
          f"({known_n * 100 // len(items)}%)")


if __name__ == "__main__":
    build()
