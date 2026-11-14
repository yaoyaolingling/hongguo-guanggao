#!/usr/bin/env bash
# 本地订阅服务器 + adb reverse
# 用途：手机无法直接访问 raw.githubusercontent.com 时，把仓库通过 127.0.0.1 暴露给手机
#
# 用法：bash tools/serve.sh
# 然后在 GKD 里添加：http://127.0.0.1:8000/gkd/hongguo-sub.json

set -euo pipefail

export MSYS_NO_PATHCONV=1
PORT="${PORT:-8000}"
ADB="${ADB:-$LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe}"

cd "$(dirname "$0")/.."

"$ADB" reverse "tcp:$PORT" "tcp:$PORT"
echo "手机内可用地址："
echo "  红果规则  http://127.0.0.1:$PORT/gkd/hongguo-sub.json"
echo "  全局开屏  http://127.0.0.1:$PORT/gkd/gkd-global-splash.json"
echo "  Clash     http://127.0.0.1:$PORT/clash/adblock-direct.yaml"
echo

python -m http.server "$PORT" --bind 127.0.0.1
