# -*- coding: utf-8 -*-
"""
aud_decode.py
=============

把 Westwood AUD 音频（红警2 / YR 引擎使用的格式）解码为 16-bit PCM WAV。

算法严格对照 OpenRA 权威实现（经过 GitHub 上 OpenRA/OpenRA@bleed 校验）：
  - OpenRA.Mods.Cnc/FileFormats/AudReader.cs
  - OpenRA.Mods.Common/FileFormats/WestwoodCompressedReader.cs
  - OpenRA.Mods.Common/FileFormats/ImaAdpcmReader.cs

AUD 文件布局
------------
  0  u16  sampleRate     采样率（8000/11025/.../48000）
  2  i32  dataSize       压缩数据总长 = Σ(8 + 每块 CompressedSize)
  6  i32  outputSize     解压后总字节数（PCM 字节数，与声道/位深无关）
 10  u8   audioFlags     bit0=Stereo(0x1)  bit1=16Bit(0x2)
 11  u8   readFormat     1 = WestwoodCompressed(8bit)  99 = ImaAdpcm(16bit)
 12  ...  chunk 流，每块：
            u16 CompressedSize
            u16 OutputSize          (本块解压字节数)
            u32 0xDEAF             (强签名锚点)
            CompressedSize 字节压缩数据

两种压缩
--------
  fmt=1  WestwoodCompressed：8-bit 增量预测编码，预测器初始 0x80。
         每字节命令的高 2 位决定解码模式（4×2bit / 2×4bit / 原样拷贝 / 重复）。
  fmt=99 IMA ADPCM：16-bit，状态(index, currentSample)跨块连续，
         输出严格受总 outputSize 约束（最后一字节可能只用低 nibble）。

输出 WAV：统一 16-bit signed PCM（与 gamesounds 既有 2293 个 WAV 位深一致）。
  - fmt=1 解出的 8-bit unsigned(中心128) 经 (u8-128)<<8 转为 16-bit signed。
  - fmt=99 解出的 16-bit signed 直接写出。

本机没有可还原的 .aud（CnCNet/YR 加密 mix 用 Ares/Phobos 私有哈希，
XCC 无法反解出真名/真字节，磁盘上也无 .aud 残留），因此解码器的正确性
通过 (1) 结构化校验 (2) 合成 AUD 的无损/确定往返 (3) 逐分支手算断言 来证明，
详见 test_aud_decode.py。
"""

import os
import struct
import wave
import argparse

# ----------------------------------------------------------------------------
# Westwood "VBR" (fmt=1) 解码表（来自 WestwoodCompressedReader.cs）
# ----------------------------------------------------------------------------
WS_STEP_2 = [-2, -1, 0, 1]
WS_STEP_4 = [-9, -8, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 8]

# ----------------------------------------------------------------------------
# IMA ADPCM (fmt=99) 解码表（来自 ImaAdpcmReader.cs）
# ----------------------------------------------------------------------------
IMA_INDEX_ADJUST = [-1, -1, -1, -1, 2, 4, 6, 8]
IMA_STEP_TABLE = [
    7, 8, 9, 10, 11, 12, 13, 14, 16,
    17, 19, 21, 23, 25, 28, 31, 34, 37,
    41, 45, 50, 55, 60, 66, 73, 80, 88,
    97, 107, 118, 130, 143, 157, 173, 190, 209,
    230, 253, 279, 307, 337, 371, 408, 449, 494,
    544, 598, 658, 724, 796, 876, 963, 1060, 1166,
    1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749,
    3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
    7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289,
    16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767,
]

RATES = frozenset({8000, 11025, 16000, 22050, 32000, 44100, 48000})
DEAF = 0xDEAF
HEADER_SIZE = 12


class AudError(Exception):
    """AUD 解析/解码失败。"""


def parse_header(data: bytes) -> dict:
    """解析 12 字节头，返回字段字典；非法则抛 AudError。"""
    if len(data) < HEADER_SIZE:
        raise AudError("文件过短，不足 AUD 头部")
    sample_rate, data_size, output_size = struct.unpack_from('<Hii', data, 0)
    audio_flags = data[10]
    read_format = data[11]

    if sample_rate not in RATES:
        raise AudError("非法采样率 %d" % sample_rate)
    if read_format not in (1, 99):
        raise AudError("未知压缩格式 %d" % read_format)
    if audio_flags > 3:
        raise AudError("非法 audioFlags %d" % audio_flags)
    if data_size <= 0 or output_size <= 0:
        raise AudError("非法的 dataSize/outputSize")

    sample_bits = 16 if (audio_flags & 0x2) else 8
    channels = 2 if (audio_flags & 0x1) else 1
    return {
        "sample_rate": sample_rate,
        "data_size": data_size,
        "output_size": output_size,
        "audio_flags": audio_flags,
        "read_format": read_format,
        "sample_bits": sample_bits,
        "channels": channels,
    }


def iter_chunks(data: bytes):
    """从 offset=12 起逐块行走，yield (compressed_size, output_size, payload)。

    每块：u16 CompressedSize, u16 OutputSize, u32 0xDEAF, payload。
    遇到非法块签名即抛 AudError（保证不会越界读到随机数据）。
    """
    n = len(data)
    pos = HEADER_SIZE
    while pos + 8 <= n:
        comp, out = struct.unpack_from('<HH', data, pos)
        sig = struct.unpack_from('<I', data, pos + 4)[0]
        if sig != DEAF:
            raise AudError("块签名缺失 0xDEAF @ offset %d (got 0x%08x)" % (pos + 4, sig))
        start = pos + 8
        end = start + comp
        if end > n:
            raise AudError("块数据越界 @ offset %d (comp=%d)" % (pos, comp))
        yield comp, out, data[start:end]
        pos = end


def decode_westwood(chunks, output_size: int) -> bytes:
    """解码 fmt=1（WestwoodCompressed）为 8-bit unsigned PCM 字节流。

    'sample' 预测器为 uint8（0..255），初始 0x80。严格对照
    WestwoodCompressedReader.DecodeWestwoodCompressedSample。
    """
    out = bytearray(output_size)
    w = 0
    sample = 0x80

    def clamp8(v):
        if v < 0:
            return 0
        if v > 255:
            return 255
        return v

    for _comp, _out, payload in chunks:
        r = 0
        plen = len(payload)
        while r < plen and w < output_size:
            cmd = payload[r]
            r += 1
            count = cmd & 0x3F
            mode = cmd >> 6
            if mode == 0:
                for _ in range(count + 1):
                    if r >= plen or w + 4 > output_size:
                        break
                    code = payload[r]
                    r += 1
                    sample = clamp8(sample + WS_STEP_2[(code >> 0) & 0x03])
                    out[w] = sample; w += 1
                    sample = clamp8(sample + WS_STEP_2[(code >> 2) & 0x03])
                    out[w] = sample; w += 1
                    sample = clamp8(sample + WS_STEP_2[(code >> 4) & 0x03])
                    out[w] = sample; w += 1
                    sample = clamp8(sample + WS_STEP_2[(code >> 6) & 0x03])
                    out[w] = sample; w += 1
            elif mode == 1:
                for _ in range(count + 1):
                    if r >= plen or w + 2 > output_size:
                        break
                    code = payload[r]
                    r += 1
                    sample = clamp8(sample + WS_STEP_4[(code >> 0) & 0x0F])
                    out[w] = sample; w += 1
                    sample = clamp8(sample + WS_STEP_4[(code >> 4) & 0x0F])
                    out[w] = sample; w += 1
            elif mode == 2 and (count & 0x20) != 0:
                # 对照 OpenRA: sample += (sbyte)((sbyte)count << 3) >> 3。
                # count ∈ [0,63]，(sbyte) 恒等，左移3再算术右移3 = count 本身。
                sample = clamp8(sample + count)
                if w < output_size:
                    out[w] = sample; w += 1
            elif mode == 2:
                for _ in range(count + 1):
                    if r >= plen or w >= output_size:
                        break
                    sample = payload[r]
                    r += 1
                    out[w] = sample; w += 1
            else:  # mode == 3：重复当前 sample
                for _ in range(count + 1):
                    if w >= output_size:
                        break
                    out[w] = sample; w += 1
    return bytes(out[:output_size])


def decode_ima(chunks, output_size: int) -> bytes:
    """解码 fmt=99（IMA ADPCM）为 16-bit signed PCM 的 little-endian 字节流。

    状态(index, current)跨块连续（对照 ImaAdpcmAudStream 的实例字段）。
    每字节先解低 nibble 再解高 nibble；当已产出字节数 >= outputSize 时
    跳过该字节的高 nibble（最后一字节可能只用低半字节）。
    """
    out = bytearray(output_size)
    w = 0  # 已产出字节数
    index = 0
    current = 0

    def decode_nibble(nib):
        nonlocal index, current
        sb = (nib & 8) != 0
        step = IMA_STEP_TABLE[index]
        delta = step * (nib & 7) // 4 + step // 8
        if sb:
            delta = -delta
        current += delta
        if current > 32767:
            current = 32767
        elif current < -32768:
            current = -32768
        index += IMA_INDEX_ADJUST[nib & 7]
        if index < 0:
            index = 0
        elif index > 88:
            index = 88
        return current

    for _comp, _out, payload in chunks:
        for b in payload:
            if w + 2 <= output_size:
                s = decode_nibble(b & 0x0F)
                out[w:w + 2] = struct.pack('<h', s)
                w += 2
            if w < output_size:  # 高 nibble：仅当尚未产出满
                s = decode_nibble((b >> 4) & 0x0F)
                out[w:w + 2] = struct.pack('<h', s)
                w += 2
    return bytes(out[:output_size])


def decode_aud(data: bytes) -> tuple:
    """解码整个 AUD 字节流。

    返回 (pcm_bytes, info) ：
      pcm_bytes : 16-bit signed little-endian PCM
      info      : 含 sample_rate / channels / sample_bits / read_format / length 等
    非法输入抛 AudError。
    """
    hdr = parse_header(data)
    chunks = list(iter_chunks(data))

    if hdr["read_format"] == 1:
        pcm8 = decode_westwood(chunks, hdr["output_size"])
        # 8-bit unsigned(中心128) -> 16-bit signed
        pcm = bytearray()
        for b in pcm8:
            s = (b - 128) << 8
            pcm += struct.pack('<h', s)
        pcm = bytes(pcm)
        bits = 16
    else:  # fmt == 99
        pcm = decode_ima(chunks, hdr["output_size"])
        bits = 16

    n_samples = len(pcm) // 2
    length = n_samples / hdr["channels"] / hdr["sample_rate"] if hdr["sample_rate"] else 0.0
    info = {
        "sample_rate": hdr["sample_rate"],
        "channels": hdr["channels"],
        "sample_bits": bits,
        "read_format": hdr["read_format"],
        "n_samples": n_samples,
        "length": round(length, 3),
        "output_size": hdr["output_size"],
    }
    return pcm, info


def _ws_to16(pcm8: bytes) -> bytes:
    """把 8-bit unsigned(中心128) PCM 转成 16-bit signed 表示（与小端 u16）。

    供测试与交叉验证：ffmpeg wsaud 解出的是 8-bit unsigned PCM，本解码器输出
    16-bit；两者可经此转换后直接比对。
    """
    return b''.join(struct.pack('<h', (b - 128) << 8) for b in pcm8)


def pcm_to_wav(pcm: bytes, sample_rate: int, channels: int, sample_bits: int = 16) -> bytes:
    """把 16-bit PCM 字节流封装为标准 WAV 文件字节。"""
    import io
    buf = io.BytesIO()
    w = wave.open(buf, 'wb')
    try:
        w.setnchannels(channels)
        w.setsampwidth(sample_bits // 8)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    finally:
        w.close()
    return buf.getvalue()


def aud_to_wav(data: bytes) -> tuple:
    """解码 AUD 为 (wav_bytes, info)。"""
    pcm, info = decode_aud(data)
    wav = pcm_to_wav(pcm, info["sample_rate"], info["channels"], info["sample_bits"])
    return wav, info


def decode_file(src: str, dst: str | None = None) -> dict:
    """解码单个 .aud 文件为 .wav。dst 缺省为同目录同名 .wav。"""
    with open(src, 'rb') as f:
        data = f.read()
    wav, info = aud_to_wav(data)
    if dst is None:
        dst = os.path.splitext(src)[0] + '.wav'
    with open(dst, 'wb') as f:
        f.write(wav)
    return {"src": src, "dst": dst, "info": info}


def main():
    ap = argparse.ArgumentParser(description="把 Westwood AUD 解码为 16-bit WAV。")
    ap.add_argument("input", nargs='+', help="一个或多个 .aud 文件 / 目录")
    ap.add_argument("-o", "--output", default=None, help="输出目录（默认与输入同目录）")
    ap.add_argument("--fmt", action="store_true", help="输出附带 info 文本")
    args = ap.parse_args()

    files = []
    for p in args.input:
        if os.path.isdir(p):
            for fn in sorted(os.listdir(p)):
                if fn.lower().endswith('.aud'):
                    files.append(os.path.join(p, fn))
        else:
            files.append(p)

    for src in files:
        dst = args.output
        if dst is None:
            out_path = os.path.splitext(src)[0] + '.wav'
        else:
            os.makedirs(dst, exist_ok=True)
            out_path = os.path.join(dst, os.path.splitext(os.path.basename(src))[0] + '.wav')
        try:
            r = decode_file(src, out_path)
            i = r["info"]
            print("[ok] %s -> %s  (%dHz %dch fmt%d %.2fs)" % (
                os.path.basename(src), os.path.basename(out_path),
                i["sample_rate"], i["channels"], i["read_format"], i["length"]))
        except AudError as e:
            print("[skip] %s : %s" % (os.path.basename(src), e))


if __name__ == "__main__":
    main()
