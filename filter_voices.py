#!/usr/bin/env python3
"""从 voice_scan.json 过滤低质量转写，把高置信真人声写入 notes.db。

全量扫描后做质量收口：丢弃 base.en 在 RA2 失真音效上的假阳性
（幽灵音 //、尖叫 GRA/BE 长尾重复、超短无意义词），只保留确定是
真人声的英文转写。不依赖模型重跑——直接从已落盘的 scan 结果过滤。

过滤规则：
  - 文本去空白后为空或仅 1 个字符 -> 丢弃
  - 文本含 '//' -> 丢弃（幽灵/电子音的幽灵 token）
  - 单 token 重复 >= 8 次（GRA/BE/are/aw 等）-> 丢弃（幻觉重复）
  - 去重压缩后长度 > 80 字符（典型长尾幻觉） -> 丢弃
  - no_speech_prob > 0.5 -> 丢弃（保证安全边际）
"""

import json
import os
import re
import sqlite3
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(ROOT, "notes.db")
DEFAULT_SCAN = os.path.join(ROOT, "voice_scan.json")

_TOKEN_RE = re.compile(r"[A-Za-z']+")
_VOWEL_RE = re.compile(r"[aeiou]", re.I)


def dominant_repeat_count(text):
    """空格分词后，单个 token 的累计出现次数（幻觉检测）。"""
    toks = _TOKEN_RE.findall(text.lower())
    if not toks:
        return 0
    from collections import Counter

    return max(Counter(toks).values())


def is_good(text, nsp, max_nsp=0.5):
    if nsp is None or nsp > max_nsp:
        return False
    t = (text or "").strip()
    if len(t) <= 1:
        return False
    if "//" in t:
        return False
    # 去除标点/空格后的纯内容
    bare = re.sub(r"[^A-Za-z]", "", t)
    # 规则1：整段无空格的超长串（幻觉巨串，如 Whaaaareareare...）
    has_space = " " in t
    if not has_space:
        # 短且含元音的单字（Ahh/Ugh/Whoa 等）允许保留
        if len(bare) > 15:
            return False
        if not _VOWEL_RE.search(bare):
            return False
    # 规则2：同一 token 累计重复 >= 8（aw aw aw / Materialian Materialian / reported reported）
    if dominant_repeat_count(t) >= 8:
        return False
    # 规则3：折叠连续重复后语义 token 数异常长（长尾幻觉）
    toks = _TOKEN_RE.findall(t.lower())
    if toks:
        folded = []
        for tk in toks:
            if not folded or tk != folded[-1]:
                folded.append(tk)
        if len(folded) > 80:
            return False
    return True


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--scan", default=DEFAULT_SCAN)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    scan = json.load(open(args.scan))
    con = sqlite3.connect(args.db)

    n_total = n_speech = n_kept = n_dropped = 0
    kept, dropped = [], []
    for f, rec in scan.items():
        n_total += 1
        if not rec.get("speech"):
            continue
        n_speech += 1
        if is_good(rec.get("text", ""), rec.get("no_speech_prob")):
            n_kept += 1
            kept.append((f, rec))
        else:
            n_dropped += 1
            dropped.append((f, rec))

    print(
        f"[filter] 总 {n_total} | 扫描判语音 {n_speech} | "
        f"保留 {n_kept} | 丢弃假阳性 {n_dropped}",
        file=sys.stderr,
    )
    print("\n[保留抽样]", file=sys.stderr)
    for f, rec in kept[:15]:
        print(f"  {f:14s} {rec['text']!r}", file=sys.stderr)
    print("\n[丢弃抽样]", file=sys.stderr)
    for f, rec in dropped[:15]:
        print(f"  {f:14s} nsp={rec.get('no_speech_prob')} {rec.get('text')!r}", file=sys.stderr)

    if args.dry_run:
        return

    # 备份，防止清洗出错
    import shutil

    backup = args.db + ".bak"
    shutil.copy2(args.db, backup)
    print(f"[backup] 已备份原 notes.db -> {backup}", file=sys.stderr)

    pre_existing = {r[0] for r in con.execute("SELECT file FROM notes").fetchall()}
    speech_files = {f for f, rec in scan.items() if rec.get("speech")}
    kept_files = {f for f, _ in kept}
    # 大王原有备注 = 库里原有且不在本次语音扫描范围内（如 bclovata 中文备注）
    # 这些天然不受 DELETE 影响。需清除的脏数据 = 首次扫描写入、但本次过滤丢弃的。
    to_delete = (speech_files & pre_existing) - kept_files
    if to_delete:
        con.executemany("DELETE FROM notes WHERE file = ?", [(f,) for f in to_delete])
        print(f"[clean] 删除首次扫描误写的脏备注 {len(to_delete)} 条", file=sys.stderr)

    for f, rec in kept:
        con.execute(
            "INSERT OR IGNORE INTO notes (file, note, updated_at) VALUES (?,?,?)",
            (f, rec["text"].strip(), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
        )
    con.commit()
    total_notes = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    protected = len(pre_existing - to_delete - kept_files)
    con.close()
    print(
        f"\n[done] 写入高置信语音 {n_kept} 条（保留原有备注 {protected} 条），"
        f"notes 表现共 {total_notes} 条",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
