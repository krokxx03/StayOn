#!/bin/bash
# Build standalone macOS app using PyInstaller
set -e

cd "$(dirname "$0")"

echo "Building StayOn.app..."
.venv/bin/pyinstaller --noconfirm --onedir --windowed --name "StayOn" \
  --hidden-import "pyautogui" \
  --hidden-import "Quartz" \
  --hidden-import "AppKit" \
  --hidden-import "rubicon.objc" \
  --collect-submodules "pyautogui" \
  juggle_cursor.py

echo ""
echo "✅ Build complete! Application created at: dist/StayOn.app"
