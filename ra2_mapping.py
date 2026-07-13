# -*- coding: utf-8 -*-
"""
Red Alert 2 / Yuri's Revenge 音效文件名 -> 兵种 / 状态 对照表。

数据来源：社区模组（modding）知识整理。
- side: soviet / allied / yuri / other
- inferred=True 表示推断项（依据 Rules.ini 内部 ID 与命名规律，非 100% 确认）

文件名约定：[兵种代码][状态后缀].AUD
解析时：先按最长匹配从右端剥掉已知 state token，剩下的字母串即 unit 前缀。
"""

# 兵种代码 -> {name_zh, name_en, side, inferred?}
UNITS = {
    # ---- 苏军步兵 ----
    "E1":    {"name_zh": "动员兵",      "name_en": "Conscript",        "side": "soviet", "inferred": False},
    "E2":    {"name_zh": "防空步兵",    "name_en": "Flak Trooper",     "side": "soviet", "inferred": False},
    "E3":    {"name_zh": "磁暴步兵",    "name_en": "Tesla Trooper",    "side": "soviet", "inferred": False},
    "IVAN":  {"name_zh": "疯狂伊万",    "name_en": "Crazy Ivan",       "side": "soviet", "inferred": False},
    "E4":    {"name_zh": "疯狂伊万(备选)", "name_en": "Crazy Ivan (alt)", "side": "soviet", "inferred": True},
    "E6":    {"name_zh": "恐怖分子",    "name_en": "Terrorist",        "side": "soviet", "inferred": False},
    "E7":    {"name_zh": "辐射工兵",    "name_en": "Desolator",        "side": "soviet", "inferred": False},

    # ---- 苏军载具 ----
    "TNK":   {"name_zh": "犀牛坦克",    "name_en": "Rhino Tank",       "side": "soviet", "inferred": False},
    "APOC":  {"name_zh": "天启坦克",    "name_en": "Apocalypse Tank",  "side": "soviet", "inferred": False},
    "V3":    {"name_zh": "V3火箭发射车","name_en": "V3 Rocket Launcher","side": "soviet", "inferred": False},
    "DRN":   {"name_zh": "恐怖机器人",  "name_en": "Terror Drone",     "side": "soviet", "inferred": True},
    "FTK":   {"name_zh": "防空履带车",  "name_en": "Flak Track",       "side": "soviet", "inferred": True},
    "HARV":  {"name_zh": "武装矿车",    "name_en": "Ore Truck",        "side": "soviet", "inferred": True},
    "DTRK":  {"name_zh": "自爆卡车",    "name_en": "Demolition Truck", "side": "soviet", "inferred": True},
    "TESLA": {"name_zh": "磁暴线圈",    "name_en": "Tesla Coil",       "side": "soviet", "inferred": True},
    "FLK":   {"name_zh": "防空炮",      "name_en": "Flak Cannon",      "side": "soviet", "inferred": True},
    "SUB":   {"name_zh": "台风潜艇",    "name_en": "Typhoon Submarine","side": "soviet", "inferred": True},
    "DRED":  {"name_zh": "无畏级战舰",  "name_en": "Dreadnought",      "side": "soviet", "inferred": True},
    "KSUB":  {"name_zh": "基洛夫空艇",  "name_en": "Kirov Airship",    "side": "soviet", "inferred": True},
    "KIROV": {"name_zh": "基洛夫空艇",  "name_en": "Kirov Airship",    "side": "soviet", "inferred": True},
    "MIG":   {"name_zh": "米格战机",    "name_en": "MiG Fighter",      "side": "soviet", "inferred": True},
    "BORIS": {"name_zh": "鲍里斯",      "name_en": "Boris",            "side": "soviet", "inferred": True},

    # ---- 盟军步兵 ----
    "GI":    {"name_zh": "美国大兵",    "name_en": "G.I.",             "side": "allied", "inferred": False},
    "SPY":   {"name_zh": "间谍",        "name_en": "Spy",              "side": "allied", "inferred": False},
    "TANYA": {"name_zh": "谭雅",        "name_en": "Tanya",            "side": "allied", "inferred": False},
    "MTNK":  {"name_zh": "灰熊坦克",    "name_en": "Grizzly Tank",     "side": "allied", "inferred": False},
    "ENG":   {"name_zh": "工程师",      "name_en": "Engineer",         "side": "allied", "inferred": True},
    "ENGR":  {"name_zh": "工程师",      "name_en": "Engineer",         "side": "allied", "inferred": True},
    "CRON":  {"name_zh": "超时空军团兵","name_en": "Chrono Legionnaire","side": "allied", "inferred": True},
    "CHR":   {"name_zh": "超时空军团兵","name_en": "Chrono Legionnaire","side": "allied", "inferred": True},
    "PRISM": {"name_zh": "光棱坦克",    "name_en": "Prism Tank",       "side": "allied", "inferred": True},
    "PTNK":  {"name_zh": "光棱坦克",    "name_en": "Prism Tank",       "side": "allied", "inferred": True},
    "RKT":   {"name_zh": "火箭飞行兵",  "name_en": "Rocketeer",        "side": "allied", "inferred": True},
    "NHK":   {"name_zh": "夜鹰直升机",  "name_en": "NightHawk",        "side": "allied", "inferred": True},
    "BEAG":  {"name_zh": "黑鹰战机",    "name_en": "Black Eagle",      "side": "allied", "inferred": True},
    "DEST":  {"name_zh": "驱逐舰",      "name_en": "Destroyer",        "side": "allied", "inferred": True},
    "CARRIER":{"name_zh": "航空母舰",   "name_en": "Aircraft Carrier", "side": "allied", "inferred": True},
    "PRIS":  {"name_zh": "光棱塔",      "name_en": "Prism Tower",      "side": "allied", "inferred": True},
    "BIGGUN":{"name_zh": "巨炮",        "name_en": "Grand Cannon",     "side": "allied", "inferred": True},

    # ---- 尤里 ----
    "YURI":  {"name_zh": "尤里复制人",  "name_en": "Yuri (Clone)",     "side": "soviet", "inferred": False},
    "YURP":  {"name_zh": "尤里X",       "name_en": "Yuri Prime",       "side": "yuri",   "inferred": False},
    "BRUTE": {"name_zh": "狂兽人",      "name_en": "Brute",            "side": "yuri",   "inferred": True},
    "VIRUS": {"name_zh": "病毒狙击手",  "name_en": "Virus",            "side": "yuri",   "inferred": True},
    "GATT":  {"name_zh": "盖特坦克",    "name_en": "Gattling Tank",    "side": "yuri",   "inferred": True},
    "LSUB":  {"name_zh": "雷鸣潜艇",    "name_en": "Laser Submarine",  "side": "yuri",   "inferred": True},
    "MIND":  {"name_zh": "精神控制车",  "name_en": "Mastermind",       "side": "yuri",   "inferred": True},
    "YGUN":  {"name_zh": "精神控制塔",  "name_en": "Psychic Tower",    "side": "yuri",   "inferred": True},
    "PSYD":  {"name_zh": "心灵控制器",  "name_en": "Psychic Dominator","side": "yuri",   "inferred": True},
    "MAG":   {"name_zh": "基因突变器",  "name_en": "Genetic Mutator",  "side": "yuri",   "inferred": True},

    # ---- 系统 / 环境 ----
    "EVA":   {"name_zh": "EVA系统语音", "name_en": "EVA Computer",     "side": "other",  "inferred": False},
    "MENU":  {"name_zh": "菜单音乐",    "name_en": "Menu Music",       "side": "other",  "inferred": False},
    "GAGRP": {"name_zh": "基地警报",    "name_en": "Base Alarm",       "side": "other",  "inferred": True},
    "INT":   {"name_zh": "过场/简报",   "name_en": "Intermission",     "side": "other",  "inferred": True},
    "EVILA": {"name_zh": "剧情语音",    "name_en": "Story Voice",      "side": "other",  "inferred": True},
    "EFX":   {"name_zh": "通用音效",    "name_en": "Generic SFX",      "side": "other",  "inferred": True},
    "THEME": {"name_zh": "背景音乐",    "name_en": "Theme Music",      "side": "other",  "inferred": True},
}

# 状态后缀 -> {label_zh, label_en}（按长度降序匹配，先剥长的）
STATES = {
    "SEL":   {"label_zh": "选中",     "label_en": "Select"},
    "MOV":   {"label_zh": "移动",     "label_en": "Move"},
    "DIE":   {"label_zh": "死亡",     "label_en": "Die"},
    "DED":   {"label_zh": "阵亡",     "label_en": "Dead"},
    "ACT":   {"label_zh": "攻击/开火","label_en": "Attack/Fire"},
    "NOW":   {"label_zh": "就绪",     "label_en": "Ready"},
    "AFLD":  {"label_zh": "在机场",   "label_en": "Airfield"},
    "CRYS":  {"label_zh": "欢呼",     "label_en": "Cheer"},
    "CHEER": {"label_zh": "欢呼",     "label_en": "Cheer"},
    "FEAR":  {"label_zh": "恐慌",     "label_en": "Panic"},
    "PANIC": {"label_zh": "恐慌",     "label_en": "Panic"},
    "CTRL":  {"label_zh": "被控制",   "label_en": "Under Control"},
    "HELP":  {"label_zh": "求救",     "label_en": "Help"},
    "GIDD":  {"label_zh": "嘲笑",     "label_en": "Laugh"},
    # 单字母确认语音（需特殊处理，见解析逻辑）
}

# 单字母确认语音：A/B/C/D 表示第 N 句确认台词
SINGLE_LETTER_STATES = {
    "A": "确认语音1", "B": "确认语音2", "C": "确认语音3", "D": "确认语音4",
}

# 阵营展示顺序与中文名
SIDES = [
    ("soviet", "苏军"),
    ("allied", "盟军"),
    ("yuri",   "尤里"),
    ("other",  "系统 / 环境"),
]
