#!/usr/bin/env python3
"""
SyncBoard 打包腳本
Build script for SyncBoard executable
"""

import os
import sys
import subprocess
import platform

def build_executable():
    """打包成可執行檔"""
    print("🚀 開始打包 SyncBoard...")
    
    # 檢查 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("❌ 未安裝 PyInstaller，正在安裝...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # 根據系統選擇參數
    system = platform.system().lower()
    if system == "windows":
        exe_name = "SyncBoard.exe"
        icon = None  # 可以加入 .ico 檔案
    else:
        exe_name = "SyncBoard"
        icon = None  # 可以加入 .icns 檔案
    
    # 打包命令
    cmd = [
        "pyinstaller",
        "-F",  # 單一檔案
        "-n", exe_name,
        "--windowed",  # 無控制台視窗
        "--clean",  # 清理暫存
        "main.py"
    ]
    
    if icon:
        cmd.extend(["--icon", icon])
    
    print(f"📦 執行打包命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 打包完成！")
        print(f"📁 可執行檔位置: dist/{exe_name}")
        print("\n📋 分發說明:")
        print(f"1. 複製 dist/{exe_name} 到目標電腦")
        print("2. 直接執行，無需安裝 Python")
        print("3. 支援 Windows 7+、macOS 10.12+、Linux")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失敗: {e}")
        return False
    
    return True

if __name__ == "__main__":
    build_executable()
