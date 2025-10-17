from http.server import BaseHTTPRequestHandler, HTTPServer
import random

# test2.py
# 簡單本機抽籤網頁 (不需第三方套件)
# 執行： python .\test2.py
# 在瀏覽器開啟 http://localhost:8000


HTML = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>抽籤小工具</title>
<style>
    body { font-family: system-ui, "Segoe UI", Roboto, "Noto Sans", Arial; max-width:800px; margin:40px auto; padding:0 20px; color:#222; }
    h1 { text-align:center; }
    textarea { width:100%; height:160px; font-size:14px; padding:8px; box-sizing:border-box; }
    .row { display:flex; gap:8px; margin:10px 0; align-items:center; }
    input[type="number"] { width:80px; padding:6px; }
    button { padding:8px 14px; cursor:pointer; }
    #result { margin-top:18px; font-size:20px; min-height:48px; padding:12px; background:#f7f7f7; border-radius:6px; }
    .name { display:inline-block; margin:6px; padding:8px 12px; background:#fff; border:1px solid #ddd; border-radius:6px; }
    .winner { background: linear-gradient(90deg,#ffd54a,#ffb74d); border-color:#ff9800; transform:scale(1.05); box-shadow:0 6px 18px rgba(0,0,0,0.12); }
    .note { color:#666; font-size:13px; }
</style>
</head>
<body>
<h1>抽籤小工具</h1>
<p class="note">每列或以逗號輸入一位參加者名稱，空行會被忽略。</p>

<label>參與者清單：</label>
<textarea id="names" placeholder="例如：&#10;小明&#10;小華&#10;小美"></textarea>

<div class="row">
    <label>抽取名額：</label>
    <input id="count" type="number" min="1" value="1">
    <button id="drawBtn">抽籤</button>
    <button id="randomFill">測試用隨機產生 10 名</button>
</div>

<div id="result" aria-live="polite"></div>

<script>
function parseNames(text) {
    // 支援換行或逗號分隔，移除空白
    const parts = text.split(/[,\\n]/).map(s => s.trim()).filter(s => s);
    // 移除重複
    return Array.from(new Set(parts));
}

function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

function showWinners(winners) {
    const box = document.getElementById('result');
    box.innerHTML = '';
    winners.forEach((w, i) => {
        const span = document.createElement('div');
        span.className = 'name' + (i === 0 ? ' winner' : '');
        span.textContent = w;
        box.appendChild(span);
    });
}

document.getElementById('drawBtn').addEventListener('click', () => {
    const raw = document.getElementById('names').value;
    const names = parseNames(raw);
    const count = Math.max(1, Math.floor(Number(document.getElementById('count').value) || 1));
    if (names.length === 0) {
        alert('請先輸入至少一位參與者名稱。');
        return;
    }
    if (count > names.length) {
        alert('抽取名額不能大於參與人數。');
        return;
    }

    // 快速動畫：短暫輪播隨機名稱，再顯示最終結果
    const display = document.getElementById('result');
    display.textContent = '';
    let rounds = 30;
    const interval = 60;
    const pool = names.slice();
    const anim = setInterval(() => {
        const t = pool[Math.floor(Math.random() * pool.length)];
        display.innerHTML = '<div class="name">' + t + '</div>';
        rounds--;
        if (rounds <= 0) {
            clearInterval(anim);
            const final = shuffle(names).slice(0, count);
            showWinners(final);
        }
    }, interval);
});

// 測試輔助按鈕
document.getElementById('randomFill').addEventListener('click', () => {
    const arr = [];
    for (let i = 1; i <= 10; i++) arr.push('人員' + i);
    document.getElementById('names').value = arr.join('\\n');
    document.getElementById('count').value = 3;
});
</script>
</body>
</html>
"""

class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
                path = self.path.split('?',1)[0]
                if path in ('/', '/index.html'):
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/html; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(HTML.encode('utf-8'))
                else:
                        self.send_response(404)
                        self.send_header('Content-Type', 'text/plain; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(b'Not Found')

        def log_message(self, format, *args):
                # 靜默/簡化日誌顯示
                print("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format%args))

if __name__ == '__main__':
        HOST = '0.0.0.0'
        PORT = 8000
        server = HTTPServer((HOST, PORT), SimpleHandler)
        print(f'啟動抽籤頁面：請在瀏覽器開啟 http://localhost:{PORT} (按 Ctrl+C 停止)')
        try:
                server.serve_forever()
        except KeyboardInterrupt:
                print('已停止伺服器。')
                server.server_close()