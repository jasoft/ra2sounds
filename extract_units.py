# -*- coding: utf-8 -*-
"""
extract_units.py  (v3 - 真·递归嵌套 + 向量盲扫)
============================================

目标：从**原版** RA2 / YR 的 .mix 里，递归拆出所有单位音效 AUD。

实测结论（v2 之后）：
  * CnCNet 的 ra2md.mix 用 Ares/Phobos 私有哈希，XCC db 对不上 → 跳过。
  * 原版 ra2.mix 是**明文 MIX（未加密）**，顶层含 ~1189 个
    **明文嵌套子 MIX**；音效就藏在这些子包里（2~3 层深）。
  * 思路：对每个子 MIX 的 content 做**向量化盲扫 0xdeaf 锚点**
    （锚点-16 处须是合法样本率 + fmt∈{1,99} + flags<=3），
    再走 chunk 校验抠出真实 AUD。

严校验 try_mix_head：任何 entry 越界即判假 MIX（避免把
大块地图数据误判成子包）。
"""

import os
import struct
import argparse

import numpy as np
import extract_ra2_sounds as E

RATES = np.array([8000, 11025, 16000, 22050, 32000, 44100, 48000], dtype=np.uint16)
_SEEN = set()


def try_mix_head(data):
    """若是合法明文 MIX 头返回 entries dict，否则 None（严校验）。"""
    n = len(data)
    if n < 6:
        return None
    is_cnc = int.from_bytes(data[0:2], 'little') != 0
    if is_cnc:
        ho = 0
        is_enc = False
    else:
        flags = int.from_bytes(data[2:4], 'little')
        is_enc = (flags & 0x2) != 0
        ho = 4
    if is_enc:
        return None
    num = int.from_bytes(data[ho:ho + 2], 'little')
    if num <= 0 or num > 50000:
        return None
    entries = {}
    pos = ho + 6
    data_start = ho + 6 + num * 12
    max_end = 0
    for _ in range(num):
        if pos + 12 > n:
            return None
        h = int.from_bytes(data[pos:pos + 4], 'little')
        o = int.from_bytes(data[pos + 4:pos + 8], 'little')
        l = int.from_bytes(data[pos + 8:pos + 12], 'little')
        entries[h] = (o, l)
        pos += 12
        if o < 0 or l < 0 or data_start + o + l > n:
            return None
        max_end = max(max_end, data_start + o + l)
    if max_end > n + 64:
        return None
    return entries


def find_aud_in_block(data):
    """在一段 MIX 块 data 里向量化盲扫真实 AUD 起点。返回 [(off,length)]。"""
    n = len(data)
    if n < 20:
        return []
    d = np.frombuffer(data, dtype=np.uint8)
    marks = np.where((d[:-3] == 0xaf) & (d[1:-2] == 0xde) & (d[2:-1] == 0) & (d[3:] == 0))[0]
    if len(marks) == 0:
        return []
    p = marks.astype(np.int64) - 16
    p = p[p >= 0]
    if len(p) == 0:
        return []
    sr = (d[p].astype(np.uint16) << 8) | d[p + 1].astype(np.uint16)
    fmt = d[p + 11]
    flags = d[p + 10]
    ok = np.isin(sr, RATES) & np.isin(fmt, [1, 99]) & (flags <= 3)
    cand = p[ok]
    results = []
    for pp in cand.tolist():
        cur = pp + 12
        consumed = 0
        good = True
        step = 0
        while cur + 8 <= n and step < 500:
            if d[cur] != 0xaf or d[cur + 1] != 0xde or d[cur + 2] != 0 or d[cur + 3] != 0:
                good = False
                break
            csize = (d[cur + 4].astype(np.uint16) << 8) | d[cur + 5].astype(np.uint16)
            osize = (d[cur + 6].astype(np.uint16) << 8) | d[cur + 7].astype(np.uint16)
            cur += 8 + csize
            consumed += csize
            step += 1
            if csize == 0 and osize == 0:
                break
            if step >= 200:
                break
        if good:
            length = cur - pp
            if 0 < length <= n - pp:
                results.append((pp, length))
    return results


def extract_block(data, out_dir, label, stats):
    """处理一段块：若是 MIX 递归下钻，否则盲扫 AUD 导出。"""
    fp = (id(data), len(data))
    if fp in _SEEN:
        return
    _SEEN.add(fp)

    entries = try_mix_head(data)
    if entries is not None:
        for h, (o, l) in entries.items():
            if o < 0 or o + l > len(data) or l <= 0:
                continue
            stats['nested'] += 1
            extract_block(data[o:o + l], out_dir, f"{label}_{h:08x}", stats)
        return

    found = find_aud_in_block(data)
    for off, length in found:
        blob = data[off:off + length]
        h = struct.unpack_from('<I', blob, 0)[0] if len(blob) >= 4 else 0
        name = f"{label}_{h:08x}.aud"
        path = os.path.join(out_dir, name)
        if os.path.exists(path) and os.path.getsize(path) == length:
            continue
        with open(path, 'wb') as f:
            f.write(blob)
        stats['aud'] += 1


def extract_mix_file(mix_path, out_dir):
    _SEEN.clear()
    stats = {'aud': 0, 'nested': 0}
    arc = E.MixArchive(mix_path)
    base = os.path.splitext(os.path.basename(mix_path))[0]
    for h, (o, l) in arc.entries.items():
        blob = arc.get_content(o, l)
        if len(blob) <= 0:
            continue
        stats['nested'] += 1
        extract_block(blob, out_dir, f"{base}_{h:08x}", stats)
    return stats


def main():
    ap = argparse.ArgumentParser(description="递归解包原版 .mix，向量化盲扫导出单位音效 AUD。")
    ap.add_argument("mix", nargs='+')
    ap.add_argument("-o", "--output", default="extracted_units")
    args = ap.parse_args()
    for m in args.mix:
        print(f"[*] {m}")
        st = extract_mix_file(m, args.output)
        print(f"    导出 AUD={st['aud']}  下钻块={st['nested']}")


if __name__ == "__main__":
    main()
