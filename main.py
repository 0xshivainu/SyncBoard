from __future__ import annotations

import argparse
import os
import socket
import tempfile
import time
import uuid
import shutil
from io import BytesIO
from typing import Optional, Set, List, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, Response, FileResponse
import uvicorn
import qrcode


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def build_app() -> FastAPI:
    app = FastAPI(title="SyncBoard Browser")
    sockets: Set[WebSocket] = set()
    messages: List[Dict] = []  # {id, content, ts, sender, type}
    
    # 檔案暫存在記憶體中，不下載就消失
    file_cache: Dict[str, bytes] = {}  # {file_id: file_content}
    file_metadata: Dict[str, Dict] = {}  # {file_id: {filename, size, timestamp}}
    
    # 清理超過 1 小時的記憶體檔案
    def cleanup_old_files():
        try:
            current_time = time.time()
            expired_files = []
            for file_id, metadata in file_metadata.items():
                if current_time - metadata['timestamp'] > 3600:  # 1 小時
                    expired_files.append(file_id)
            
            for file_id in expired_files:
                file_cache.pop(file_id, None)
                file_metadata.pop(file_id, None)
        except Exception:
            pass

    @app.get("/")
    async def index() -> HTMLResponse:
        html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SyncBoard</title>
  <style>
    :root { --bg: #0b0f1a; --panel: #111827; --card: #0f172a; --text: #e5e7eb; --muted: #94a3b8; --accent: #22d3ee; }
    html, body { height: 100%; margin: 0; }
    body { background: linear-gradient(135deg, #0b0f1a, #0a0f2c); color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; }
    .container { max-width: 860px; margin: 0 auto; padding: 12px; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; }
    .header { display: flex; align-items: center; justify-content: space-between; padding: 8px 0 12px 0; flex-wrap: wrap; gap: 8px; }
    .brand { font-weight: 700; letter-spacing: 0.5px; font-size: 18px; }
    .brand .accent { color: var(--accent); }
    .chat { flex: 1; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 12px; overflow: auto; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02); min-height: 0; margin-bottom: 12px; }
    .msg { background: var(--card); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 10px 12px; margin: 8px 0; display: flex; flex-direction: column; gap: 8px; }
    .msg .meta { font-size: 12px; color: var(--muted); display: flex; gap: 8px; }
    .msg .content { white-space: pre-wrap; word-wrap: break-word; }
    .msg .actions { display: flex; gap: 6px; flex-wrap: wrap; }
    .msg.file { border-left: 3px solid var(--accent); }
    .msg .file-info { display: flex; align-items: center; gap: 8px; margin: 4px 0; flex-wrap: wrap; }
    .msg .file-icon { width: 16px; height: 16px; flex-shrink: 0; }
    .msg .file-link { color: var(--accent); text-decoration: none; word-break: break-all; }
    .msg .file-link:hover { text-decoration: underline; }
    .msg .image-preview { max-width: 100%; max-height: 200px; border-radius: 8px; margin: 8px 0; cursor: pointer; }
    .msg .image-preview:hover { opacity: 0.8; }
    .input { display: flex; flex-direction: column; gap: 10px; }
    .input-row { display: flex; gap: 10px; align-items: flex-end; }
    .input-controls { display: flex; flex-direction: column; gap: 8px; min-width: 80px; }
    textarea { resize: vertical; min-height: 80px; max-height: 40vh; background: var(--panel); color: var(--text); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 10px 12px; font-size: 14px; outline: none; box-shadow: 0 0 0 1px rgba(34,211,238,0); transition: box-shadow .2s ease; flex: 1; }
    textarea:focus { box-shadow: 0 0 0 1px rgba(34,211,238,.35); }
    .controls { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .btn { background: linear-gradient(135deg, #06b6d4, #22d3ee); color: #001018; border: none; padding: 8px 12px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; white-space: nowrap; }
    .btn.secondary { background: transparent; color: var(--text); border: 1px solid rgba(255,255,255,0.12); }
    .hint { color: var(--muted); font-size: 11px; margin-top: 6px; }
    .name { background: var(--panel); color: var(--text); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 8px 10px; width: 120px; font-size: 14px; }
    
    @media (max-width: 768px) {
      .container { padding: 8px; }
      .header { flex-direction: column; align-items: stretch; }
      .controls { justify-content: space-between; }
      .name { width: 100%; }
      .input-row { flex-direction: row; align-items: flex-end; }
      .input-controls { flex-direction: column; min-width: 80px; }
      .btn { padding: 8px 10px; font-size: 12px; }
      .msg .actions { justify-content: flex-start; }
      .msg .file-info { flex-direction: column; align-items: flex-start; gap: 4px; }
      .msg .image-preview { max-width: 100%; max-height: 150px; }
      textarea { min-height: 60px; }
    }
  </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <div class="brand">Sync<span class="accent">Board</span></div>
        <div class="controls">
          <input id="name" class="name" placeholder="Your name" />
          <button id="copyLink" class="btn secondary">📋 Copy Link</button>
          <a class="btn secondary" href="/qr" target="_blank">QR</a>
        </div>
      </div>
      <div id="chat" class="chat"></div>
      <div class="input">
        <div class="input-row">
          <textarea id="msg" placeholder="Type and press Send..."></textarea>
          <div class="input-controls">
            <button id="send" class="btn">Send</button>
            <button id="upload" class="btn secondary">📎 File</button>
            <button id="clear" class="btn secondary">Clear</button>
          </div>
        </div>
      </div>
      <div class="hint">Tip: On mobile HTTP, browsers may require a tap to copy.</div>
    </div>
    <script>
      const elChat = document.getElementById('chat');
      const elMsg = document.getElementById('msg');
      const elName = document.getElementById('name');
      const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');

      const fmt = (ts) => new Date(ts * 1000).toLocaleString();
      const scrollBottom = () => { elChat.scrollTop = elChat.scrollHeight; };

      function renderMessage(m) {
        const card = document.createElement('div');
        card.className = m.type === 'file' ? 'msg file' : 'msg';
        card.setAttribute('data-id', m.id);
        const content = document.createElement('div');
        content.className = 'content';
        if (m.type === 'file') {
          const fileInfo = document.createElement('div');
          fileInfo.className = 'file-info';
          const isImage = /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(m.filename);
          if (isImage) {
            const img = document.createElement('img');
            img.className = 'image-preview';
            img.src = `/files/${m.file_id}`;
            img.alt = m.filename;
            img.onclick = () => window.open(`/files/${m.file_id}`, '_blank');
            content.appendChild(img);
          }
          fileInfo.innerHTML = `<span class="file-icon">${isImage ? '🖼️' : '📎'}</span><a href="/files/${m.file_id}" class="file-link" target="_blank">${m.filename}</a> <span style="color: var(--muted);">(${m.size} bytes)</span>`;
          content.appendChild(fileInfo);
        } else {
          content.textContent = m.content || '';
        }
        const actions = document.createElement('div');
        actions.className = 'actions';
        if (m.type !== 'file') {
          const copy = document.createElement('button');
          copy.textContent = 'Copy';
          copy.className = 'btn secondary';
          copy.onclick = async () => { try { await navigator.clipboard.writeText(m.content || ''); } catch(e){} };
          actions.appendChild(copy);
        } else {
          const download = document.createElement('button');
          download.textContent = 'Download';
          download.className = 'btn secondary';
          download.onclick = () => { window.open(`/files/${m.file_id}`, '_blank'); };
          actions.appendChild(download);
        }
        const del = document.createElement('button');
        del.textContent = 'Delete';
        del.className = 'btn secondary';
        del.onclick = () => { ws.send(JSON.stringify({ type: 'delete', id: m.id })); };
        actions.appendChild(del);
        const meta = document.createElement('div');
        meta.className = 'meta';
        meta.textContent = `${m.sender || 'Anon'} • ${fmt(m.ts)}`;
        card.appendChild(content);
        card.appendChild(actions);
        card.appendChild(meta);
        elChat.appendChild(card);
      }

      function renderHistory(items){ elChat.innerHTML=''; (items||[]).forEach(renderMessage); scrollBottom(); }

      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === 'history') { renderHistory(data.items); return; }
          if (data.type === 'message') { renderMessage(data.item); scrollBottom(); return; }
          if (data.type === 'delete') { 
            const el = document.querySelector(`[data-id="${data.id}"]`);
            if (el) el.remove();
            return;
          }
          if (data.type === 'clear') { renderHistory([]); return; }
        } catch {}
      };

      document.getElementById('send').onclick = () => {
        const sender = elName.value.trim() || 'Anon';
        const content = elMsg.value;
        ws.send(JSON.stringify({ type: 'message', sender, content, msg_type: 'text' }));
        elMsg.value = '';
      };
      document.getElementById('upload').onclick = async () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.onchange = async (e) => {
          const file = e.target.files[0];
          if (!file) return;
          const formData = new FormData();
          formData.append('file', file);
          try {
            const res = await fetch('/upload', { method: 'POST', body: formData });
            const data = await res.json();
            const sender = elName.value.trim() || 'Anon';
            ws.send(JSON.stringify({ type: 'message', sender, msg_type: 'file', file_id: data.file_id, filename: data.filename, size: data.size }));
          } catch (e) { console.error('Upload failed:', e); }
        };
        input.click();
      };
      document.getElementById('clear').onclick = () => {
        ws.send(JSON.stringify({ type: 'clear' }));
      };
      document.getElementById('copyLink').onclick = async () => {
        const url = window.location.href;
        try {
          await navigator.clipboard.writeText(url);
          const btn = document.getElementById('copyLink');
          const originalText = btn.textContent;
          btn.textContent = '✅ Copied!';
          setTimeout(() => { btn.textContent = originalText; }, 2000);
        } catch (e) {
          // 備援方案：顯示網址讓使用者手動複製
          prompt('Copy this link:', url);
        }
      };
    </script>
  </body>
  </html>
        """
        return HTMLResponse(content=html)

    @app.get("/qr")
    async def qr() -> Response:
        url = f"http://{get_local_ip()}:56321"
        img = qrcode.make(url)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")

    @app.post("/upload")
    async def upload_file(file: UploadFile = File(...)) -> dict:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename")
        
        file_id = str(uuid.uuid4())
        content = await file.read()
        
        # 儲存到記憶體
        file_cache[file_id] = content
        file_metadata[file_id] = {
            "filename": file.filename,
            "size": len(content),
            "timestamp": time.time()
        }
        
        # 清理舊檔案
        cleanup_old_files()
        
        return {"file_id": file_id, "filename": file.filename, "size": len(content)}

    @app.get("/files/{file_id}")
    async def get_file(file_id: str) -> Response:
        if file_id not in file_cache:
            raise HTTPException(status_code=404, detail="File not found or expired")
        
        metadata = file_metadata.get(file_id, {})
        filename = metadata.get("filename", "unknown")
        content = file_cache[file_id]
        
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        sockets.add(ws)
        try:
            # send history on connect
            await ws.send_json({"type": "history", "items": messages})
            while True:
                data = await ws.receive_json()
                t = data.get("type")
                if t == "message":
                    sender = (data.get("sender") or "Anon").strip() or "Anon"
                    msg_type = data.get("msg_type", "text")
                    if msg_type == "text":
                        content = (data.get("content") or "").rstrip()
                        if not content:
                            continue
                        item = {"id": len(messages)+1, "content": content, "ts": time.time(), "sender": sender, "type": "text"}
                    elif msg_type == "file":
                        file_id = data.get("file_id")
                        filename = data.get("filename")
                        size = data.get("size")
                        if not file_id or not filename:
                            continue
                        item = {"id": len(messages)+1, "file_id": file_id, "filename": filename, "size": size, "ts": time.time(), "sender": sender, "type": "file"}
                    messages.append(item)
                    for peer in list(sockets):
                        try:
                            await peer.send_json({"type": "message", "item": item})
                        except Exception:
                            try:
                                await peer.close()
                            except Exception:
                                pass
                            sockets.discard(peer)
                elif t == "delete":
                    msg_id = data.get("id")
                    messages[:] = [m for m in messages if m.get("id") != msg_id]
                    for peer in list(sockets):
                        try:
                            await peer.send_json({"type": "delete", "id": msg_id})
                        except Exception:
                            try:
                                await peer.close()
                            except Exception:
                                pass
                            sockets.discard(peer)
                elif t == "clear":
                    messages.clear()
                    for peer in list(sockets):
                        try:
                            await peer.send_json({"type": "clear"})
                        except Exception:
                            try:
                                await peer.close()
                            except Exception:
                                pass
                            sockets.discard(peer)
        except WebSocketDisconnect:
            pass
        finally:
            sockets.discard(ws)

    return app


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SyncBoard Browser Server")
    p.add_argument("--port", type=int, default=56321)
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    app = build_app()
    
    print(f"🚀 即時傳輸模式：檔案暫存記憶體，不下載就消失")
    print(f"🌐 服務啟動: http://127.0.0.1:{args.port}")
    print(f"📱 手機連線: http://{get_local_ip()}:{args.port}")
    print(f"🔗 QR 碼: http://{get_local_ip()}:{args.port}/qr")
    
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()


