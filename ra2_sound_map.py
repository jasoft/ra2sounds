# -*- coding: utf-8 -*-
"""
ra2_sound_map.py
====================
Red Alert 2 / Yuri's Revenge 音效文件名 -> 兵种 / 语音类型 的【权威对照表】。

数据来源（按可信度排序）：
  1. 原版 Yuri's Revenge 的 soundmd.ini + rulesmd.ini
     （来源：CnCNet/cncnet-yr-client-package 的 develop 分支，游戏原始文件）——
     其中 rulesmd.ini 把每个单位绑定到语音事件，soundmd.ini 再给出语音事件对应的
     真实音效文件名，这是最高权威。
  2. OpenRA ra2 mod 的 audio/voices.yaml——用于交叉核对步兵语音组。
  3. 实际提取的 sounds/ 文件与 Westwood 官方命名规律相互印证。

Westwood 官方音效命名规则：
  文件名 = [前缀1字母][兵种代码2~4字母][语音类型2~3字母][序号字母 a~g]
  前缀: i=步兵  v=载具/空军  a=环境/动物  u=界面/系统  b=建筑  g=建筑/通用
        s=超级武器  x/t/c=资料片/音乐/剧情语音
  语音类型: mo/mob/moc=移动  se/sel/sea...=选中  att/ata/atb...=攻击
           fe/fed/fee...=受惊  di/die/dia...=死亡  sta=启动  cra=坠毁
           dep=部署  go=收矿返回  ha=收割  cha=充电  sha=爆炸破片
           lo=循环  on/off=开关  tele=传送  etc.

以「(前缀, 兵种代码)」为键来避免歧义：例如 "fla" 在 i+fla=防空步兵、v+fla=防空履带车、
b+fla=防空炮里分别对应不同单位。
"""

# ---------------------------------------------------------------------------
# 前缀 -> (proto 类, 中文大类)
# ---------------------------------------------------------------------------
PREFIX = {
    "i": ("infantry", "步兵"),
    "v": ("vehicle",  "载具 / 空军"),
    "a": ("ambient",  "环境 / 动物"),
    "u": ("ui",       "界面 / 系统"),
    "b": ("building", "建筑 (苏/尤)"),
    "g": ("building", "建筑 / 通用"),
    "s": ("support",  "超级武器 / 支援"),
    "x": ("expansion","资料片附加"),
    "t": ("expansion","资料片附加"),
    "c": ("expansion","资料片附加"),
}

# ---------------------------------------------------------------------------
# 语音类型 token -> 中文标签
# ---------------------------------------------------------------------------
VOICE_TYPE = {
    "mo": "移动", "mob": "移动", "moc": "移动", "mod": "移动", "moe": "移动", "moa": "移动",
    "se": "选中", "sea": "选中", "seb": "选中", "sec": "选中", "sed": "选中", "sel": "选中",
    "see": "发现敌人",
    "att": "攻击", "at": "攻击指令", "ata": "攻击", "atb": "攻击", "atc": "攻击", "atd": "攻击",
    "ate": "攻击", "atf": "攻击", "atg": "攻击", "ath": "攻击", "attd": "攻击", "atte": "攻击",
    "fe": "受惊", "fed": "受击", "fee": "受击", "feb": "受击", "fec": "受击",
    "di": "死亡", "die": "死亡", "dia": "死亡", "dib": "死亡", "dic": "死亡", "did": "死亡",
    "diea": "死亡", "dieb": "死亡", "diec": "死亡", "died": "死亡", "dief": "死亡",
    "sta": "启动移动", "staa": "启动移动", "stab": "启动移动", "stac": "启动移动",
    "cra": "坠毁", "pow": "断电",
    "dep": "部署", "go": "收矿返回", "ha": "收割", "cha": "充电", "sha": "爆炸破片",
    "lo": "循环音", "on": "开启", "of": "关闭", "open": "开启",
    "tele": "传送", "read": "读取", "laun": "发射", "expl": "爆炸", "intr": "过场",
    "def": "防御", "dom": "心灵主宰", "rev": "反转", "snuk": "核弹",
    "up": "上升", "down": "下降", "mov": "移动", "act": "动作",
    "now": "就绪",
    "ex": "特殊攻击", "kill": "击杀",
}

# 用于后缀剥离（最长优先）
_TYPE_TOKENS = sorted(VOICE_TYPE.keys(), key=len, reverse=True)

# ---------------------------------------------------------------------------
# 核心表： (前缀, 兵种代码) -> (中文名, 英文名, side, proto)
#   side: soviet / allied / yuri / other
#   proto: infantry / vehicle / building / ambient / ui / support
# ---------------------------------------------------------------------------
U = {
    # ===================== 步兵 i =====================
    ("i", "gi"):   ("美国大兵", "G.I.", "allied", "infantry"),
    ("i", "ggi"):  ("重装大兵", "Guardian GI", "allied", "infantry"),
    ("i", "con"):  ("动员兵", "Conscript", "soviet", "infantry"),
    ("i", "fla"):  ("防空步兵", "Flak Trooper", "soviet", "infantry"),
    ("i", "tes"):  ("磁暴步兵", "Tesla Trooper", "soviet", "infantry"),
    ("i", "cra"):  ("疯狂伊万", "Crazy Ivan", "soviet", "infantry"),
    ("i", "des"):  ("辐射工兵", "Desolator", "soviet", "infantry"),
    ("i", "ter"):  ("恐怖分子", "Terrorist", "soviet", "infantry"),
    ("i", "sni"):  ("狙击手", "Sniper", "soviet", "infantry"),
    ("i", "bor"):  ("鲍里斯", "Boris", "soviet", "infantry"),
    ("i", "dog"):  ("军犬", "Attack Dog", "soviet", "infantry"),
    ("i", "spy"):  ("间谍", "Spy", "allied", "infantry"),
    ("i", "chr"):  ("超时空军团兵", "Chrono Legionnaire", "allied", "infantry"),
    ("i", "roc"):  ("火箭飞行兵", "Rocketeer", "allied", "infantry"),
    ("i", "sea"):  ("海豹突击队", "Navy SEAL", "allied", "infantry"),
    ("i", "sec"):  ("机密局特工", "Secret Service", "allied", "infantry"),
    ("i", "ein"):  ("爱因斯坦", "Einstein", "allied", "infantry"),
    ("i", "yur"):  ("超能力部队（心灵突击队）", "Psi-Corps / Psi Commando", "soviet", "infantry"),
    ("i", "clo"):  ("尤里复制人", "Yuri Clone", "yuri", "infantry"),
    ("i", "ini"):  ("尤里新兵", "Initiate", "yuri", "infantry"),
    ("i", "bru"):  ("狂兽人", "Brute", "yuri", "infantry"),
    ("i", "vir"):  ("病毒狙击手", "Virus", "yuri", "infantry"),
    ("i", "yup"):  ("尤里X", "Yuri Prime", "yuri", "infantry"),
    ("i", "ena"):  ("工程师（盟军）", "Engineer (Allied)", "allied", "infantry"),
    ("i", "ens"):  ("工程师（苏军）", "Engineer (Soviet)", "soviet", "infantry"),
    ("i", "eny"):  ("工程师（尤里）", "Engineer (Yuri)", "yuri", "infantry"),
    ("i", "tan"):  ("谭雅", "Tanya", "allied", "infantry"),
    ("i", "tap"):  ("谭雅", "Tanya", "allied", "infantry"),
    ("i", "las"):  ("登月火箭兵", "Cosmonaut", "soviet", "infantry"),
    ("i", "rom"):  ("罗曼诺夫总理", "Premier Romanov", "soviet", "infantry"),
    ("i", "sl1"):  ("奴隶矿工", "Slave Worker", "yuri", "infantry"),
    ("i", "sl2"):  ("奴隶矿工（获救）", "Slave Freed", "yuri", "infantry"),
    ("i", "arn"):  ("阿诺（好莱坞英雄）", "Arnie Frankenfurter", "other", "infantry"),
    ("i", "cli"):  ("弗林特（好莱坞英雄）", "Flint Westwood", "other", "infantry"),
    ("i", "sly"):  ("萨米（好莱坞英雄）", "Sammy Stallion", "other", "infantry"),
    ("i", "gen"):  ("步兵通用音效", "Generic Infantry", "other", "infantry"),
    ("i", "civ"):  ("平民（攻击音效）", "Civilian Attack", "other", "infantry"),
    ("i", "civ1"): ("平民（胖）", "Civilian (Fat)", "other", "infantry"),
    ("i", "civ2"): ("平民（瘦）", "Civilian (Thin)", "other", "infantry"),
    ("i", "cia"):  ("平民（盟军男）", "Civ. Allied Male", "other", "infantry"),
    ("i", "cis"):  ("平民（苏军男）", "Civ. Soviet Male", "other", "infantry"),
    ("i", "cfa"):  ("平民（盟军女）", "Civ. Allied Female", "other", "infantry"),
    ("i", "cfs"):  ("平民（苏军女）", "Civ. Soviet Female", "other", "infantry"),
    ("i", "cte"):  ("平民（德州人）", "Civ. Texan", "other", "infantry"),

    # ===================== 载具 / 空军 v =====================
    ("v", "gri"):  ("灰熊坦克", "Grizzly Tank", "allied", "vehicle"),
    ("v", "ifv"):  ("多功能步兵车", "IFV", "allied", "vehicle"),
    ("v", "mir"):  ("幻影坦克", "Mirage Tank", "allied", "vehicle"),
    ("v", "pri"):  ("光棱坦克", "Prism Tank", "allied", "vehicle"),
    ("v", "bat"):  ("战斗要塞", "Battle Fortress", "allied", "vehicle"),
    ("v", "rob"):  ("机器人坦克", "Robot Tank", "allied", "vehicle"),
    ("v", "tan"):  ("坦克杀手", "Tank Destroyer", "allied", "vehicle"),
    ("v", "tad"):  ("坦克杀手", "Tank Destroyer", "allied", "vehicle"),
    ("v", "chr"):  ("超时空矿车", "Chrono Miner", "allied", "vehicle"),
    ("v", "mca"):  ("基地车（盟军）", "Allied MCV", "allied", "vehicle"),
    ("v", "air"):  ("航空母舰", "Aircraft Carrier", "allied", "vehicle"),
    ("v", "des"):  ("驱逐舰", "Destroyer", "allied", "vehicle"),
    ("v", "aeg"):  ("神盾巡洋舰", "Aegis Cruiser", "allied", "vehicle"),
    ("v", "dol"):  ("海豚", "Dolphin", "allied", "vehicle"),
    ("v", "osp"):  ("鱼鹰运输机", "Osprey", "allied", "vehicle"),
    ("v", "int"):  ("鹞式战机", "Harrier", "allied", "vehicle"),
    ("v", "ble"):  ("黑鹰战机", "Black Eagle", "allied", "vehicle"),
    ("v", "blh"):  ("夜鹰直升机", "NightHawk", "allied", "vehicle"),
    ("v", "ho"):   ("两栖运输艇（盟军）", "Hover Transport (Allied)", "allied", "vehicle"),
    ("v", "rhi"):  ("犀牛坦克", "Rhino Tank", "soviet", "vehicle"),
    ("v", "apo"):  ("天启坦克", "Apocalypse Tank", "soviet", "vehicle"),
    ("v", "v3l"):  ("V3火箭发射车", "V3 Launcher", "soviet", "vehicle"),
    ("v", "fla"):  ("防空履带车", "Flak Track", "soviet", "vehicle"),
    ("v", "tes"):  ("磁能坦克", "Tesla Tank", "soviet", "vehicle"),
    ("v", "dem"):  ("自爆卡车", "Demolition Truck", "soviet", "vehicle"),
    ("v", "ter"):  ("恐怖机器人", "Terror Drone", "soviet", "vehicle"),
    ("v", "war"):  ("武装矿车", "War Miner", "soviet", "vehicle"),
    ("v", "mcs"):  ("基地车（苏军）", "Soviet MCV", "soviet", "vehicle"),
    ("v", "kir"):  ("基洛夫空艇", "Kirov Airship", "soviet", "vehicle"),
    ("v", "mig"):  ("米格战机", "MiG Fighter", "soviet", "vehicle"),
    ("v", "sub"):  ("台风潜艇", "Typhoon Submarine", "soviet", "vehicle"),
    ("v", "dre"):  ("无畏级战舰", "Dreadnought", "soviet", "vehicle"),
    ("v", "squ"):  ("巨型乌贼", "Giant Squid", "soviet", "vehicle"),
    ("v", "sco"):  ("海蝎", "Sea Scorpion", "soviet", "vehicle"),
    ("v", "cho"):  ("武装直升机", "Siege Chopper", "soviet", "vehicle"),
    ("v", "hos"):  ("两栖运输艇（苏军）", "Hover Transport (Soviet)", "soviet", "vehicle"),
    ("v", "las"):  ("鞭打者坦克", "Lasher Tank", "yuri", "vehicle"),
    ("v", "gat"):  ("盖特坦克", "Gattling Tank", "yuri", "vehicle"),
    ("v", "mag"):  ("磁电坦克", "Magnetron", "yuri", "vehicle"),
    ("v", "mas"):  ("精神控制车", "Mastermind", "yuri", "vehicle"),
    ("v", "cha"):  ("神经突击车", "Chaos Drone", "yuri", "vehicle"),
    ("v", "sla"):  ("奴隶矿场", "Slave Miner", "yuri", "vehicle"),
    ("v", "flo"):  ("镭射幽浮", "Floating Disc", "yuri", "vehicle"),
    ("v", "boo"):  ("雷鸣潜艇", "Boomer", "yuri", "vehicle"),
    ("v", "mcy"):  ("基地车（尤里）", "Yuri MCV", "yuri", "vehicle"),
    ("v", "hoy"):  ("两栖运输艇（尤里）", "Hover Transport (Yuri)", "yuri", "vehicle"),
    # 通用载具 / 海军语音组
    ("v", "gra"):  ("盟军载具（通用）", "Allied Vehicle (generic)", "allied", "vehicle"),
    ("v", "grs"):  ("苏军载具（通用）", "Soviet Vehicle (generic)", "soviet", "vehicle"),
    ("v", "waa"):  ("盟军海军（通用）", "Allied Naval (generic)", "allied", "vehicle"),
    ("v", "was"):  ("苏军海军（通用）", "Soviet Naval (generic)", "soviet", "vehicle"),
    # 音效 / 辅助 / 废案
    ("v", "mcvst"):("基地车（启动音效）", "MCV Move Start", "other", "vehicle"),
    ("v", "gen"):  ("载具损毁（通用）", "Vehicle Generic Die", "other", "vehicle"),
    ("v", "cabst"):("民用车（启动）", "Civilian Car Start", "other", "vehicle"),
    ("v", "coplo"):("警车（警笛循环）", "Police Siren Loop", "other", "vehicle"),
    ("v", "crush"):("Tank Crush", "Tank Crush", "other", "vehicle"),
    ("v", "lan"):  ("两栖运输艇（启动）", "Landing Craft Start", "other", "vehicle"),
    ("v", "nav"):  ("海军上浮（音效）", "Naval Unit Emerge", "other", "vehicle"),
    ("v", "orehar"):("采矿（音效）", "Ore Truck Harvest", "other", "vehicle"),
    ("v", "spy"):  ("侦察机", "Spy Plane", "soviet", "vehicle"),
    ("v", "tro"):  ("缆车", "Cable Car", "other", "vehicle"),
    ("v", "acc"):  ("游轮", "Cruise Ship", "other", "vehicle"),
    ("v", "arm"):  ("装甲运输（攻击音效）", "Armored Transport", "other", "vehicle"),
    ("v", "sea"):  ("海狼（未采用）", "Seawolf (cut)", "other", "vehicle"),

    # ===================== 建筑 / 通用 g =====================
    ("g", "radio"):("无线电通讯（战机）", "Radio Chatter", "other", "building"),
    ("g", "damag"):("建筑受损", "Building Damage", "other", "building"),
    ("g", "firlo"):("建筑火焰（循环）", "Building Fire Loop", "other", "building"),
    ("g", "flare"):("闪光弹", "Flare", "other", "building"),
    ("g", "exp"):  ("爆炸", "Explosion", "other", "building"),
    ("g", "bigben"):("大本钟", "Big Ben", "other", "building"),
    ("g", "blacru"):("围墙压碎", "Wall Crush", "other", "building"),
    ("g", "sancru"):("围墙压碎", "Wall Crush", "other", "building"),
    ("g", "cow"):  ("奶牛", "Cow", "other", "animal"),
    ("g", "chi"):  ("黑猩猩", "Chimpanzee", "other", "animal"),
    ("g", "bro"):  ("雷龙", "Brontosaurus", "other", "animal"),
    ("g", "rex"):  ("霸王龙", "T-Rex", "other", "animal"),
    ("g", "mum"):  ("木乃伊", "Mummy", "other", "animal"),
    ("g", "bea"):  ("北极熊", "Polar Bear", "other", "animal"),
    ("g", "ali"):  ("短吻鳄", "Alligator", "other", "animal"),
    ("g", "all"):  ("短吻鳄", "Alligator", "other", "animal"),
    ("g", "cam"):  ("骆驼", "Camel", "other", "animal"),
    ("g", "car"):  ("汽车", "Car", "other", "vehicle"),
    ("g", "cop"):  ("警车", "Police Car", "other", "vehicle"),
    ("g", "cra"):  ("补给箱", "Crate", "other", "building"),
    ("g", "defu"): ("拆除工具", "Defuse Kit", "other", "building"),
    ("g", "ente"): ("进入载具", "Enter Transport", "other", "building"),
    ("g", "exit"): ("离开载具", "Exit Transport", "other", "building"),
    ("g", "mon"):  ("纪念碑（崩塌）", "Monument Crumble", "other", "building"),
    ("g", "navsin"):("落水沉没", "Water Die", "other", "building"),
    ("g", "ore"):  ("钻矿（音效）", "Ore Mine Extract", "other", "building"),
    ("g", "pow"):  ("电力", "Power", "other", "building"),
    ("g", "psyam"):("心灵放大器（循环）", "Psychic Amplifier", "yuri", "building"),
    ("g", "ship"): ("游轮", "Cruise Ship", "other", "vehicle"),
    ("g", "times"):("超时空传送（特效）", "Chrono Screen Effect", "other", "building"),
    ("g", "tugbo"):("拖船", "Tugboat", "other", "vehicle"),
    ("g", "upgrad"):("升级", "Upgrade", "other", "building"),
    ("g", "virex"):("病毒受害者（爆裂）", "Virus Victim Explode", "yuri", "building"),
    ("g", "airrai"):("空袭警报", "Air Raid", "other", "building"),
    ("g", "foulo"):("喷泉（循环）", "Fountain Loop", "other", "building"),
    ("g", "mindcle"):("心灵控制解除", "Mind Cleared", "other", "building"),

    # ===================== 建筑 b (苏/尤/盟) =====================
    ("b", "ao"):   ("驻军建筑（攻击）", "Garrisoned Building Attack", "other", "building"),
    ("b", "fla"):  ("防空炮", "Flak Cannon", "soviet", "building"),
    ("b", "bioent"):("生化反应堆", "Bio Reactor", "yuri", "building"),
    ("b", "clov"): ("复制中心", "Cloning Vats", "soviet", "building"),
    ("b", "gen"):  ("建筑损毁（通用）", "Building Generic Die", "other", "building"),
    ("b", "gra"):  ("巨炮", "Grand Cannon", "allied", "building"),
    ("b", "grin"): ("部队回收厂", "Grinder", "yuri", "building"),
    ("b", "metdam"):("建筑受损（金属）", "Building Metal Damaged", "other", "building"),
    ("b", "oillo"):("油井", "Oil Pump", "other", "building"),
    ("b", "orer"): ("精炼厂（加工）", "Ore Refinery", "other", "building"),
    ("b", "par"):  ("巴黎铁塔", "Paris Tower", "other", "building"),
    ("b", "pat"):  ("爱国者导弹", "Patriot", "allied", "building"),
    ("b", "pil"):  ("机枪碉堡", "Pillbox", "allied", "building"),
    ("b", "pow"):  ("电厂", "Power Plant", "other", "building"),
    ("b", "pri"):  ("光棱塔", "Prism Tower", "allied", "building"),
    ("b", "psy"):  ("心灵放大器", "Psychic Amplifier", "other", "building"),
    ("b", "psydet"):("心灵探测器", "Psychic Detector", "yuri", "building"),
    ("b", "sen"):  ("哨戒炮", "Sentry Gun", "soviet", "building"),
    ("b", "spy"):  ("间谍卫星", "Spy Satellite", "allied", "building"),
    ("b", "tan"):  ("坦克碉堡", "Tank Bunker", "soviet", "building"),
    ("b", "tes"):  ("磁暴线圈", "Tesla Coil", "soviet", "building"),
    ("b", "yub"):  ("尤里雕像", "Yuri Bust", "yuri", "building"),

    # ===================== 环境 / 动物 a =====================
    ("a", "gul"):  ("海鸥", "Gull", "other", "animal"),
    ("a", "birj"): ("鸟鸣（丛林）", "Bird (jungle)", "other", "animal"),
    ("a", "birm"): ("鸟鸣（清晨）", "Bird (morning)", "other", "animal"),
    ("a", "birp"): ("鸟鸣（公园）", "Bird (park)", "other", "animal"),
    ("a", "birt"): ("鸟鸣（温带）", "Bird (temperate)", "other", "animal"),
    ("a", "owl"):  ("猫头鹰", "Owl", "other", "animal"),
    ("a", "urb"):  ("城市", "Urban", "other", "ambient"),
    ("a", "cri"):  ("蟋蟀", "Cricket", "other", "animal"),
    ("a", "tra"):  ("街道交通", "Traffic", "other", "ambient"),
    ("a", "jur"):  ("丛林", "Jungle", "other", "ambient"),
    ("a", "wav"):  ("海浪", "Wave", "other", "ambient"),
    ("a", "win"):  ("风", "Wind", "other", "ambient"),
    ("a", "riv"):  ("河流", "River", "other", "ambient"),
    ("a", "des"):  ("沙漠", "Desert", "other", "ambient"),
    ("a", "wat"):  ("瀑布", "Waterfall", "other", "ambient"),
    ("a", "prot"): ("宣传车（未采用）", "Propaganda Truck (cut)", "other", "vehicle"),

    # ===================== 界面 / 系统 u =====================
    ("u", "acb"):  ("建造栏（开合）", "Sidebar Tab", "other", "ui"),
    ("u", "base"): ("基地遇袭（警报）", "Base Under Attack", "other", "ui"),
    ("u", "beac"): ("信标", "Beacon", "other", "ui"),
    ("u", "bonu"): ("奖励（金钱箱）", "Bonus", "other", "ui"),
    ("u", "camer"):("镜头切换", "Camera Switch", "other", "ui"),
    ("u", "chee"): ("欢呼", "Cheer", "other", "ui"),
    ("u", "comma"):("指令栏", "Command Bar", "other", "ui"),
    ("u", "cred"): ("金额（增减）", "Credits", "other", "ui"),
    ("u", "gamcl"):("游戏关闭", "Game Close", "other", "ui"),
    ("u", "garri"):("驻军", "Garrison", "other", "ui"),
    ("u", "mensc"):("菜单警告", "Menu Scold", "other", "ui"),
    ("u", "menu"): ("菜单点击", "Menu Click", "other", "ui"),
    ("u", "mes"):  ("消息（文字）", "Message", "other", "ui"),
    ("u", "movlo"):("过场电影（开/关）", "Movie On/Off", "other", "ui"),
    ("u", "ne"):   ("新游戏", "New Game", "other", "ui"),
    ("u", "plac"): ("放置建筑", "Place Building", "other", "ui"),
    ("u", "plan"): ("计划模式", "Planning Mode", "other", "ui"),
    ("u", "qe"):   ("建造队列", "Build Queue", "other", "ui"),
    ("u", "radar"):("雷达（开/关）", "Radar", "other", "ui"),
    ("u", "repai"):("维修完成", "Repair", "other", "ui"),
    ("u", "scolo"):("得分徽章（循环）", "Score Emblem", "other", "ui"),
    ("u", "selbu"):("出售建筑", "Sell Building", "other", "ui"),
    ("u", "slid"): ("菜单滑动", "Menu Slide", "other", "ui"),
    ("u", "ta"):   ("菜单标签", "Menu Tab", "other", "ui"),
    ("u", "tex"):  ("文本提示音", "Text Bleep", "other", "ui"),
    ("u", "warni"):("警告", "Warning", "other", "ui"),

    # ===================== 超级武器 / 支援 s =====================
    ("s", "nuk"):  ("核弹", "Nuclear Missile", "other", "support"),
    ("s", "gen"):  ("基因突变器", "Genetic Mutator", "yuri", "support"),
    ("s", "psy"):  ("心灵控制器", "Psychic Dominator", "yuri", "support"),
    ("s", "for"):  ("力场护盾", "Force Shield", "other", "support"),
    ("s", "chr"):  ("超时空传送仪", "Chronosphere", "allied", "support"),
    ("s", "iro"):  ("铁幕", "Iron Curtain", "soviet", "support"),
    ("s", "par"):  ("伞兵", "Paratroopers", "other", "support"),
    ("s", "wea"):  ("天气控制机", "Weather Control", "other", "support"),

    # ===================== 资料片 / 其他 =====================
    ("x", "s3c"): ("伦敦平民（战役）", "London Civilians", "other", "ui"),
    ("c", "eva"): ("战役剧情语音", "Cinematic EVA", "other", "ui"),
}

# soundmd.ini 中的 Test1..Test10 音效
for i in range(1, 11):
    U[("t", f"s{i}")] = ("测试音效", f"Test Sound {i}", "other", "ui")

# 由 U 推导：前缀 -> 该前缀下所有已知兵种代码（长度降序，用于最长前缀匹配）
_CODES_BY_PRE = {}
for (pre, code), _ in U.items():
    _CODES_BY_PRE.setdefault(pre, []).append(code)
for pre in _CODES_BY_PRE:
    _CODES_BY_PRE[pre].sort(key=len, reverse=True)


def classify(name: str):
    """
    依据 Westwood 命名规则解析音效文件名。
    返回 dict: pre, code, vtype, vtype_zh, unit_zh, unit_en, side, proto, known, label
    """
    raw = name
    name = name.lower()
    if name.endswith(".wav"):
        name = name[:-4]
    if not name:
        return _miss(raw, "", "", "音效")
    pre = name[0]
    body = name[1:]

    def _strip_token(s):
        """若 s 以已知类型 token 结尾，返回 (code_candidate, token)，否则 (None, None)。"""
        for tok in _TYPE_TOKENS:
            if s.endswith(tok) and len(s) > len(tok):
                return s[:len(s) - len(tok)], tok
        return None, None

    def _resolve(cand):
        """cand 本身或 cand 的最长前缀若存在于 U，返回该 code。"""
        for L in range(len(cand), 1, -1):
            key = (pre, cand[:L])
            if key in U:
                return cand[:L]
        return None

    code = vtype = None

    # 1) 先剥掉一个序号字母 a~g 再匹配类型 token（避免 tele/see/die 等被拆坏）
    if len(body) > 2 and body[-1] in "abcdefg":
        b2 = body[:-1]
        cand, tok = _strip_token(b2)
        if cand:
            hit = _resolve(cand)
            if hit:
                code, vtype = hit, tok

    # 2) 不剥序号直接匹配类型 token（tele/see/die 等正好以 a~g 结尾的真实 token）
    if code is None:
        cand, tok = _strip_token(body)
        if cand:
            hit = _resolve(cand)
            if hit:
                code, vtype = hit, tok

    # 3) 回退：在 U 已知代码里找最长前缀匹配
    if code is None:
        for cand in _CODES_BY_PRE.get(pre, []):
            if body.startswith(cand) and len(cand) >= 2:
                code = cand
                vtype = "?"
                break
        if code is not None:
            rem = body[len(code):]
            # 若 rem 尾是序号字母，先剥一次再试 token
            if rem and rem[-1] in "abcdefg":
                rem2 = rem[:-1]
                _, tok = _strip_token(rem2)
            else:
                tok = None
            if tok is None:
                _, tok = _strip_token(rem)
            if tok:
                vtype = tok

    if code is None:
        code = body

    info = U.get((pre, code))
    known = info is not None
    if not known:
        # 二次回退：用 code 的最长前缀解析（例如 craar -> cra）
        for L in range(len(code), 1, -1):
            info = U.get((pre, code[:L]))
            if info:
                code = code[:L]
                known = True
                break

    if info:
        unit_zh, unit_en, side, proto = info
    else:
        unit_zh = unit_en = code
        side = PREFIX.get(pre, ("other", "其他"))[0]
        proto = PREFIX.get(pre, ("other", "其他"))[1]

    vtype_zh = VOICE_TYPE.get(vtype, "语音" if vtype in ("?", None) else "音效")

    return {
        "pre": pre,
        "code": code,
        "vtype": vtype or "",
        "vtype_zh": vtype_zh,
        "unit_zh": unit_zh,
        "unit_en": unit_en,
        "side": side,
        "proto": proto,
        "known": known,
        "label": (f"{unit_zh} · {vtype_zh}" if known else f"{code} · {vtype_zh}"),
    }


def _miss(raw, pre, code, vt):
    return {
        "pre": pre, "code": code, "vtype": "", "vtype_zh": "音效",
        "unit_zh": raw, "unit_en": raw, "side": "other", "proto": "other",
        "known": False, "label": raw,
    }


if __name__ == "__main__":
    tests = [
        "igisea", "iconsea", "iflaata", "itesatb", "vrhiatb", "vgriatta",
        "vapoat1a", "vpriata", "vwaaata", "vgrsata", "vflaat1a", "icraata",
        "iyupatd", "ibruata", "vbooa1a", "vmigata", "abirj01a", "uradaron",
        "vchrtele", "vsladepa", "iggiat2a", "vaircraa", "vtesatta",
        "vfloata", "vchoa1a", "iteschaa", "gcrafire",
    ]
    for t in tests:
        r = classify(t)
        print(f"{t:12} -> pre={r['pre']} code={r['code']:6} type={r['vtype']:4} "
              f"{r['unit_zh']} · {r['vtype_zh']}  known={r['known']}")
