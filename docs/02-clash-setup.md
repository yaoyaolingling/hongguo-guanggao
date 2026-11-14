# Clash 部署

## 1. 选择配置

| 你的情况 | 用哪个文件 |
|---|---|
| 只想安静看红果，不需要翻墙 | `clash/adblock-direct.yaml` |
| 已有机场订阅，想保留节点 | `clash/rules-only.yaml`（合并规则） |

`adblock-direct.yaml` **不含任何节点**，全部流量直连，不消耗机场流量。

---

## 2. CMFA 导入（文件方式）

1. 把 `adblock-direct.yaml` 传到手机（QQ/微信/数据线均可），放到「下载」目录。
2. 打开 Clash Meta for Android。
3. 首页 →「配置」。
4. 右上角 `+` →「从文件导入」。
5. 在文件选择器里找到该文件 → 点选 → 保存。
6. 回到配置列表，点该配置**左侧的圆点**激活（圆点变实心）。
7. 返回首页 →「点此启动」。

成功标志：

```text
运行中
规则模式
adblock-direct 已激活
```

---

## 3. CMFA 导入（URL 方式）

适合把配置放在自己的服务器/GitHub 上：

1. 首页 →「配置」→ 右上 `+` →「从 URL 导入」。
2. 填 raw 地址，例如：
   `https://raw.githubusercontent.com/yaoyaolingling/hongguo-guanggao/main/clash/adblock-direct.yaml`
3. 保存 → 激活 → 启动。

> 若仓库私有，raw 链接不可用，改用文件方式。

---

## 4. 合并到现有机场配置

1. 找到你正在用的配置文件（CMFA 里长按配置 → 编辑，或从订阅导出）。
2. 打开 `clash/rules-only.yaml`，复制 `rules:` 下的全部条目。
3. 粘贴到你配置的 `rules:` 列表**最前面**（至少要在 `MATCH,xxx` 之前）。
4. 保存并重新加载。

注意：

- 不要改动原有的 `proxies` / `proxy-groups`；
- 如果原配置已有同名规则，去重即可；
- 合并后如果出现「配置解析失败」，多半是缩进问题，YAML 用 2 空格。

---

## 5. 实测踩过的坑

### 5.1 点保存没反应

两个原因都遇到过：

1. **配置名重复**：列表里已有同名项时，保存会被静默拒绝。换个名字。
2. **`proxies` / `proxy-groups` 全空**：CMFA 的校验可能不通过。本仓库的配置放了一个从不被引用的占位代理：

```yaml
proxies:
  - name: placeholder-unused
    type: socks5
    server: 127.0.0.1
    port: 1080
```

它不会被任何规则或策略组引用，仅用于通过校验。

### 5.2 启动后无法上网

- 确认最后一条是 `MATCH,DIRECT`；
- 确认没有误选占位代理；
- 关掉「允许局域网」不影响手机自身；
- 如果系统提示 VPN 冲突，先断开其他 VPN/加速器。

### 5.3 想切回机场

配置列表里点机场配置的圆点即可。两份配置互不影响，`adblock-direct` 不会修改你的订阅。

---

## 6. 验证

```bash
# VPN 接口是否建立（输出 1）
adb shell dumpsys connectivity | grep -c "VPN:com.github.metacubex.clash.meta"

# 当前前台配置（部分版本无对外 API，只能看 UI）
# 首页应显示：运行中 / 规则模式 / adblock-direct 已激活
```

CMFA 默认不监听 `external-controller`，所以没有可直接查询的 REST API；以 UI 与 `dumpsys` 为准。
