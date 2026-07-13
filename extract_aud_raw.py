# -*- coding: utf-8 -*-
"""
extract_aud_raw.py
==================

不依赖 MIX 文件名哈希，直接对 .mix 原始字节流做"盲扫"，定位并抽取所有
Westwood AUD 音频文件。

判断依据（来自 OpenRA AudReader.cs）：
  AUD 文件头 12 字节：
    u16  sampleRate
    i32  dataSize     (压缩后总数据长度)
    i32  outputSize   (解压后总样本字节数)
    u8   audioFlags   (0/1=mono, 2=16bit, ...)
    u8   readFormat   (1 = WestwoodCompressed, 99 = ImaAdpcm)
  之后是若干 chunk：
    u16  compressedSize
    u16  outputSize
    u32  0xdeaf        <- 强签名
    <compressedSize 字节数据>

我们用 0xdeaf 作为锚点：每个 chunk 头都含 0xdeaf，文件起始处 offset 16
就是第一个 chunk 的 0xdeaf。因此对每个 0xdeaf 位置 m，候选文件起点 p=m-16，
再用文件头多字段校验即可确定是否为合法 AUD。
"""

import os
import struct
import sys

RATES = {8000, 11025, 16000, 22050, 32000, 44100, 48000}
DEAF = b'\xaf\xde\x00\x00'


def find_aud_starts(data: bytes):
    """返回所有合法 AUD 文件起点偏移（去重、按序）。"""
    starts = []
    last_end = -1
    pos = 0
    n = len(data)
    while True:
        m = data.find(DEAF, pos)
        if m < 0:
            break
        pos = m + 1
        p = m - 16  # 候选文件起点
        if p < 0 or p <= last_end:
            continue
        # 文件头校验
        sr = struct.unpack_from('<H', data, p)[0]
        data_size = struct.unpack_from('<i', data, p + 2)[0]
        out_size = struct.unpack_from('<i', data, p + 6)[0]
        flags = data[p + 10]
        fmt = data[p + 11]
        if sr not in RATES:
            continue
        if fmt not in (1, 99):
            continue
        if flags > 3:
            continue
        if data_size <= 0 or out_size <= 0:
            continue
        if p + 12 + data_size > n:  # 数据越界
            continue
        # chunk 行走，验证结构与总长度
        cur = p + 12
        consumed = 0
        ok = True
        while cur + 8 <= n:
            csize = struct.unpack_from('<H', data, cur)[0]
            osize = struct.unpack_from('<H', data, cur + 2)[0]
            if data[cur + 4:cur + 8] != DEAF:
                ok = False
                break
            cur += 8 + csize
            consumed += csize
            if csize == 0 and osize == 0:
                break
            if consumed >= data_size:
                break
        if not ok:
            continue
        length = cur - p
        starts.append((p, length))
        last_end = p + length
    return starts


def extract_mix(mix_path: str, out_dir: str, limit=None):
    os.makedirs(out_dir, exist_ok=True)
    data = open(mix_path, 'rb').read()
    starts = find_aud_starts(data)
    if limit:
        starts = starts[:limit]
    base = os.path.splitext(os.path.basename(mix_path))[0]
    count = 0
    for i, (p, length) in enumerate(starts):
        blob = data[p:p + length]
        dst = os.path.join(out_dir, f"{base}_{p:08x}.aud")
        with open(dst, 'wb') as f:
            f.write(blob)
        count += 1
    return count, len(starts)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("mix", nargs='+', help="一个或多个 .mix 文件")
    ap.add_argument("-o", "--output", default="extracted")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    total = 0
    for m in args.mix:
        c, found = extract_mix(m, args.output, limit=args.limit)
        print(f"[ok] {os.path.basename(m)}: 检出 {found} 个 AUD 起点，写出 {c} 个")
        total += c
    print(f"[done] 共写出 {total} 个 .aud -> {args.output}")


if __name__ == "__main__":
    main()
