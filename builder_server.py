import http.server
import socketserver
import json
import os
import shutil
import subprocess

PORT = 8990
BASE_DIR = r"C:\Users\danil\Desktop\САЙТ_ДЛЯ_GITHUB_PAGES"

PROJECT_PATHS = [
    r"C:\Users\danil\Desktop\САЙТ_ДЛЯ_GITHUB_PAGES\index.html",
    r"C:\Users\danil\OneDrive\Рабочий стол\САЙТ_ДЛЯ_GITHUB_PAGES\index.html",
    r"C:\Users\danil\Desktop\ГОТОВО_ДЛЯ_GITHUB_PAGES\index.html",
    r"C:\Users\danil\OneDrive\Рабочий стол\ГОТОВО_ДЛЯ_GITHUB_PAGES\index.html",
]

class ConstructorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/api/save':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                cfg = json.loads(body)
                self.save_configuration(cfg)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "message": "Сохранено успешно!"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode('utf-8'))

        elif self.path == '/api/deploy':
            deploy_script = r"C:\Users\danil\OneDrive\Рабочий стол\deploy.ps1"
            if not os.path.exists(deploy_script):
                deploy_script = r"C:\Users\danil\Desktop\deploy.ps1"
            
            subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", deploy_script])
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def save_configuration(self, cfg):
        src_path = PROJECT_PATHS[0]
        with open(src_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Update theme
        if cfg.get('theme') == 'dark':
            html = html.replace('<html lang="ru" class="light">', '<html lang="ru" class="dark">')
            html = html.replace("localStorage.getItem('meteo_theme') || 'light'", "localStorage.getItem('meteo_theme') || 'dark'")
        else:
            html = html.replace('<html lang="ru" class="dark">', '<html lang="ru" class="light">')
            html = html.replace("localStorage.getItem('meteo_theme') || 'dark'", "localStorage.getItem('meteo_theme') || 'light'")

        # 2. Update brand name
        brand = cfg.get('brandName', '').strip()
        if brand:
            # Replace brand text inside header
            html = html.replace('<span class="tracking-tight">МЕТЕОПОРТАЛ</span>', f'<span class="tracking-tight">{brand}</span>')

        # 3. Update font weight
        fw = cfg.get('fontWeight')
        if fw in ['font-bold', 'font-extrabold', 'font-black']:
            html = html.replace('font-extrabold font-mono tracking-tight text-slate-900', f'{fw} font-mono tracking-tight text-slate-900')
            html = html.replace('font-bold font-mono tracking-tight text-slate-900', f'{fw} font-mono tracking-tight text-slate-900')
            html = html.replace('font-black font-mono tracking-tight text-slate-900', f'{fw} font-mono tracking-tight text-slate-900')

        # 4. Hide/Show blocks via custom style injection
        blocks = cfg.get('blocks', {})
        hidden_styles = []
        if not blocks.get('header', True):
            hidden_styles.append('header { display: none !important; }')
        if not blocks.get('ribbon', True):
            hidden_styles.append('#sticky-ribbon { display: none !important; }')
        if not blocks.get('search', True):
            hidden_styles.append('#search-form { display: none !important; }')
        if not blocks.get('stations', True):
            hidden_styles.append('#stations-bar { display: none !important; }')
        if not blocks.get('tabs', True):
            hidden_styles.append('#tabs-bar { display: none !important; }')
        if not blocks.get('footer', True):
            hidden_styles.append('footer { display: none !important; }')
        if not blocks.get('mobilenav', True):
            hidden_styles.append('nav.md\\:hidden { display: none !important; }')

        # Inject or update hidden blocks style tag
        style_marker = '/* CONSTRUCTOR DYNAMIC STYLES */'
        if style_marker in html:
            # Replace existing
            import re
            html = re.sub(r'/\* CONSTRUCTOR DYNAMIC STYLES \*/.*?/\* END CONSTRUCTOR DYNAMIC STYLES \*/',
                          f'/* CONSTRUCTOR DYNAMIC STYLES */\n    ' + '\n    '.join(hidden_styles) + '\n    /* END CONSTRUCTOR DYNAMIC STYLES */',
                          html, flags=re.DOTALL)
        else:
            if hidden_styles:
                injection = f'\n  <style>\n    /* CONSTRUCTOR DYNAMIC STYLES */\n    ' + '\n    '.join(hidden_styles) + '\n    /* END CONSTRUCTOR DYNAMIC STYLES */\n  </style>'
                html = html.replace('</head>', injection + '\n</head>')

        # Write to all destinations
        for p in PROJECT_PATHS:
            if os.path.exists(os.path.dirname(p)):
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"[CONSTRUCTOR SAVED] {p}")

if __name__ == '__main__':
    print(f"Starting Meteo Studio Server on http://127.0.0.1:{PORT}...")
    server = socketserver.TCPServer(("", PORT), ConstructorHandler)
    server.serve_forever()
