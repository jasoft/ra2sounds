#!/usr/bin/env python3
"""RA2 音效语音检测 + 英文转写，结果写入 notes.db。

只把「确实含有真人语音」的音效识别出来，把英文转写文本写入 notes 表的
note 字段（纯英文，按大王要求暂不翻译）。判定依据是 whisper 的
no_speech_prob：纯攻击音效 / 环境音效会返回 0 个 segment 或极高的
no_speech_prob，一律跳过，不写备注。

扫描范围：sounds/*.wav 与 sounds/taunts/*.wav（不含 bgm 背景音乐）。
已存在的 notes 行不会被覆盖（INSERT OR IGNORE）。

扫描结果还会持久化到 voice_scan.json，记录每个文件的 speech 判定与
no_speech_prob，供后续翻译 / 复查使用，并支持断点续传。
"""

import argparse
import glob
import json
import os
import sqlite3
import sys
import time

import mlx_whisper

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(ROOT, "notes.db")
DEFAULT_SCAN = os.path.join(ROOT, "voice_scan.json")
SPEECH_THRESHOLD = 0.5  # no_speech_prob 低于此值才视为有人声


def find_wavs(sounds_dir):
    wavs = []
    for top in ("", "taunts"):
        d = os.path.join(sounds_dir, top) if top else sounds_dir
        for f in sorted(glob.glob(os.path.join(d, "*.wav"))):
            rel = os.path.basename(f)
            wavs.append((rel, f))
    return wavs


def is_speech(result, threshold):
    segs = result.get("segments") or []
    if not segs:
        return False
    nsp = max(s.get("no_speech_prob", 1.0) for s in segs)
    text = (result.get("text") or "").strip()
    return nsp < threshold and bool(text)


def open_db(path):
    con = sqlite3.connect(path)
    con.execute(
        """CREATE TABLE IF NOT EXISTS notes (
               file TEXT PRIMARY KEY,
               note TEXT NOT NULL DEFAULT '',
               updated_at TEXT NOT NULL)"""
    )
    return con


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sounds-dir", default=os.path.join(ROOT, "sounds"))
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--scan", default=DEFAULT_SCAN)
    ap.add_argument("--model", default="mlx-community/whisper-base.en-mlx")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 个（试跑）")
    ap.add_argument("--speech-threshold", type=float, default=SPEECH_THRESHOLD)
    ap.add_argument("--no-write-notes", action="store_true", help="只扫描不写库")
    ap.add_argument("--overwrite-scan", action="store_true", help="忽略断点续传全量重扫")
    args = ap.parse_args()

    wavs = find_wavs(args.sounds_dir)
    if args.limit:
        wavs = wavs[: args.limit]

    # 断点续传：已扫描过的跳过
    scan = {}
    if os.path.exists(args.scan) and not args.overwrite_scan:
        try:
            scan = json.load(open(args.scan))
            print(f"[scan] 载入已有扫描记录 {len(scan)} 条", file=sys.stderr)
        except Exception as e:
            print(f"[scan] 载入失败，忽略：{e}", file=sys.stderr)

    pending = [(rel, f) for rel, f in wavs if rel not in scan]
    print(f"[scan] 总文件 {len(wavs)}，待处理 {len(pending)}", file=sys.stderr)

    con = open_db(args.db)
    n_speech = sum(1 for v in scan.values() if v.get("speech"))
    n_done = 0
    t0 = time.time()
    flush_every = 50

    try:
        for rel, f in pending:
            try:
                r = mlx_whisper.transcribe(f, language="en")
                speech = is_speech(r, args.speech_threshold)
                text = (r.get("text") or "").strip()
                segs = r.get("segments") or []
                nsp = max((s.get("no_speech_prob", 1.0) for s in segs), default=None)
                rec = {
                    "speech": speech,
                    "text": text,
                    "no_speech_prob": nsp,
                    "duration": round(len(segs) and segs[-1].get("end", 0.0), 2),
                }
            except Exception as e:
                rec = {"speech": False, "text": "", "error": str(e)}
                speech = False
                text = ""

            scan[rel] = rec

            if speech and text and not args.no_write_notes:
                con.execute(
                    "INSERT OR IGNORE INTO notes (file, note, updated_at) VALUES (?,?,?)",
                    (rel, text, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                )
                con.commit()
                n_speech += 1

            n_done += 1
            if n_done % flush_every == 0 or n_done == len(pending):
                json.dump(scan, open(args.scan, "w"), ensure_ascii=False)
                dt = time.time() - t0
                rate = n_done / dt if dt else 0
                print(
                    f"[scan] {n_done}/{len(pending)}  "
                    f"语音 {n_speech}  速率 {rate:.1f}/s  ETA {dt/rate*(len(pending)-n_done):.0f}s",
                    file=sys.stderr,
                )
    finally:
        json.dump(scan, open(args.scan, "w"), ensure_ascii=False)
        con.commit()
        con.close()

    # 汇总
    total = len(scan)
    speech_files = [k for k, v in scan.items() if v.get("speech")]
    print(
        f"\n[done] 扫描 {total} 文件，其中含真人语音 {len(speech_files)} 个"
        f"（已写入 notes.db）。",
        file=sys.stderr,
    )
    if speech_files:
        print("[samples]", file=sys.stderr)
        for k in speech_files[:8]:
            print(f"  {k}: {scan[k]['text']!r}", file=sys.stderr)


if __name__ == "__main__":
    main()
