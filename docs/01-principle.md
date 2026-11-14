# 原理详解

## 0. 一句话

让广告 SDK **拿不到物料**（网络层），同时在广告真的出现时 **把关闭动作做掉**（无障碍层）。

---

## 1. 红果的广告链路

红果短剧是字节系产品，广告主要来自穿山甲（Pangle）与巨量引擎（Ocean Engine）。
一次冷启动大致经历：

```text
App 启动
  │
  ├─ 初始化广告 SDK
  │    ├─ GET pangolin-sdk-toutiao.com        拉 SDK 配置与广告位
  │    ├─ GET pglstatp-toutiao.com            曝光/事件上报
  │    └─ GET ads*-normal.zijieapi.com        请求广告
  │
  ├─ 拉素材
  │    └─ GET *-ad-sign.byteimg.com/*         图片/视频物料（带签名）
  │
  ├─ 渲染开屏
  │    └─ 显示倒计时 + 「跳过」
  │
  └─ 进入首页
```

阅读页还有两条独立链路：

```text
ReaderActivity
  ├─ 底部卡片广告：ImageView + 「关闭此广告」
  └─ 视频广告：v*-reading-ad.qznovelvod.com + 「点击关闭广告并退出小说」
```

短剧页则用「上滑继续观看短剧」作为广告结束的交互。

---

## 2. 第一层：网络层

### 2.1 为什么用 fake-ip

```yaml
dns:
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
```

域名先被解析成 `198.18.x.x` 的假地址，真实解析交给 Clash。
好处：

- 不受运营商 DNS 污染/劫持影响；
- 规则匹配发生在连接建立时，域名信息完整；
- 命中 `REJECT` 时连接直接被拒，不会泄漏真实 IP。

### 2.2 为什么开 sniffer

```yaml
sniffer:
  enable: true
  parse-pure-ip: true
  override-destination: false
```

有些 SDK 会把域名解析结果缓存成 IP，后续直接连 IP，不再走 DNS。
此时 `DOMAIN-SUFFIX` 规则会失效。sniffer 从 TLS ClientHello 的 **SNI** 或 HTTP 的 **Host** 里把域名还原出来，再交给规则引擎判断。

`override-destination: false` 表示只借用域名做匹配，不改写真实连接目标。

### 2.3 REJECT 之后 SDK 会怎样

穿山甲 SDK 的降级路径大致是：

1. 配置请求失败 → 重试 N 次 → 放弃本次广告位；
2. 素材请求 403/超时 → 该素材作废，无备选时不展示；
3. 曝光上报失败 → 不影响展示，但广告主侧统计缺失（对用户无感）。

所以「开屏直接没了」通常不是 bug，而是 SDK 主动放弃了这次展示。

### 2.4 规则为什么这样分组

| 分组 | 目的 | 代价 |
|---|---|---|
| SDK 配置域名 | 断入口，最有效 | 可能影响同 SDK 的其他 App 广告（这正是我们要的） |
| 素材签名域名 | 让物料加载失败 | 图片 CDN 关键词匹配，注意不要误伤普通图片 |
| 广告位正则 | 精确匹配 `ads12-normal` 之类 | 正则写错会漏，需要按版本更新 |
| 曝光/落地页 | 减少跳转与上报 | 基本无副作用 |

`DOMAIN-KEYWORD,-ad-sign.byteimg.com` 用的是关键词而非后缀，因为实际域名形如
`p3-ad-sign.byteimg.com`、`p9-ad-sign.byteimg.com`，前缀不固定。

---

## 3. 第二层：UI 层

### 3.1 AccessibilityService 能做什么

开启无障碍后，App 可以：

- 收到 `TYPE_WINDOW_STATE_CHANGED` / `TYPE_WINDOW_CONTENT_CHANGED` 事件；
- 读取当前窗口的 `AccessibilityNodeInfo` 树（文本、id、类名、坐标、可见性）；
- 对节点执行 `ACTION_CLICK`；
- 通过 `dispatchGesture` 执行滑动。

它**看不到**别的 App 的私有数据，只能看到渲染出来的控件树。这刚好够用：广告的「跳过」一定是个可见控件。

### 3.2 一次匹配的时序

```text
t0  窗口切换（App 启动/Activity 跳转）
t1  GKD 收到事件
t2  fastQuery 在缓存的节点树里做选择器匹配
t3  命中「跳过」→ 计算节点中心点 → ACTION_CLICK
t4  广告关闭，窗口再次变化
```

关键参数（详见 `05-rule-syntax.md`）：

- `matchTime: 10000`：只在切换后的 10 秒内匹配，避免长时间空转；
- `actionMaximum: 2`：每个 App 会话最多点 2 次，防误触连环点；
- `resetMatch: app`：切换 App 时重置计数；
- `fastQuery: true`：用节点缓存加速，减少遍历开销。

### 3.3 防误触

「跳过」这两个字在很多正常界面也存在（引导页、教程、广告预览）。所以规则里加了 `excludeMatches`：

```text
[text*="搜索"] [text="历史记录"] [text$="在搜"]
[text="Submit"] [text*="阅读并同意"] [text="书签"] [text="NEXT"]
[text$="设置"] [text$="选好了"] [text^="下一步"] [text^="完成"] [text*="跳过片"]
[text^="选择"][text*="偏好"/"兴趣"/"喜好"]
```

再加尺寸约束 `width<500 && height<300`，把整屏的「跳过引导」排除掉。

### 3.4 为什么全局组要 `matchAnyApp`

GKD 的 `globalGroups` 默认并不是「无差别对所有 App 生效」。不写 `matchAnyApp: true` 时，它只会对组内 `apps` 列表里的包名生效。

本仓库的 `gkd-global-splash.json` 显式写了：

```json
"matchAnyApp": true,
"matchSystemApp": false,
"matchLauncher": false
```

即：**所有用户安装的 App 都生效，但不动系统界面和桌面**（避免在系统弹窗上误点）。

### 3.5 与专属规则的关系

全局组带：

```json
"disableIfAppGroupMatch": "开屏广告"
```

含义：如果当前 App 有名为「开屏广告」的专属组（红果就有），全局组自动让位，避免同一次开屏被两套规则各点一次。

---

## 4. 两层如何配合

```text
                  ┌────────────────────────────┐
   App 启动 ──────▶│ 广告 SDK 请求配置/素材      │
                  └────────────┬───────────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Clash 规则命中？      │
                    └──────┬────────┬──────┘
                       是  │        │ 否（备用域名/IP/缓存）
                    ┌──────▼──┐  ┌──▼─────────────────┐
                    │ REJECT  │  │ 广告真的渲染出来了  │
                    └──────┬──┘  └──┬─────────────────┘
                           │        │
                    ┌──────▼────────▼──────┐
                    │ 无广告 / GKD 点「跳过」│
                    └──────────┬───────────┘
                               ▼
                          直接进入内容
```

实测表现：冷启动 1 秒内进入内容页；即使 DNS 层漏掉，GKD 也会在广告出现的下一帧点掉。

---

## 5. 边界

这套方案**不处理**：

- 视频贴片广告（在播放器内部，无独立关闭控件）；
- 需要登录/会员才能跳过的广告；
- 广告内容的「软性植入」（信息流里的推广视频，与正常内容同构）；
- 服务端强制下发的开屏（无「跳过」控件、不可关闭）。

遇到上述情况，只能靠会员或换端，不属于本项目范围。
