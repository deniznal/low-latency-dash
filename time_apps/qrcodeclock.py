import socket, threading, time, re
from http.server import SimpleHTTPRequestHandler, HTTPServer

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

LAN_IP = get_local_ip()
PORT   = 8080

INDEX_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OBS Live QR (Latency)</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
  <style>
    body {{ margin:0; background:#fff; display:flex;
           flex-direction:column; align-items:center;
           justify-content:center; font-family:Arial,sans-serif; }}
    #qrcode {{ width:256px; height:256px; }}
    #ts {{ margin-top:8px; font-size:12px; color:#666; }}
  </style>
</head>
<body>
  <div id="qrcode"></div>
  <div id="ts">loading…</div>
  <script>
    const qrDiv = document.getElementById('qrcode');
    const tsDiv = document.getElementById('ts');
    const BASE = 'http://{LAN_IP}:{PORT}';

    // one QRCode instance
    const qr = new QRCode(qrDiv, {{
      text:'', width:256, height:256,
      correctLevel:QRCode.CorrectLevel.H
    }});

    function tick() {{
      const t = Date.now();
      const path = `/latency_${{t}}.html`;
      qr.clear();
      qr.makeCode(BASE + path);
      tsDiv.textContent = 'frame-ts: ' + t;
    }}

    tick();
    setInterval(tick, 350);
  </script>
</body>
</html>
"""

LATENCY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Latency Report</title>
  <style>
    body { font-family:Arial,sans-serif; text-align:center;
           margin-top:40px; color:#333; }
    .val { font-size:32px; margin:20px 0; }
    small { color:#666; }
  </style>
</head>
<body>
  <h1>Stream Latency</h1>
  <div class="val" id="latency">Calculating…</div>
  <div><small>Frame timestamp: <span id="ts">{ts}</span></small></div>
  <div><small>Now: <span id="now"></span></small></div>

  <script>
    const ts = parseInt(document.getElementById('ts').textContent, 10);
    const now = Date.now();
    document.getElementById('now').textContent = now;
    document.getElementById('latency').textContent = (now - ts) + ' ms';
  </script>
</body>
</html>
"""

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type','text/html')
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode('utf-8'))
            return

        m = re.fullmatch(r'/latency_(\d+)\.html', self.path)
        if m:
            ts = m.group(1)
            page = LATENCY_HTML.replace('{ts}', ts)
            self.send_response(350)
            self.send_header('Content-Type','text/html')
            self.end_headers()
            self.wfile.write(page.encode('utf-8'))
            return

        super().do_GET()

def run():
    print(f"Serving on http://{LAN_IP}:{PORT}")
    httpd = HTTPServer(('', PORT), Handler)
    httpd.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=run, daemon=True).start()
    while True:
        time.sleep(1)