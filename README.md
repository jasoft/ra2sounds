# 红警2 / 尤里的复仇 音效库浏览器

一个离线、零版权风险的《命令与征服：红色警戒2 / 尤里的复仇》音效浏览与检索工具。

---

## 特性

- 按 **阵营 / 兵种 / 语音类型** 三级浏览全部原版音效
- 用 Westwood 官方命名规则自动识别 2000+ 条音效
- 映射数据来自 **原版游戏 INI（soundmd.ini + rulesmd.ini）**，而非二手对照表
- 每条音效可加 **备注**，持久化在本地 SQLite 数据库中
- **仅局域网 / 本机客户端可编辑备注**；公网访问自动降级为只读

---

## 数据来源与版权说明

本项目**不包含任何游戏原始音频文件**。

音效文件（`sounds/*.wav`）属于《红色警戒2 / 尤里的复仇》的版权内容，需要你自己从正版游戏中提取。映射表本身（`ra2_sound_map.py`、`sounds.json`）是公开的游戏数据整理，可以自由分享。

---

## 准备音效文件

### 使用 XCC Mixer 提取

1. 下载并运行 **XCC Mixer**（由 Olaf van der Spek 开发的 C&C 资源工具）。
2. 打开游戏目录中的 `.mix` 文件，例如：
   - `ra2.mix`
   - `ra2md.mix`
   - `language.mix` / `langmd.mix`
3. 在 XCC Mixer 中找到 `.aud` 音频条目，右键选择 **"Copy as WAV"** 或批量导出为 `.wav`。
4. 将导出的 `.wav` 文件放入本项目的 `sounds/` 目录。

> 文件名应保持原始音效代码，例如 `igisea.wav`、`vchrtele.wav` 等。浏览器依靠这些原始名称识别兵种。

---

## 构建编目

放置好音效文件后，运行：

```bash
python3 build_sounds_json.py
```

脚本会：

- 扫描 `sounds/` 下所有 `.wav`
- 调用 `ra2_sound_map.classify()` 自动识别兵种与语音类型
- 生成浏览器使用的 `sounds.json`

---

## 使用浏览器

本项目的备注功能需要一个轻量后端（`server.py`，仅用 Python 标准库，零第三方依赖）。
请先启动后端，再用浏览器访问：

```bash
python3 server.py            # 默认监听 0.0.0.0:8000
# 然后在浏览器打开：
open http://127.0.0.1:8000/
```

> 后端会同时托管静态资源（`index.html`、`sounds.json`、`sounds/*.wav`）并处理备注读写。
> 不启动后端、直接双击 `index.html` 也能浏览音效，但备注框会处于只读状态。

常用参数：

```bash
python3 server.py --port 8000 --db notes.db        # 指定端口与数据库文件
python3 server.py --host 127.0.0.1                 # 仅本机可访问
python3 server.py --trust-proxy                    # 经反向代理部署时，按 X-Forwarded-For 判定来源 IP
```

界面支持：

- 按苏军 / 盟军 / 尤里 / 系统 切换阵营
- 按兵种名称搜索
- 点击任意音效条目试听
- 选中音效后，在下方 **「📝 音效备注」** 框中书写备注并保存（仅局域网 / 本机可保存）
- 顶部 **“标签核对页”** 链接可查看仍需人工确认的待定分组

### 备注的编辑权限

备注接口按**客户端来源 IP** 判定：

| 来源 | 能否编辑 |
| --- | --- |
| 本机 `127.0.0.1` / `::1` | ✅ 可编辑 |
| 局域网（私有网段：`10.*`、`172.16~31.*`、`192.168.*`、`169.254.*`、IPv6 ULA 等） | ✅ 可编辑 |
| 公网 / 其他 | ⚠️ 只读（保存返回 403，备注框置灰） |

备注保存在 `notes.db`（SQLite，已在 `.gitignore` 中忽略）。
同一局域网下的手机或其他电脑，用本机内网 IP（如 `http://192.168.1.x:8000/`）访问即可共同编辑。

---

## 项目结构

```text
.
├── index.html              # 浏览器界面（含音效备注编辑框）
├── badges.js               # 阵营/兵种徽章生成
├── server.py               # 轻量后端：静态托管 + 备注 API（零依赖，标准库）
├── sounds.json             # 音效编目（自动生成）
├── build_sounds_json.py    # 扫描并生成 sounds.json
├── ra2_sound_map.py        # 文件名 → 兵种 映射表 + 解析器
├── openra_voices.yaml      # OpenRA ra2 mod 的步兵语音定义（参考）
├── SOUND_MAPPING.md        # 映射规则与修正说明
├── review.html             # 待确认标签试听页
├── notes.db                # 音效备注数据库（运行时生成，已 gitignore）
└── sounds/                 # 自行提取的 .wav 文件（默认被 .gitignore 忽略）
```

---

## 修正映射

如果发现某个音效标签错误：

1. 编辑 `ra2_sound_map.py` 中的 `U` 字典。
2. 重新运行 `python3 build_sounds_json.py`。
3. 刷新浏览器。

详细的修正历史和规则说明见 [SOUND_MAPPING.md](./SOUND_MAPPING.md)。

---

## 致谢

- 映射数据基于 Westwood Studios 原版 `soundmd.ini` / `rulesmd.ini`。
- 步兵语音组与 OpenRA ra2 mod 的 `audio/voices.yaml` 交叉核对。
- CnCNet 社区维护的 YR 客户端包提供了可直接获取的原版 INI 文件。
