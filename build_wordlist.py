# -*- coding: utf-8 -*-
"""
build_wordlist.py
==================

生成红警 2 / YR 的"可能音效文件名"总表（wordlist）。

用途：把这份清单里的每个文件名算出 Classic / CRC32 哈希，
去解密后的 ra2md.mix entry 表反查，就能把哈希还原成
  E1AUD.AUD / TNKDIE.AUD 这种**真名**（等价于 XCC 的 global mix database）。

命名规律（RA2/YR 引擎约定）：
  [兵种代码][状态/语音序号].AUD
  兵种代码见下；状态后缀见下；部分单位语音用 V1..V9 表示第 N 句。
"""

# ---- 兵种 / 系统 代码（来自 ra2_mapping.py + 社区补全）----
UNITS = [
    # 苏军步兵
    "E1","E2","E3","E4","E6","E7",
    "IVAN",
    # 苏军载具
    "TNK","APOC","V3","DRN","FTK","HARV","DTRK","TESLA","FLK","SUB","DRED",
    "KSUB","KIROV","MIG","BORIS",
    # 盟军步兵
    "GI","SPY","TANYA","MTNK","ENG","ENGR","CRON","CHR",
    # 盟军载具
    "PRISM","PTNK","RKT","NHK","BEAG","DEST","CARRIER","PRIS","BIGGUN",
    # 尤里
    "YURI","YURP","BRUTE","VIRUS","GATT","LSUB","MIND","YGUN","PSYD","MAG",
    # 系统 / 剧情
    "EVA","MENU","GAGRP","INT","EVILA","EFX","THEME",
    # 其他常见
    "AMMO","BARL","CRUS","DOG","SNIP","SEAL","SHK","SCSI","HTK","SCUBA",
    "FTRK","FTNK","MCMA","MCMV","MNNK","MGTK","MCAR","MMIN","MSAM","MSH","MSUB",
    "MSPA","MSPYP","MTNKR","MFTK","MSUB","MGTK","APOCP","APOCC","APOCT",
    "APOCM","APOCA","APOCB","YURIM","YURIC","YURIP","YURIV","YURIT",
    "E1E","E1C","E1F","E2E","E2C","E3E","E3C","TNKF","TNKE","TNKC",
    "APOCE","APOCC2","IVANE","IVANC","GISE","GISELECT","GIC","SPYE","SPYC",
    "TANYAE","TANYAC","YURIE","YURIC2","YURIPE","YURIP","YURIV2",
]

# ---- 状态 / 语音 后缀 ----
STATES = [
    "AUD",          # 通用语音包（最强特征）
    "SEL","MOV","DIE","DED","ACT","NOW","AFLD","CRYS","CHEER",
    "FEAR","PANIC","CTRL","HELP","GIDD",
    # 单字母确认语音（第 1~4 句）
    "A","B","C","D",
    # 数字序号语音（V1..V9 表示第 N 句）
    "V1","V2","V3","V4","V5","V6","V7","V8","V9",
    # 通用后缀
    "1","2","3","4","5","6","7","8","9",
]

# ---- 一些完整已知文件名（直接列，提高命中）----
EXTRAS = [
    "E1AUD.AUD","E2AUD.AUD","E3AUD.AUD","E4AUD.AUD","E6AUD.AUD","E7AUD.AUD",
    "IVANAUD.AUD","GIAUD.AUD","SPYAUD.AUD","TANYAAUD.AUD",
    "TNKDIE.AUD","APOCV1.AUD","APOCV2.AUD","YURIC.AUD","YURIP.AUD",
    "E1SEL.AUD","E1MOV.AUD","E1DIE.AUD","GISEL.AUD","GIMOV.AUD",
    "EVAMENU.AUD","MENUMUS.AUD","THEME1.AUD","INTRO1.AUD",
    "E1A.AUD","E1B.AUD","E1C.AUD","E1D.AUD","GI A.AUD","GI B.AUD",
    "TNK A.AUD","TNK B.AUD","APOC A.AUD","YURI A.AUD","YURI B.AUD",
    "E1V1.AUD","E1V2.AUD","E1V3.AUD","E1V4.AUD","E1V5.AUD",
    "GIV1.AUD","GIV2.AUD","GIV3.AUD","TNV1.AUD","APOCV3.AUD",
]


def build():
    wl = set()
    # [unit][state].AUD
    for u in UNITS:
        for s in STATES:
            wl.add(f"{u}{s}.AUD")
        wl.add(f"{u}.AUD")
    # 补：部分单位是 [unit]_[state] 或 [unit][state] 不带 .AUD 尾
    for e in EXTRAS:
        wl.add(e)
    # 一些无前缀的系统音
    for s in ["MENU.AUD","EVA.AUD","GAGRP.AUD","INT.AUD","EVILA.AUD","EFX.AUD","THEME.AUD"]:
        wl.add(s)
    return sorted(wl)


if __name__ == "__main__":
    w = build()
    print(f"# wordlist size: {len(w)}")
    for x in w[:40]:
        print(x)
