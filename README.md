# SyncBoard 📋

**跨平台即時剪貼簿同步工具** | **Cross-Platform Real-time Clipboard Sync**

一個簡單高效的瀏覽器端剪貼簿同步工具，支援文字、圖片、檔案即時傳輸，無需安裝額外軟體。

A simple and efficient browser-based clipboard sync tool that supports real-time text, image, and file transfer without additional software installation.

## ✨ 功能特色 / Features

- 🌐 **瀏覽器端**：任何裝置的瀏覽器都能使用
- 📱 **跨平台**：Windows、macOS、Linux、手機通用
- ⚡ **即時同步**：WebSocket 即時傳輸，無延遲
- 📎 **檔案傳輸**：支援任何檔案類型，圖片自動預覽
- 💾 **記憶體模式**：檔案暫存記憶體，不污染硬碟
- 🔒 **區域網路**：完全離線，無需網際網路
- 📋 **一鍵分享**：電腦複製連結，手機掃描 QR 碼

## 🚀 快速開始 / Quick Start

### 方法一：Python 環境 / Method 1: Python Environment

**安裝依賴 / Install Dependencies**
```bash
pip install -r requirements.txt
```

**啟動服務 / Start Service**
```bash
python main.py
```

**連線方式 / Connection Methods**
- 💻 **電腦**：`http://127.0.0.1:56321`
- 📱 **手機**：`http://<電腦IP>:56321`
- 🔗 **分享**：點擊「📋 Copy Link」複製網址
- 📱 **QR 碼**：`http://<電腦IP>:56321/qr`


## 📖 使用說明 / Usage Guide

### 1. 啟動服務 / Start Service
```bash
python main.py
# 或直接執行 SyncBoard.exe
```

### 2. 連線裝置 / Connect Devices
- **電腦對電腦**：複製連結貼到另一台電腦瀏覽器
- **手機連線**：掃描 QR 碼或輸入網址
- **混合使用**：任何組合都能完美運作

### 3. 開始同步 / Start Syncing
- 📝 **文字**：輸入文字按 Send，即時同步到所有裝置
- 📎 **檔案**：點擊「📎 File」上傳，支援任何檔案類型
- 🖼️ **圖片**：自動顯示縮圖預覽
- 📥 **下載**：點擊「Download」下載檔案

### 4. 結束使用 / End Usage
- 關閉瀏覽器分頁即可斷線
- 停止服務：`Ctrl+C` 或關閉終端

## 🔧 進階設定 / Advanced Settings

### 自訂埠號 / Custom Port
```bash
python main.py --port 8080
```

### 防火牆設定 / Firewall Settings
- **Windows**：允許 Python 通過防火牆
- **macOS**：系統偏好設定 → 安全性與隱私 → 防火牆
- **Linux**：`sudo ufw allow 56321`


### 方法二：可執行檔 / Method 2: Executable
## 📦 打包說明 / Packaging Guide

### 使用 PyInstaller 打包 / Package with PyInstaller
```bash
# 安裝打包工具
pip install pyinstaller

# 打包成可執行檔
pyinstaller -F -n SyncBoard --windowed main.py

# 產出檔案
dist/SyncBoard.exe  # Windows
dist/SyncBoard      # macOS/Linux
```

### 部署方式 / Distribution
1. 將 `dist/SyncBoard` 複製到目標電腦
2. 直接執行，無需安裝 Python
3. 支援 Windows 7+、macOS 10.12+、Linux


## 🛠️ 技術規格 / Technical Specs

- **後端**：FastAPI + WebSocket
- **前端**：原生 HTML/CSS/JavaScript
- **傳輸**：HTTP + WebSocket
- **檔案**：記憶體暫存，1小時自動清理
- **網路**：區域網路 mDNS

## 📝 授權條款 / License

MIT License - 詳見 [LICENSE](LICENSE) 檔案

## 🤝 貢獻 / Contributing

歡迎提交 Issue 和 Pull Request！

Welcome to submit issues and pull requests!

---

**SyncBoard** - 讓跨裝置傳輸變得簡單 | Making cross-device transfer simple
