# 红果短剧去广告 · Android 免 root 方案

两层拦截：**Clash 网络层 REJECT 广告域名** + **GKD 无障碍层兜底点击**。

实测环境：realme RMX6699 / Android 16 / 未 root / GKD 1.13.0 / Clash Meta for Android（CMFA）。

---

## 1. 能做到什么

| 场景 | 处理方式 | 结果 |
|---|---|---|
| 启动开屏广告 | 拦截穿山甲/巨量域名 + 自动点「跳过」 | 冷启动 1 秒内直达内容页 |
| 阅读页底部卡片广告 | 点 X → 点「关闭此广告」 | 卡片消失 |
| 阅读页视频广告 | 横向滑动翻页 | 跳过视频广告 |
| 短剧「上滑继续观看」 | 检测提示后上滑 | 自动续播 |
| 其他 App 开屏 | 全局规则 `matchAnyApp` | 有「跳过」按钮即自动点 |

不消耗机场流量：本方案的去广告配置**没有任何代理节点**，全部流量直连。

---

## 2. 原理

### 2.1 红果的广告从哪里来

红果短剧（`com.phoenix.read`，字节系）的广告素材和配置基本走穿山甲（Pangle）与巨量引擎：

```
App 启动
  └─ 广告 SDK 初始化
       ├─ 拉配置：pangolin-sdk-toutiao.com / pglstatp-toutiao.com
       ├─ 拉素材：*-ad-sign.byteimg.com / ads*-normal.zijieapi.com
       ├─ 曝光上报：ad.oceanengine.com / adlog.oceanengine.com
       └─ 阅读页视频：v*-reading-ad.qznovelvod.com
```

广告 SDK 只有在**配置、素材、上报链路**都可用时才能渲染开屏。任意一环被切断，SDK 会降级为「不展示广告」。

### 2.2 第一层：网络层（Clash / DNS）

核心不是「屏蔽广告内容」，而是**让广告 SDK 拿不到可渲染的物料**。

- `enhanced-mode: fake-ip`：域名先解析到 `198.18.0.0/16`，由 Clash 按规则决定放行还是拒绝，避免真实 DNS 污染影响判断。
- `sniffer.enable + parse-pure-ip`：从 TLS SNI / HTTP Host 里还原域名。即使 App 直接连 IP，也能命中域名规则。这是「硬编码 IP」场景的兜底。
- `REJECT`：命中后 Clash 直接拒绝连接，SDK 收到失败，走降级逻辑。

规则分四类：

| 类型 | 例子 | 作用 |
|---|---|---|
| SDK 配置域名 | `pangolin-sdk-toutiao.com`、`pglstatp-toutiao.com` | 断掉广告请求入口 |
| 素材签名域名 | `-ad-sign.byteimg.com`、`-ad-sign.bytemaimg.com` | 素材 403/超时 |
| 广告位域名 | `ads*-normal.zijieapi.com`、`*reading-ad.qznovelvod.com` | 阅读页视频广告 |
| 曝光/落地页 | `ad.oceanengine.com`、`www.chengzijianzhan.com` | 减少上报与误跳转 |

完整清单见 [`clash/rules-only.yaml`](clash/rules-only.yaml)。

### 2.3 第二层：UI 层（GKD / AccessibilityService）

网络层会漏：备用域名、IP 直连、已缓存素材、非字节系广告。所以再加一层「看到广告就点掉」。

GKD 通过 Android 无障碍服务读取当前窗口的**节点树**，用选择器定位控件，再执行 `click` / `swipe`：

```text
WindowStateChanged
  └─ 读取节点树（fastQuery 加速）
       └─ 选择器匹配
            ├─ [text*="跳过"][text.length<10][visibleToUser=true]  → click
            ├─ [id="com.byted.pangle:id/tt_splash_skip_btn"]        → click
            └─ [text^="上滑继续"][visibleToUser=true]               → swipe
```

红果专属规则见 [`gkd/hongguo-sub.json`](gkd/hongguo-sub.json)，全局开屏规则见 [`gkd/gkd-global-splash.json`](gkd/gkd-global-splash.json)。

### 2.4 为什么必须两层

| 只有网络层 | 只有 UI 层 |
|---|---|
| 换域名 / IP 直连就漏 | 广告已渲染，仍要等 1–3 秒 |
| 已缓存素材仍会展示 | 部分广告无「跳过」按钮（只能上滑/关闭） |
| 无法处理非字节系广告 | 每次启动都要跑一次匹配，耗电略高 |

两层叠加后：**能拦的拦掉（快），拦不住的自动点掉（稳）**。

### 2.5 为什么不需要 root / Xposed / 悬浮窗

- 网络层是 VPNService（本地 TUN），系统原生能力。
- UI 层是 AccessibilityService，用户授权即可。
- GKD 执行规则**不依赖悬浮窗**；悬浮窗只用于触发提示。系统拒绝 `SYSTEM_ALERT_WINDOW` 也不影响点击。

---

## 3. 仓库内容

```text
hongguo-guanggao/
├── README.md                     # 本文
├── clash/
│   ├── adblock-direct.yaml       # 纯去广告 + 全直连（可直接导入 CMFA）
│   └── rules-only.yaml           # 规则块（合并进现有机场配置用）
├── gkd/
│   ├── hongguo-sub.json          # 红果专属规则（开屏/底部卡片/视频广告/上滑）
│   └── gkd-global-splash.json    # 全局开屏跳过（任意 App）
├── docs/
│   ├── 01-principle.md           # 原理详解与时序
│   ├── 02-clash-setup.md         # Clash 部署步骤
│   ├── 03-gkd-setup.md           # GKD 部署步骤
│   ├── 04-verify.md              # 验证命令与排错
│   └── 05-rule-syntax.md         # GKD 订阅/选择器字段速查
├── tools/
│   ├── build_global_sub.py       # 从 AIsouler 订阅提取全局开屏组
│   ├── serve.sh                  # 本地订阅服务器 + adb reverse
│   └── verify.sh                 # adb 一键体检
└── NOTICE.md                     # 规则来源与致谢
```

---

## 4. 快速开始

### 4.1 只想去广告，不需要翻墙

1. 把 [`clash/adblock-direct.yaml`](clash/adblock-direct.yaml) 传到手机。
2. CMFA →「配置」→ 右上 `+` →「从文件导入」→ 选择该文件 → 保存。
3. 点配置左侧圆点激活，回到首页点「点此启动」。
4. 看到 `运行中 / 规则模式 / adblock-direct 已激活` 即成功。

详细步骤与常见坑：[`docs/02-clash-setup.md`](docs/02-clash-setup.md)。

### 4.2 已有机场订阅，想保留节点

不要用 `adblock-direct.yaml`，改用规则块：

1. 打开 [`clash/rules-only.yaml`](clash/rules-only.yaml)。
2. 把 `rules:` 下的条目**整体追加**到你现有配置的 `rules:` 里。
3. 确保这些条目在 `MATCH,xxx` **之前**。
4. 重新导入/更新配置。

这样节点、订阅、分流策略都不变，只多出 21 条 REJECT。

### 4.3 只装 GKD（不用 Clash）

1. 安装 GKD（建议用系统文件管理器点 APK 安装，见 [`docs/03-gkd-setup.md`](docs/03-gkd-setup.md)）。
2. 开启无障碍：系统设置 → 无障碍 → 已下载的应用 → GKD → 开启 → 允许。
3. GKD →「订阅」→ 右下 `+` → 粘贴：
   - 红果规则：`https://raw.githubusercontent.com/yaoyaolingling/hongguo-guanggao/main/gkd/hongguo-sub.json`
   - 全局开屏：`https://raw.githubusercontent.com/yaoyaolingling/hongguo-guanggao/main/gkd/gkd-global-splash.json`
4. 进入订阅确认「开屏广告」「开屏广告-全局」开关为蓝色。

> 仓库若为私有，raw 链接不可用，请改用本地文件方式（`tools/serve.sh` 或 GKD 的本地导入）。

---

## 5. 验证

```bash
# Clash 是否在跑（输出 1 表示 VPN 已建立）
adb shell dumpsys connectivity | grep -c "VPN:com.github.metacubex.clash.meta"

# 无障碍是否绑定
adb shell dumpsys accessibility | grep -E "Bound services|Crashed services"

# GKD 是否存活
adb shell ps -A | grep li.songe.gkd
```

或直接跑 `tools/verify.sh`。

功能验证：`am force-stop com.phoenix.read` 后冷启动，1 秒内应直接进入内容页，无开屏倒计时。

---

## 6. 已知问题

1. **GKD 首页显示「无障碍发生故障」**
   部分 ColorOS/Android 16 机型上，GKD 的 UI 进程重启后收不到服务重连回调，状态文案会误报；但系统侧 `dumpsys accessibility` 仍显示 `Bound services = GKD`，规则照常执行。若规则真的失效，按 `docs/04-verify.md` 的「无障碍掉线」步骤重开一次。

2. **ColorOS 会限制侧载应用的无障碍**
   通过 `adb install` 安装的 APK 可能无法正常使用无障碍。解决：把 APK 放进手机存储，用**系统文件管理器**点开安装（覆盖安装即可，无需卸载）。

3. **CMFA 新建配置时保存无反应**
   实测 `proxies` / `proxy-groups` 全空、或配置名与已有项重复时，点保存可能不生效。本仓库的配置已加入一个从不被引用的占位代理并改了名，可直接导入。

4. **切换配置会影响代理**
   `adblock-direct` 是纯直连配置，启用后无法翻墙；需要时切回原机场配置即可，两者互不影响。

5. **规则时效性**
   域名和控件 ID 会随版本变化。失效时优先看 `docs/04-verify.md`，再考虑更新规则。

---

## 7. 参考与致谢

- 红果专属 GKD 规则：[baidu0013/hongguo-short-drama-gkd](https://github.com/baidu0013/hongguo-short-drama-gkd)
- 全局开屏规则：[AIsouler/GKD_subscription](https://github.com/AIsouler/GKD_subscription)
- 工具：[GKD](https://github.com/gkd-kit/gkd)、[Clash Meta for Android](https://github.com/MetaCubeX/ClashMetaForAndroid)

规则版权归原作者，本仓库只做整合、适配与文档化。详见 [`NOTICE.md`](NOTICE.md)。
