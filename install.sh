#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [[ "$(uname)" == "Darwin" ]]; then
  python - <<'PY'
import tkinter
print('tkinter ok')
PY
  if [ $? -ne 0 ]; then
    if command -v brew >/dev/null 2>&1; then
      brew install python-tk
    else
      echo "Thiếu tkinter. Cài đặt bằng: brew install python-tk"
      exit 1
    fi
  fi
fi

echo ""
echo "==> Cài đặt xong. Chạy trong venv bằng:"
echo "  source .venv/bin/activate"
echo "  python traffic_collector.py"
echo "  python traffic_label_tool.py"
