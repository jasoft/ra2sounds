# RA2/YR 音效文件与兵种映射说明

本文档记录 `sounds/` 目录下 2293 个《红色警戒2 / 尤里的复仇》原版音效文件是如何对应到具体兵种 / 建筑 / 系统的。

---

## 1. 权威数据来源

本项目的映射不再依赖社区二手表格，而是直接使用游戏原始 INI：

- `soundmd.ini`：定义游戏中所有“语音事件”，例如 `[ChronoMinerSelect]`、`[AircraftCarrierMove]`，并列明每个事件引用的真实音效文件。
- `rulesmd.ini`：定义每个单位（`[CMIN]`、`[CARRIER]`、`[GGI]`…）使用哪些语音事件。

来源仓库：`CnCNet/cncnet-yr-client-package` 的 `develop` 分支中的 `game-assets/cncnet.pack/`。
通过交叉引用这两个文件，即可得到“文件名 → 兵种”的权威对应关系。

> 注：OpenRA ra2 mod 的 `audio/voices.yaml` 仅用于核对步兵语音组；由于 OpenRA 把大量载具语音通用化，载具部分以原版 INI 为准。

---

## 2. 文件名解析规则（Westwood 官方约定）

音效文件名基本结构：

```text
[前缀1字母][兵种代码2~4字母][语音类型2~3字母][序号 a~g].wav
```

前缀含义：

| 前缀 | 含义 | 例子 |
|------|------|------|
| `i` | 步兵 | `igisea` = GI 选中 |
| `v` | 载具 / 空军 / 海军 | `vchrsea` = 超时空矿车选中 |
| `b` | 建筑（苏/尤/盟防御建筑） | `bflaatta` = 防空炮攻击 |
| `g` | 通用 / 环境 / 动物 / 箱子 | `gcowdiea` = 奶牛死亡 |
| `a` | 环境音 / 动物 | `abirj01a` = 丛林鸟鸣 |
| `u` | 界面 / 系统 | `uradaron` = 雷达开启 |
| `s` | 超级武器 / 支援技能 | `schrtele` = 超时空传送仪传送 |
| `x/t/c` | 资料片 / 测试 / 剧情语音 | `xs3c101` = 伦敦战役平民 |

常见语音类型后缀：

| 后缀 | 含义 | 例子 |
|------|------|------|
| `sea/seb/sec/…` | 选中 | `igisea` |
| `moa/mob/moc/…` | 移动 | `iconmoa` |
| `ata/atb/att/…` | 攻击 | `vrhiatta` |
| `dia/die/…` | 死亡 | `igiddia` |
| `fea/fed/…` | 受惊 | `ibrufea` |
| `tele` | 传送 | `vchrtele` |
| `dep` | 部署 | `vsladepa` |
| `go` | 收矿返回 | `vchrgoa` |
| `ha` | 收割 | `vwarhaa` |
| `cha` | 充电 | `iteschaa` |
| `cra` | 坠毁 | `vaircraa` |
| `lo` | 循环音 | `vgatlo1a` |
| `on/off` | 开启 / 关闭 | `gpowon` / `bspyof` |

同一个“兵种代码”在不同前缀下代表不同单位，所以映射表以 `(前缀, 代码)` 作为唯一键。

---

## 3. 解析器实现要点

`ra2_sound_map.py` 中的 `classify()` 函数按以下顺序解析：

1. **剥除序号字母后匹配类型 token**：先把末尾 `a~g` 的序号去掉，再匹配 `sea`/`moa`/`ata` 等后缀。这样避免 `tele`/`see`/`die` 这类本身以 `e` 结尾的 token 被序号剥离破坏。
2. **不剥序号直接匹配类型 token**：处理 `tele`/`see`/`die` 等真实以 `a~g` 结尾的 token。
3. **前缀最长匹配回退**：如果前两步失败，在前缀已知代码中找最长前缀匹配，再从剩余部分推导类型。
4. **前缀解析**：例如 `gcraarmo` 会被解析为 `g` + `cra`（补给箱）+ `armo`，因为 `craar` 的最长前缀命中 `cra`。

---

## 4. 核心修正清单

以下是以原版 INI 核对后发现的主要错误（已修复）：

| 文件前缀 | 旧标签 | 正确标签 | 说明 |
|----------|--------|----------|------|
| `vchr*` | 超时空传送仪 | 超时空矿车 | `[ChronoMiner*]` 事件 |
| `vsla*` | 超时空矿车 | 奴隶矿场 | `[SlaveMiner*]` 事件 |
| `vair*` | 空指部 | 航空母舰 | `[AircraftCarrier*]` 事件 |
| `iggi*` | 美国大兵 | 重装大兵 | `[GuardianGI*]` 事件 |
| `vwar*` | 战车工厂 | 武装矿车 | `[WarMiner*]` 事件 |
| `vtes*` | 磁暴线圈 | 磁能坦克 | `[TeslaTank*]` 事件 |
| `vfla*` | 防空炮 | 防空履带车 | `[FlakTrack*]` 事件 |
| `vgat*` | 裂缝产生器 | 盖特坦克 | `[GattlingTank*]` 事件 |
| `vmas*` | 武装矿车 | 精神控制车 | `[MasterMind*]` 事件 |
| `vmag*` | 磁能坦克 | 磁电坦克 | `[Magnetron*]` 事件 |
| `vlas*` | 镭射幽浮 | 鞭打者坦克 | `[LasherTank*]` 事件 |
| `vcho*` | — | 武装直升机 | `[SeigeChopper*]` 事件 |
| `vboo*` | — | 雷鸣潜艇 | `[Boomer*]` 事件 |
| `vflo*` | — | 镭射幽浮 | `[FloatingDisc*]` 事件 |
| `vcha*` | — | 神经突击车 | `[ChaosDrone*]` 事件 |
| `vsco*` | 侦察车 | 海蝎 | `[SeaScorpion*]` 事件 |
| `vapo*` | 天启坦克（盟军） | 天启坦克（苏军） | 阵营修正 |
| `vmca*` | 磁能坦克 | 盟军基地车 | `[MCVAllied*]` |
| `vmcs*` | 磁能坦克 | 苏军基地车 | `[MCVSoviet*]` |
| `vmcy*` | 磁能坦克 | 尤里基地车 | `[MCVYuri*]` |
| `itan*` | — | 谭雅 | `[Tanya*]` 旧语音事件 |
| `iclo*` | — | 尤里复制人 | `[YuriClone*]` |
| `iyur*` | 尤里复制人 | 超能力部队/心灵突击队 | `[Yuri*]` 事件对应 `PTROOP` |
| `ilas*` | — | 登月火箭兵 | `[LaserCosmo*]` |
| `bfla*` | 闪电风暴 | 防空炮 | `[FlakCannonAttack]` |
| `bpil*` | 核弹发射井 | 机枪碉堡 | `[PillboxAttack]` |
| `bgra*` | — | 巨炮 | `[GrandCannon*]` |
| `bpar*` | 伞兵 | 巴黎铁塔 | `[ParisTowerAttack]` |
| `byub*` | 尤里基地车 | 尤里雕像 | `[YuriBust*]` |
| `bclov*` | 平民屋 | 复制中心 | `[CloningVatsCreate]` |
| `bgen*` | 基因突变器 | 建筑损毁（通用） | `[BuildingGenericDie]` |
| `g+radio*` | 无线电 | 无线电通讯（战机） | `[Intruder*]` 事件混用 |
| `g+cra*` | 起重机 | 补给箱 | `[Crate*]` 事件 |
| `g+bro*` | 铜管乐 | 雷龙 | `[Bronto*]` 事件 |
| `g+cam*` | 相机 | 骆驼 | `[Camel*]` 事件 |
| `g+times*` | 计时震撼 | 超时空传送（特效） | `[ChronoScreenSound]` |
| `u+selbu*` | 选择建造 | 出售建筑 | `[SellBuilding]` |
| `u+movlo*` | 移动循环 | 过场电影（开/关） | `[MovieOn]` / `[MovieOff]` |
| `a+tra*` | 树 | 街道交通 | `[_Amb_Traffic]` |

---

## 5. 新增兵种 / 系统（之前未识别）

| 前缀+代码 | 标签 | 说明 |
|-----------|------|------|
| `iarn*` / `icli*` / `isly*` | 好莱坞三英雄 | 阿诺 / 弗林特 / 萨米 |
| `irom*` | 罗曼诺夫总理 | 战役角色 |
| `isl1*` / `isl2*` | 奴隶矿工 / 奴隶矿工（获救） | `[SlaveWorker*]` / `[SlaveFreed*]` |
| `ieny*` | 工程师（尤里） | `[EngYuri*]` |
| `vho*` / `vhos*` / `vhoy*` | 两栖运输艇（盟/苏/尤） | `[HoverAllied/Soviet/Yuri*]` |
| `vtan*` / `vtad*` | 坦克杀手 | `[TankDestroyer*]` |
| `vsea*` | 海狼（未采用） | 注释掉的 `[Seawolf]` |
| `a+prot*` | 宣传车（未采用） | 注释掉的 `[PropagandaTruck]` |
| `t+s1..s10` | 测试音效 | `[Test1..Test10]` |
| `x+s3c*` | 伦敦平民（战役） | `[LCiv*Select]` |

---

## 6. 仍需人工确认的标签

部分分组属于通用音效、废案单位或命名有取舍，已单独放到 `review.html`。打开该页面可以试听并核对，不对的请直接修改 `ra2_sound_map.py` 中的 `U` 表后重新运行：

```bash
python3 build_sounds_json.py
```

`review.html` 中的典型待确认项：

- `a+prot*` 宣传车（废案）
- `v+sea*` 海狼（废案）
- `v+acc*` 游轮、`v+tro*` 缆车
- `v+nav*` 海军上浮音效、`v+orehar*` 采矿音效
- `v+crush*` Tank Crush（已按你要求保留英文）
- `g+times*` / `g+navsin*` / `g+virex*` 等通用特效
- `u+acb*` 建造栏开合、`u+movlo*` 过场电影
- `i+yur*` 超能力部队 vs 心灵突击队 的命名取舍

---

## 7. 如何更新映射

如果以后发现某组标签不对：

1. 编辑 `ra2_sound_map.py` 中的 `U` 字典。
2. （可选）在 `VOICE_TYPE` 里补充新的类型后缀。
3. 运行：

```bash
python3 build_sounds_json.py
```

该脚本会重新扫描 `sounds/` 并生成新的 `sounds.json`。

---

## 8. 文件名 → 单位自查速查

若想快速查某个文件名对应的单位，可直接运行：

```bash
python3 -c "import ra2_sound_map as S; print(S.classify('vchrsea'))"
```

输出示例：

```text
{'pre': 'v', 'code': 'chr', 'vtype': 'sea', 'vtype_zh': '选中',
 'unit_zh': '超时空矿车', 'unit_en': 'Chrono Miner', 'side': 'allied',
 'proto': 'vehicle', 'known': True, 'label': '超时空矿车 · 选中'}
```
