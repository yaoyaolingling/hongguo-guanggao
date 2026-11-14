# 验证与排错

## 1. 一键体检

```bash
bash tools/verify.sh
```

等价命令：

```bash
# 设备在线
adb devices

# Clash VPN 是否建立（1 = 是）
adb shell dumpsys connectivity | grep -c "VPN:com.github.metacubex.clash.meta"

# 无障碍绑定情况
adb shell dumpsys accessibility | grep -E "Bound services|Enabled services|Crashed services"

# GKD 进程
adb shell ps -A | grep li.songe.gkd
```

期望输出：

```text
Bound services:{Service[label=GKD, ...]}
Enabled services:{{li.songe.gkd/...SelectToSpeakService}}
Crashed services:{}
```

---

## 2. 功能验证

```bash
adb shell am force-stop com.phoenix.read
adb shell monkey -p com.phoenix.read -c android.intent.category.LAUNCHER 1
# 1 秒后截图，应直接是内容页，没有倒计时/跳过按钮
adb exec-out screencap -p > shot.png
```

其他 App 同理。若某 App 仍出现开屏，先看它是否有「跳过」按钮：

- 有按钮但没点 → GKD 规则/无障碍问题；
- 没有按钮（纯视频/无关闭）→ 规则无法处理。

---

## 3. GKD 显示「无障碍发生故障」

先判断真假：

```bash
adb shell dumpsys accessibility | grep -E "Bound services|Crashed services"
```

- `Bound services` 里有 GKD、`Crashed services` 为空 → 服务实际正常，属于 UI 状态误报；
- `Bound services` 为空 → 真的掉线，按下面处理。

### 无障碍掉线恢复

1. 系统设置 → 无障碍 → 已下载的应用 → GKD → 关闭；
2. 等 2 秒 → 重新打开 → 允许；
3. 回 GKD 首页确认状态；
4. 仍不行：重启手机后再开一次。

> 不要用 `adb shell am force-stop li.songe.gkd`，会清除服务绑定状态。

---

## 4. 常见问题

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 红果仍有开屏 | Clash 未启动 / 配置未激活 | 看首页是否「运行中」 |
| 只有红果无效 | 专属规则组被关 | 订阅里打开「开屏广告」组 |
| 所有 App 无效 | 无障碍掉线 / 全局组关闭 | 查 `dumpsys accessibility`，开全局组 |
| 点错位置（误触） | 选择器过宽 | 关闭对应组，或加 `excludeMatches` |
| 底部卡片还在 | 只开了网络层 | 打开「局部广告-阅读-底部卡片广告」组 |
| 视频广告跳过失败 | 规则限定 `ReaderActivity` | 确认当前在阅读页；版本更新可能改了 Activity |
| CMFA 保存无反应 | 名称重复 / 空 proxies | 改名；用仓库自带配置 |
| 切配置后不能翻墙 | 当前是纯直连配置 | 切回机场配置 |

---

## 5. 抓规则日志

GKD 设置里有「触发记录」，可看到最近命中的规则。若为空但功能正常，通常是：

- 广告在 DNS 层就被拦掉，根本没有控件可点；
- 触发记录被系统清理。

需要更细的日志时：

```bash
adb logcat -d | grep -i -E "selecttospeak|li.songe.gkd" | tail -50
```
