#!/usr/bin/env bash
# adb 一键体检：设备 / Clash VPN / 无障碍绑定 / GKD 进程

set -uo pipefail

export MSYS_NO_PATHCONV=1
ADB="${ADB:-$LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe}"

echo "== 设备 =="
"$ADB" devices

echo
echo "== Clash VPN 接口（1 = 已建立）=="
"$ADB" shell dumpsys connectivity 2>/dev/null \
  | grep -c "VPN:com.github.metacubex.clash.meta" || true

echo
echo "== 无障碍 =="
"$ADB" shell dumpsys accessibility 2>/dev/null \
  | grep -E "Bound services|Enabled services|Crashed services" || true

echo
echo "== GKD 进程 =="
"$ADB" shell ps -A 2>/dev/null | grep li.songe.gkd || echo "未运行"

echo
echo "== 电池白名单 =="
"$ADB" shell dumpsys deviceidle whitelist 2>/dev/null | grep li.songe.gkd || echo "未加入"
