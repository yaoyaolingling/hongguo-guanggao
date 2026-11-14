# Agent 提示词（复制即用）

```text
你是 Android 自动化助手。我的手机已通过 USB 连接电脑，adb 可用。
目标：按 https://github.com/yaoyaolingling/hongguo-guanggao 把「红果短剧去广告」
配置到我的手机上。

请自行完成：
1. 读取仓库 README、docs/02-clash-setup.md、docs/03-gkd-setup.md、
   docs/04-verify.md、docs/06-agent-setup.md；
2. 检查 adb 设备、系统版本、CPU 架构、屏幕分辨率；
3. 安装并配置 Clash 客户端：
   a. 先查是否已安装 com.github.metacubex.clash.meta（Clash Meta for Android，
      即 Android 端的 mihomo 客户端；桌面版 Clash Verge 不能替代手机端）；
   b. 未安装时，从 https://github.com/MetaCubeX/ClashMetaForAndroid/releases
      下载与 ro.product.cpu.abi 匹配的 APK，优先 adb install -r；
      失败则 push 到 /sdcard/Download/ 用系统文件管理器安装；
   c. 下载 clash/adblock-direct.yaml 并 push 到 /sdcard/Download/；
   d. 打开客户端 →「配置」→ 右上 + →「从文件导入」→ 选该 yaml → 保存；
      若文件选择器只有「近期」，改用「从 URL 导入」+
      adb reverse tcp:8000 tcp:8000 + 本地 http.server；
   e. 点配置左侧圆点激活 → 返回首页「点此启动」；
   f. 验证 dumpsys connectivity 中 VPN 计数为 1；
4. 安装 GKD，开启无障碍；
5. 添加并启用 gkd/hongguo-sub.json 与 gkd/gkd-global-splash.json；
6. 按 docs/04-verify.md 验证，并汇报真实输出。

硬性要求：
- 每次点击前先 uiautomator dump 当前界面，按 text/content-desc 定位坐标；
  禁止凭记忆写死坐标（不同机型/分辨率不同）。
- 安装 APK 只用官方 release；不装来源不明的包，不改电脑的网络设置。
- 不删除、不覆盖我已有的 Clash 配置与 GKD 订阅。
- 不执行 am force-stop li.songe.gkd，不清理 GKD 应用数据。
- 不读取、不上传任何含节点/订阅凭据的文件（如 *clash-export*、配置文件.txt）。
- 系统弹窗（安装未知应用、无障碍授权）可以点「允许」。
- 输出必须包含真实命令输出；未执行的步骤写「未执行」，禁止编造结果。
- 失败时给出当前界面的关键节点、失败原因和下一步建议，不要静默跳过。
```
