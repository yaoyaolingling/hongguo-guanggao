# 用 AI Agent 自动配置

把部署过程交给能执行 shell 的 Agent（Codex / Claude Code / Cursor / 自建脚本），
由它通过 adb 完成「导入配置 → 安装 GKD → 授权无障碍 → 添加订阅 → 验证」。

---

## 1. 前置条件

| 项 | 要求 |
|---|---|
| 手机 | Android 8+，已开启「开发者选项」 |
| USB | 数据线连接，手机弹「允许 USB 调试」→ 允许（建议勾选始终允许） |
| 调试开关 | USB 调试；ColorOS/realme 另需「USB 安装」「USB 调试（安全设置）」 |
| 电脑 | 已安装 adb，且 `adb devices` 能看到设备 |
| 屏幕 | 配置过程中保持解锁亮屏，避免系统锁屏打断点击 |

自检：

```bash
adb devices
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
```

Windows + Git Bash 需要先固定变量（否则 `/sdcard/...` 会被改写成 `E:/sdcard/...`）：

```bash
export MSYS_NO_PATHCONV=1
ADB="$LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe"
```

---

## 2. 直接粘贴给 Agent 的提示词

> 前提：Agent 具备 shell 执行能力，且能访问本仓库。

```text
你是 Android 自动化助手。我的手机已通过 USB 连接电脑，adb 可用。
目标：按 https://github.com/yaoyaolingling/hongguo-guanggao 把「红果短剧去广告」
配置到我的手机上。

请自行完成：
1. 读取仓库 README、docs/02-clash-setup.md、docs/03-gkd-setup.md、docs/04-verify.md；
2. 检查 adb 设备、系统版本、屏幕分辨率；
3. 导入并激活 clash/adblock-direct.yaml；
4. 安装 GKD，开启无障碍；
5. 添加并启用 gkd/hongguo-sub.json 与 gkd/gkd-global-splash.json；
6. 按 docs/04-verify.md 验证，并汇报真实输出。

硬性要求：
- 每次点击前先 uiautomator dump 当前界面，按 text/content-desc 定位坐标；
  禁止凭记忆写死坐标（不同机型/分辨率不同）。
- 不删除、不覆盖我已有的 Clash 配置与 GKD 订阅。
- 不执行 am force-stop li.songe.gkd，不清理 GKD 应用数据。
- 不读取、不上传任何含节点/订阅凭据的文件（如 *clash-export*、配置文件.txt）。
- 系统弹窗（安装未知应用、无障碍授权）可以点「允许」。
- 输出必须包含真实命令输出；未执行的步骤写「未执行」，禁止编造结果。
- 失败时给出当前界面的关键节点、失败原因和下一步建议，不要静默跳过。
```

一句话版：

```text
手机已连 adb，请按 yaoyaolingling/hongguo-guanggao 仓库的 docs/06-agent-setup.md
帮我配置红果去广告：先 dump 界面再点击，不覆盖现有配置，最后跑 verify.sh 汇报。
```

---

## 3. Agent 会执行的流程

### 3.1 环境探测

```bash
adb devices
adb shell wm size
adb shell getprop ro.build.version.sdk
adb shell pm list packages | grep -E "metacubex|songe"
```

### 3.2 部署 Clash

```bash
# 1. 取配置（或从本仓库 clone 后取 clash/adblock-direct.yaml）
curl -L -o adblock-direct.yaml \
  https://raw.githubusercontent.com/yaoyaolingling/hongguo-guanggao/main/clash/adblock-direct.yaml

# 2. 推到手机下载目录
adb push adblock-direct.yaml /sdcard/Download/adblock-direct.yaml

# 3. 打开 CMFA
adb shell monkey -p com.github.metacubex.clash.meta \
  -c android.intent.category.LAUNCHER 1
```

随后全部走 UI 自动化：

```text
首页「配置」→ 右上 + →「从文件导入」→ 选择 adblock-direct.yaml
→ 保存 → 点配置左侧圆点激活 → 返回首页 →「点此启动」
```

验证：

```bash
adb shell dumpsys connectivity | grep -c "VPN:com.github.metacubex.clash.meta"
# 期望输出 1
```

### 3.3 部署 GKD

```bash
adb push gkd.apk /sdcard/Download/gkd.apk
adb shell monkey -p com.coloros.filemanager -c android.intent.category.LAUNCHER 1
```

在文件管理器里点 APK 安装（ColorOS 会弹「允许文件管理安装应用」）。
装完打开 GKD：

```bash
adb shell monkey -p li.songe.gkd -c android.intent.category.LAUNCHER 1
```

无障碍路径：

```text
GKD 首页「无障碍未授权」→「开启无障碍」→「前往」
→ 系统设置 → 无障碍 → 已下载的应用 → GKD → 开启 → 允许
```

也可以直接跳转：

```bash
adb shell am start -a android.settings.ACCESSIBILITY_SETTINGS
```

### 3.4 添加订阅

```text
GKD → 底部「订阅」→ 右下 +
→ 粘贴 https://raw.githubusercontent.com/yaoyaolingling/hongguo-guanggao/main/gkd/hongguo-sub.json
→ 确定
→ 再添加 gkd/gkd-global-splash.json
```

进入订阅，确认「开屏广告」「开屏广告-全局」开关为蓝色。

### 3.5 验证

```bash
bash tools/verify.sh
```

---

## 4. UI 自动化配方

Agent 最容易踩的坑是「写死坐标」。正确做法是每次读取界面：

```bash
export MSYS_NO_PATHCONV=1
ADB="${ADB:-adb}"

"$ADB" shell uiautomator dump /sdcard/ui.xml >/dev/null
"$ADB" pull /sdcard/ui.xml ./ui.xml >/dev/null

python - <<'PY'
import re
s = open("ui.xml", encoding="utf-8").read()
for m in re.finditer(r"<node[^>]*>", s):
    t = m.group(0)
    txt = re.search(r'text="([^"]*)"', t)
    desc = re.search(r'content-desc="([^"]*)"', t)
    b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', t)
    if not ((txt and txt.group(1)) or (desc and desc.group(1))):
        continue
    x = (int(b.group(1)) + int(b.group(3))) // 2 if b else 0
    y = (int(b.group(2)) + int(b.group(4))) // 2 if b else 0
    print(repr(txt.group(1) if txt else ""),
          repr(desc.group(1) if desc else ""),
          f"-> tap {x} {y}")
PY
```

其他常用动作：

```bash
adb shell input tap X Y          # 点击
adb shell input swipe X1 Y1 X2 Y2 300   # 滑动
adb shell input text "http://127.0.0.1:8000/x.json"  # 输入（空格用 %s）
adb shell input keyevent 4       # 返回
```

截图（避免一次回传大图）：

```bash
adb exec-out screencap -p > shot.png
python -c "from PIL import Image;im=Image.open('shot.png');w,h=im.size;s=900/max(w,h);im.resize((int(w*s),int(h*s))).convert('RGB').save('shot.jpg',quality=80)"
```

---

## 5. 真机踩坑清单

| 坑 | 表现 | 处理 |
|---|---|---|
| Git Bash 路径改写 | `adb push` 报找不到 `/sdcard/...` | `export MSYS_NO_PATHCONV=1` |
| CMFA 保存无反应 | 点保存后仍停在表单 | 换配置名；确认不是空 `proxies` |
| 文件选择器只显示「近期」 | 找不到 Download 里的文件 | 改用「从 URL 导入」+ `adb reverse 8000` |
| 输入框没聚焦 | `input text` 没反应 | 先点输入框，再 `input text` |
| 键盘遮住按钮 | 点不到「确认」 | 先 `keyevent 4` 收键盘 |
| ColorOS 安装弹窗 | 「允许文件管理安装应用吗」 | 点「允许」，再点「继续安装」 |
| GKD 状态文案误报 | 首页「无障碍发生故障」 | 以 `dumpsys accessibility` 的 `Bound services` 为准 |
| GKD 被强行停止 | 规则全部失效 | 不要 `force-stop li.songe.gkd`；重开无障碍 |
| 坐标写死 | 换机型全乱 | 每次 dump 后按文本定位 |

---

## 6. 验收清单

- [ ] `adb devices` 显示设备为 `device`
- [ ] `dumpsys connectivity` 里 VPN 计数为 1
- [ ] CMFA 首页显示 `运行中 / 规则模式 / adblock-direct 已激活`
- [ ] `dumpsys accessibility` 的 `Bound services` 含 `label=GKD`
- [ ] GKD 订阅页有 2 条新订阅，且组开关为蓝色
- [ ] 冷启动红果 1 秒内进入内容页，无开屏倒计时
- [ ] 打开任意有「跳过」按钮的 App，按钮被自动点击

---

## 7. 回滚

```text
Clash：配置列表点回原机场配置 → 启动
GKD：订阅页长按/进入订阅 → 删除；或系统设置里关闭 GKD 无障碍
彻底卸载：adb uninstall li.songe.gkd
```

回滚不会影响手机上的照片、聊天记录等个人数据。
