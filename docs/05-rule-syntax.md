# GKD 订阅与选择器速查

## 1. 订阅结构

```json
{
  "id": 202611091,
  "name": "订阅名称",
  "version": 1,
  "author": "作者",
  "updateUrl": "https://...",
  "checkUpdateUrl": "https://...",
  "supportUri": "https://...",
  "categories": [{ "key": 0, "name": "开屏广告", "enable": true }],
  "globalGroups": [],
  "apps": []
}
```

- `id`：全局唯一，建议用时间戳式数字；
- `version`：整数，更新时递增；
- `apps`：应用专属规则；
- `globalGroups`：跨应用规则。

## 2. 应用专属组

```json
{
  "id": "com.phoenix.read",
  "name": "红果免费短剧",
  "groups": [
    {
      "key": 0,
      "name": "开屏广告",
      "desc": "自动点击[跳过]按钮",
      "actionMaximum": 1,
      "matchTime": 10000,
      "resetMatch": "app",
      "rules": [{ "matches": ["..."] }]
    }
  ]
}
```

## 3. 全局组

```json
{
  "key": 0,
  "name": "开屏广告-全局",
  "order": -10,
  "fastQuery": true,
  "matchTime": 10000,
  "actionMaximum": 2,
  "resetMatch": "app",
  "forcedTime": 10000,
  "disableIfAppGroupMatch": "开屏广告",
  "matchAnyApp": true,
  "matchSystemApp": false,
  "matchLauncher": false,
  "rules": []
}
```

## 4. 组字段

| 字段 | 含义 |
|---|---|
| `key` | 组内唯一编号 |
| `name` / `desc` | 显示名称与说明 |
| `order` | 排序，越小越先匹配 |
| `enable` | 默认是否启用 |
| `matchTime` | 窗口切换后多少毫秒内参与匹配 |
| `actionMaximum` | 单次会话最多执行动作次数 |
| `actionCd` | 两次动作的最小间隔（ms） |
| `actionDelay` | 命中后延迟多久执行 |
| `forcedTime` | 强制重新匹配间隔（ms），用于轮询 |
| `resetMatch` | `app` / `activity` / `match`，计数重置时机 |
| `fastQuery` | 使用节点缓存加速 |
| `activityIds` | 仅在这些 Activity 生效 |
| `matchAnyApp` | 对所有 App 生效 |
| `matchSystemApp` | 是否包含系统应用 |
| `matchLauncher` | 是否包含桌面 |
| `disableIfAppGroupMatch` | 同 App 有该名称的专属组时让位 |
| `apps` | 组级排除/包含列表 |

## 5. 规则字段

| 字段 | 含义 |
|---|---|
| `matches` | 选择器，命中即执行 |
| `anyMatches` | 任一命中即可（与 `matches` 组合使用） |
| `excludeMatches` | 命中则不执行，用于防误触 |
| `action` | `click`（默认）/ `swipe` |
| `swipeArg` | 滑动起止点与时长，支持 `screenWidth` 表达式 |
| `preKeys` | 前置规则编号，必须按顺序触发 |
| `snapshotUrls` | 规则截图（调试用） |

## 6. 选择器语法

```text
[text*="跳过"]                       文本包含
[text^="上滑继续"]                   文本开头
[text$="设置"]                       文本结尾
[text="关闭此广告"]                  文本精确匹配
[id="com.byted.pangle:id/tt_splash_skip_btn"]
[vid="ttlive_player_render_view"]    viewId 简写
[visibleToUser=true]                 当前可见
[width<500 && height<300]            尺寸约束
[childCount=0]                       叶子节点
```

层级关系：

```text
A > B        B 是 A 的直接子节点
A < B        A 是 B 的祖先
A + B        B 是 A 的后一个兄弟
A - B        B 在 A 之后（文档顺序）
A <<n B      向上 n 层
```

## 7. 防误触实践

1. 文本类选择器一定加 `text.length<10` 与尺寸限制；
2. 用 `excludeMatches` 排除「设置/搜索/下一步/完成」等常见词；
3. `actionMaximum` 不要设太大；
4. 新规则先只在自己的测试机上开一天，确认无误触再长期启用。
