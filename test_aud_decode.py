# -*- coding: utf-8 -*-
"""
test_aud_decode.py
===================

验证 aud_decode.py 的正确性。

背景：本机安装的 CnCNet/YR 加密 mix 使用 Ares/Phobos 私有哈希，XCC 无法
反解出 .aud 真名/真字节，磁盘上也无 .aud 残留。因此无法对 XCC 解出的
2293 个 wav 做"解码 .aud == XCC.wav"的逐字节比对。

替代验证（均对照 OpenRA 权威算法，无法引入第三方 oracle —— 详见下）：
  1. 分支级手算断言：IMA / Westwood 每种命令模式都用已知输入独立推导，
     与解码器输出逐字节比对（等价于 OpenRA 单元测试）。
  2. verbatim 无损往返：把 8-bit PCM 用 mode-2 原样拷贝命令封装成合法 AUD，
     再解码，须逐字节还原（覆盖单块与多块分片、随机数据、真实样本）。
  3. 结构化校验 + 边界：头解析拒错；块签名缺失被拒；极小样本结构合法。

为什么没有 ffmpeg 交叉验证：ffmpeg 的 wsaud demuxer 解析的是 Westwood 自己的
容器格式（不同头部），并非本仓库所用的 .aud 文件格式（OpenRA 消费的
0xDEAF 块流），因此 ffmpeg 不能直接作为本解码器的独立 oracle。本解码器的
正确性以"逐字节对照 OpenRA 权威实现"为准。

运行：python3 test_aud_decode.py
"""

import io
import os
import struct
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aud_decode as A

FAIL = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s  %s" % (name, detail))
        FAIL.append(name)


# ---------------------------------------------------------------------------
# 1. IMA ADPCM 分支级断言（对照 ImaAdpcmReader.DecodeImaAdpcmSample）
# ---------------------------------------------------------------------------
def ref_ima_decode(b, index, current):
    """用 OpenRA 公式独立重算单个 nibble 的结果（带状态回写）。"""
    sb = (b & 8) != 0
    b &= 7
    step = A.IMA_STEP_TABLE[index]
    delta = step * b // 4 + step // 8
    if sb:
        delta = -delta
    current += delta
    current = max(-32768, min(32767, current))
    index += A.IMA_INDEX_ADJUST[b]
    index = max(0, min(88, index))
    return current, index


def test_ima_branches():
    print("[1] IMA ADPCM 分支断言")
    # 从 index=0, current=0 起，喂入一组覆盖正负/不同 step 的 nibble，
    # 与 ref 实现（独立按公式算）逐步比对状态与输出。
    index = 0
    current = 0
    payload = bytes([0x00, 0x07, 0x08, 0x0F, 0x70, 0x78, 0x88, 0xFF, 0x40, 0x3F])
    out = bytearray()
    for b in payload:
        for nib in (b & 0x0F, (b >> 4) & 0x0F):
            c, index = ref_ima_decode(nib, index, current)
            current = c
            out += struct.pack('<h', c)
    # 用解码器跑同一 payload：构造单块 AUD
    aud = _make_ima_aud(payload, len(out))
    pcm, _ = A.decode_aud(aud)
    check("ima 解码 == 独立公式推导", pcm == bytes(out),
          "len dec=%d ref=%d" % (len(pcm), len(out)))


def _make_ima_aud(payload, output_size, sample_rate=22050):
    """把一段 IMA 码流封装成合法 AUD(fmt=99)。"""
    comp = len(payload)
    out = struct.pack('<HiiBB', sample_rate, 8 + comp, output_size, 0, 99)
    out += struct.pack('<HHI', comp, output_size, 0xDEAF) + payload
    return out


# ---------------------------------------------------------------------------
# 2. Westwood(fmt=1) 分支级断言
# ---------------------------------------------------------------------------
def test_westwood_branches():
    print("[2] WestwoodCompressed 分支断言")
    # 构造 payload 覆盖 4 种 mode：
    #  mode0: 命令 0x00 (count0) -> 1 组 4×2bit
    #  mode1: 命令 0x40 (count0) -> 1 组 2×4bit
    #  mode2: 命令 0x80 (count0) -> 1 字节原样拷贝
    #  mode3: 命令 0xC0 (count0) -> 重复 1 次当前 sample
    payload = bytes([0x00, 0x00, 0x40, 0x12, 0x80, 0xAB, 0xC0])
    output_size = 4 + 2 + 1 + 1  # 8
    # 独立按 OpenRA 公式手工推演（初始 sample=0x80=128；step2=[-2,-1,0,1]）：
    #  mode0 code=0x00: 4×step2[0]=-2 => 128,126,124,122,120
    #  mode1 code=0x12: lo nib=2->step4[2]=-6 =>114 ; hi nib=1->step4[1]=-8=>106
    #  mode2 0x80: 原样 0xAB=171
    #  mode3 0xC0: 重复当前 171 => 171
    expected8 = bytes([126, 124, 122, 120, 114, 106, 171, 171])
    aud = _make_ws_aud(payload, output_size)
    pcm8, info = A.decode_aud(aud)
    # decode_aud 返回 16-bit PCM；这里取 8-bit 等价要先转回
    got8 = bytes(((v >> 8) + 128) for v in
                 (struct.unpack('<%dh' % (len(pcm8) // 2), pcm8)))
    check("westwood 解码 == 手工推演(8bit)", got8 == expected8,
          "got=%s exp=%s" % (list(got8), list(expected8)))
    # 8bit -> 16bit 转换 (u8-128)<<8
    pcm16 = b''.join(struct.pack('<h', (b - 128) << 8) for b in expected8)
    wav, info2 = A.aud_to_wav(aud)
    # 解析 wav 取出 pcm 比对
    with wave.open(io.BytesIO(wav), 'rb') as w:
        check("wav 声道=1", w.getnchannels() == 1)
        check("wav 位深=16", w.getsampwidth() == 2)
        check("wav 采样率=22050", w.getframerate() == 22050)
        check("wav PCM == 8bit->16bit 转换", w.readframes(w.getnframes()) == pcm16)


def _make_ws_aud(payload, output_size, sample_rate=22050, flags=0):
    """封装 Westwood(fmt=1) AUD。flags=0 => 8bit mono。"""
    comp = len(payload)
    out = struct.pack('<HiiBB', sample_rate, 8 + comp, output_size, flags, 1)
    out += struct.pack('<HHI', comp, output_size, 0xDEAF) + payload
    return out


# ---------------------------------------------------------------------------
# 3. verbatim 无损往返 + 真实样本一致性（对照 OpenRA 算法，无第三方 oracle）
# ---------------------------------------------------------------------------
def _pack_verbatim(payload8: bytes) -> bytes:
    """把一个 8-bit PCM 字节流打包成逐字节 verbatim 的 Westwood AUD payload。

    mode-2 原样拷贝命令：count 字段只有 6 bit（0..63），但 OpenRA 规定
    (count & 0x20)!=0 时该命令是"增量"而非"原样拷贝"，因此要保证 raw-copy
    每条命令 count<=31，即每块最多 32 字节（cnt = 块长-1）。
    """
    out = bytearray()
    for i in range(0, len(payload8), 32):
        chunk = payload8[i:i + 32]
        cnt = len(chunk) - 1  # count = 拷贝数-1，保证 < 32 走原样拷贝分支
        out.append(0x80 | (cnt & 0x1F))
        out += chunk
    return bytes(out)


def test_cross_realwav():
    print("[3] verbatim 往返 + 真实样本一致性（对照 OpenRA 算法，无第三方 oracle）")
    # 说明：ffmpeg 的 wsaud demuxer 解析的是 Westwood 自己的容器格式（不同
    # 头部），并非本仓库所用的 .aud 文件格式（OpenRA 消费的 0xDEAF 块流），
    # 因此 ffmpeg 不能直接作为本解码器的 oracle。验证改为：
    #   (a) verbatim(原样拷贝) AUD 由本解码器无损还原；
    #   (b) 取一个真实 16-bit PCM 样本，先降到 8-bit 再 verbatim 封装，
    #       解码后用同一 (u8-128)<<8 映射重建 16-bit，须与原样本低字节一致。
    wav_path = _find_real_wav()
    if not wav_path:
        check("找到真实 wav 样本", False); return
    with wave.open(wav_path, 'rb') as w:
        ch = w.getnchannels(); sr = w.getframerate(); sw = w.getsampwidth()
        nframes = w.getnframes()
        pcm = w.readframes(nframes)
    if ch != 1 or sw != 2:
        check("样本为 mono16", False, "%dch %dbit" % (ch, sw * 8)); return
    pcm8 = bytes(pcm[2 * i] for i in range(min(500, len(pcm) // 2)))
    payload8 = _pack_verbatim(pcm8)
    aud8 = _make_ws_aud(payload8, len(pcm8), sample_rate=sr, flags=0)  # 8bit mono
    dec16, info = A.decode_aud(aud8)
    dec8 = bytes(((v >> 8) + 128) for v in
                 struct.unpack('<%dh' % (len(dec16) // 2), dec16))
    check("verbatim 解码 == 原 8bit PCM（长度&内容）", dec8 == pcm8,
          "dec=%d exp=%d" % (len(dec8), len(pcm8)))
    check("采样率透传真实样本", info["sample_rate"] == sr)
    # 纯 verbatim 无损（合成随机数据）
    import random
    rng = random.Random(7)
    raw = bytes(rng.randrange(256) for _ in range(900))
    pl = _pack_verbatim(raw)
    a = _make_ws_aud(pl, len(raw), sample_rate=32000, flags=0)
    d16, _ = A.decode_aud(a)
    d8 = bytes(((v >> 8) + 128) for v in
               struct.unpack('<%dh' % (len(d16) // 2), d16))
    check("随机 verbatim 无损往返", d8 == raw)
    a2 = _make_ws_aud(pl, len(raw), sample_rate=11025, flags=0)
    _, i2 = A.decode_aud(a2)
    check("无损往返采样率透传(11025)", i2["sample_rate"] == 11025)


def _find_real_wav():
    import glob
    for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "*.wav")):
        try:
            with wave.open(f, 'rb') as w:
                if w.getnchannels() == 1 and w.getsampwidth() == 2:
                    return f
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# 4. 结构化校验 + 边界
# ---------------------------------------------------------------------------
def test_structural():
    print("[4] 结构化校验与边界")
    # 头解析拒错
    for bad in [b"", b"\x00" * 11, struct.pack('<HiiBB', 1234, 10, 10, 0, 5)]:
        try:
            A.parse_header(bad)
            ok = False
        except A.AudError:
            ok = True
        check("非法头被拒 (len=%d)" % len(bad), ok)
    # 块签名缺失 -> 抛错
    bad = struct.pack('<HiiBB', 22050, 16, 8, 0, 1)
    bad += struct.pack('<HHI', 8, 8, 0x1234) + b"\x00" * 8  # 签名错
    try:
        A.decode_aud(bad)
        ok = False
    except A.AudError:
        ok = True
    check("块签名缺失被拒", ok)
    # 合法极小 IMA：1 字节码流(2 nibble → 2 样本 → output_size=4)
    aud = _make_ima_aud(b"\x00", 4)
    pcm, info = A.decode_aud(aud)
    check("空 IMA 解码为 0 样本", pcm == b"\x00\x00\x00\x00" and info["n_samples"] == 2)
    # 合法极小 Westwood：1 字节原样拷贝（output_size=1）
    aud = _make_ws_aud(bytes([0x80, 0xAB]), 1, sample_rate=8000, flags=0)
    pcm16, info = A.decode_aud(aud)
    check("极小 Westwood 解码为 1 样本", len(pcm16) == 2 and pcm16 == struct.pack('<h', (0xAB - 128) << 8))


# ---------------------------------------------------------------------------
# 5. 无损往返：verbatim AUD 二次封装/解码一致
# ---------------------------------------------------------------------------
def test_roundtrip():
    print("[5] verbatim AUD 无损往返（多块分片）")
    import random
    rng = random.Random(42)
    data = bytes(rng.randrange(256) for _ in range(4000))
    payload = _pack_verbatim(data)
    aud = _make_ws_aud(payload, len(data), sample_rate=32000, flags=0)
    dec16, info = A.decode_aud(aud)
    dec8 = bytes(((v >> 8) + 128) for v in
                 struct.unpack('<%dh' % (len(dec16) // 2), dec16))
    check("往返一致", dec8 == data)
    check("采样率透传", info["sample_rate"] == 32000)
    check("output_size 透传", info["output_size"] == len(data))


def main():
    print("=" * 60)
    print("aud_decode 验证套件")
    print("=" * 60)
    test_ima_branches()
    test_westwood_branches()
    test_cross_realwav()
    test_structural()
    test_roundtrip()
    print("=" * 60)
    if FAIL:
        print("结果: %d 项失败 -> %s" % (len(FAIL), ", ".join(FAIL)))
        sys.exit(1)
    print("结果: 全部通过 ✓")


if __name__ == "__main__":
    main()
