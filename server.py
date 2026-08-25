import os
import json
import sqlite3
import smtplib
import csv
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 8085
DB_FILE = os.path.join(os.path.dirname(__file__), "database.db")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# Default Config
DEFAULT_CONFIG = {
    "admin_password": "admin",
    "email_enabled": False,
    "smtp_server": "smtp.yandex.ru",
    "smtp_port": 465,
    "smtp_user": "info@profexpert76.ru",
    "smtp_password": "",
    "recipient_email": "info@profexpert76.ru"
}

def get_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            company TEXT,
            source TEXT,
            status TEXT DEFAULT 'NEW'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            title TEXT NOT NULL,
            badge TEXT NOT NULL,
            read_time TEXT,
            author TEXT,
            slug TEXT UNIQUE NOT NULL,
            content_json TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_lead(name, phone, company, source="Сайт"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO leads (created_at, name, phone, company, source, status)
        VALUES (?, ?, ?, ?, ?, 'NEW')
    ''', (created_at, name, phone, company, source))
    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return lead_id, created_at

def get_all_leads():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, name, phone, company, source, status FROM leads ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    leads = []
    for r in rows:
        leads.append({
            "id": r[0],
            "created_at": r[1],
            "name": r[2],
            "phone": r[3],
            "company": r[4],
            "source": r[5],
            "status": r[6]
        })
    return leads

def send_email_notification(name, phone, company, created_at, source):
    config = get_config()
    if not config.get("email_enabled"):
        print(f"[SMTP LOG] Email notification disabled. Lead from {name} ({phone}) saved to DB.")
        return
    try:
        msg = f"Subject: Новая заявка с сайта ООО «ПрофЭксперт»\nContent-Type: text/plain; charset=utf-8\n\n"
        msg += f"Новая заявка с сайта ООО «ПрофЭксперт»\n"
        msg += f"-----------------------------------------\n"
        msg += f"Имя: {name}\n"
        msg += f"Телефон: {phone}\n"
        msg += f"Компания: {company}\n"
        msg += f"Дата: {created_at}\n"
        msg += f"Источник: {source}\n"
        
        server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
        server.login(config["smtp_user"], config["smtp_password"])
        server.sendmail(config["smtp_user"], config["recipient_email"], msg.encode('utf-8'))
        server.quit()
        print(f"[SMTP SUCCESS] Notification email sent to {config['recipient_email']}")
    except Exception as e:
        print(f"[SMTP ERROR] Failed to send email: {e}")

def get_all_articles():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at, title, badge, read_time, author, slug, content_json FROM articles ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    articles = []
    for r in rows:
        articles.append({
            "id": r[0],
            "created_at": r[1],
            "title": r[2],
            "badge": r[3],
            "read_time": r[4],
            "author": r[5],
            "slug": r[6],
            "content_json": r[7],
            "url": f"blog/{r[6]}.html"
        })
    return articles

def generate_article_html(title, badge, read_time, author, created_at, blocks, slug):
    blog_dir = os.path.join(os.path.dirname(__file__), "blog")
    os.makedirs(blog_dir, exist_ok=True)
    file_path = os.path.join(blog_dir, f"{slug}.html")

    body_html = ""
    for block in blocks:
        btype = block.get("type")
        val = block.get("value", "")
        if btype == "h2":
            body_html += f"<h2>{val}</h2>\n"
        elif btype == "p":
            body_html += f"<p>{val}</p>\n"
        elif btype == "quote":
            author_text = block.get("author", "Эксперт ООО «ПрофЭксперт»")
            body_html += f'<blockquote class="article-quote"><p>«{val}»</p><cite>— {author_text}</cite></blockquote>\n'
        elif btype == "table":
            headers = block.get("headers", ["ПАРАМЕТР / ПРОЦЕДУРА", "СТАРЫЙ ПОРЯДОК", "НОВЫЙ ПОРЯДОК"])
            rows = block.get("rows", [])
            body_html += '<div class="table-wrapper"><table class="article-table"><thead><tr>'
            for h in headers:
                body_html += f'<th>{h}</th>'
            body_html += '</tr></thead><tbody>'
            for row in rows:
                body_html += '<tr>'
                for cell in row:
                    body_html += f'<td>{cell}</td>'
                body_html += '</tr>'
            body_html += '</tbody></table></div>\n'

    html_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — ООО «ПрофЭксперт»</title>
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
  <header class="header" id="header">
    <div class="container">
      <a href="../index.html" class="logo" id="logoLink">
        <img src="../assets/logo_transparent.png" alt="ООО ПрофЭксперт" class="brand-logo-img">
        <div class="logo-text">
          <span>Охрана труда для предприятий</span>
        </div>
      </a>
      <nav>
        <ul class="nav-menu" id="navMenu">
          <li><a href="../index.html#about" class="nav-link">О компании</a></li>
          <li><a href="../index.html#services" class="nav-link">Решения</a></li>
          <li><a href="../index.html#industry" class="nav-link">Компетенции</a></li>
          <li><a href="../index.html#blog" class="nav-link">Экспертный блог</a></li>
          <li><a href="../index.html#contacts" class="nav-link">Контакты</a></li>
        </ul>
      </nav>
      <div class="header-cta">
        <button class="btn btn-primary header-btn js-open-modal" data-modal-title="Получить консультацию">
          Получить консультацию
        </button>
      </div>
    </div>
  </header>

  <main class="main-content">
    <article class="article-section section">
      <div class="container container-narrow">
        <nav class="breadcrumbs" aria-label="Хлебные крошки">
          <a href="../index.html">Главная</a>
          <span class="sep">/</span>
          <a href="../index.html#blog">Статьи</a>
          <span class="sep">/</span>
          <span class="current">{title}</span>
        </nav>

        <header class="article-header">
          <span class="badge badge-dark">{badge}</span>
          <h1 class="article-title">{title}</h1>
          <div class="article-meta-bar">
            <span>{created_at}</span>
            <span class="dot">•</span>
            <span>{read_time}</span>
            <span class="dot">•</span>
            <span>АВТОР: {author}</span>
          </div>
        </header>

        <div class="article-body">
          {body_html}
        </div>

        <div class="article-footer-nav">
          <a href="../index.html#blog" class="btn btn-secondary">← Вернуться к статьям</a>
        </div>
      </div>
    </article>
  </main>

  <footer class="footer" id="contacts">
    <div class="container">
      <div class="footer-hero-contacts">
        <a href="tel:+79775558866" class="footer-phone">+7-977-555-88-66</a>
        <a href="mailto:info@profexpert76.ru" class="footer-email">INFO@PROFEXPERT76.RU</a>
      </div>

      <div class="footer-nav-grid">
        <div>
          <div class="logo" style="margin-bottom: 16px;">
            <img src="../assets/logo_transparent.png" alt="ООО ПрофЭксперт" class="brand-logo-img">
            <div class="logo-text">
              <span>Охрана труда для предприятий</span>
            </div>
          </div>
          <p style="font-size: 13px; color: var(--color-secondary);">
            Профессиональный аутсорсинг охраны труда, проведение СОУТ, оценка рисков и подготовка к проверкам Роструда.
          </p>
        </div>

        <div>
          <h4 class="footer-col-title">УСЛУГИ</h4>
          <ul class="footer-list">
            <li><a href="../index.html#services">Аутсорсинг охраны труда</a></li>
            <li><a href="../index.html#services">Разработка документов</a></li>
            <li><a href="../index.html#services">Обучение сотрудников</a></li>
            <li><a href="../index.html#services">Подготовка к проверкам</a></li>
          </ul>
        </div>

        <div>
          <h4 class="footer-col-title">КОМПАНИЯ</h4>
          <ul class="footer-list">
            <li><a href="../index.html#about">О нас</a></li>
            <li><a href="../index.html#industry">Специалисты</a></li>
            <li><a href="../index.html#advantages">Сертификаты</a></li>
            <li><a href="../index.html#blog">Статьи</a></li>
          </ul>
        </div>

        <div>
          <h4 class="footer-col-title">КОНТАКТЫ</h4>
          <ul class="footer-list">
            <li><a href="../index.html#regions">Рыбинск (Офис)</a></li>
            <li><a href="tel:+79775558866">Телефон</a></li>
            <li><a href="mailto:info@profexpert76.ru">Email</a></li>
            <li><a href="../index.html#regions">Офис и выезды</a></li>
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <div>© 2026 ООО «ПрофЭксперт». Все права защищены.</div>
        <div>Охрана труда и промышленная безопасность</div>
      </div>
    </div>
  </footer>

  <div class="modal-overlay" id="modalOverlay">
    <div class="modal-box">
      <button class="modal-close" id="modalCloseBtn">&times;</button>
      <h3 id="modalTitle" style="margin-bottom: 8px;">Получить консультацию</h3>
      <p style="margin-bottom: 24px; font-size: 14px;">Оставьте контакты — эксперт свяжется с вами для уточнения деталей.</p>
      <form id="leadForm">
        <div class="form-group">
          <label for="formName">Ваше имя</label>
          <input type="text" id="formName" class="form-input" placeholder="Иван Иванов" required>
        </div>
        <div class="form-group">
          <label for="formPhone">Телефон</label>
          <input type="tel" id="formPhone" class="form-input" placeholder="+7 (___) ___-__-__" required>
        </div>
        <div class="form-group">
          <label for="formCompany">Компания / Отрасль</label>
          <input type="text" id="formCompany" class="form-input" placeholder="ООО Название">
        </div>
        <button type="submit" class="btn btn-primary form-submit">Отправить заявку</button>
        <div class="toast-success" id="toastSuccess"></div>
      </form>
    </div>
  </div>
  <script src="../js/app.js"></script>
</body>
</html>'''

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return f"blog/{slug}.html"

def save_article(title, badge, read_time, author, created_at, blocks):
    import re
    # generate slug
    slug = re.sub(r'[^a-zA-Z0-9]', '-', title.lower()).strip('-')
    if not slug or len(slug) < 3:
        slug = f"article-{int(datetime.now().timestamp())}"
    else:
        slug = f"{slug[:40]}-{int(datetime.now().timestamp()) % 10000}"

    url = generate_article_html(title, badge, read_time, author, created_at, blocks, slug)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO articles (created_at, title, badge, read_time, author, slug, content_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (created_at, title, badge, read_time, author, slug, json.dumps(blocks, ensure_ascii=False)))
    conn.commit()
    conn.close()
    return slug, url

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def do_POST(self):
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/api/leads":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body)
            except Exception:
                data = parse_qs(body)
                data = {k: v[0] for k, v in data.items()}

            name = data.get("name", "").strip()
            phone = data.get("phone", "").strip()
            company = data.get("company", "").strip()
            source = data.get("source", "Модальное окно")

            if not name or not phone:
                self._send_json({"success": False, "error": "Пожалуйста, заполните имя и телефон."}, status=400)
                return

            lead_id, created_at = save_lead(name, phone, company, source)
            send_email_notification(name, phone, company, created_at, source)

            self._send_json({"success": True, "message": "Заявка успешно отправлена! Эксперт свяжется с вами.", "id": lead_id})
            return

        elif parsed_url.path == "/api/admin/login":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
            except Exception:
                data = {}
            password = data.get("password", "")

            config = get_config()
            if password == config.get("admin_password", "admin"):
                self._send_json({"success": True, "token": "admin-session-token-2026"})
            else:
                self._send_json({"success": False, "error": "Неверный пароль администратора."})
            return

        elif parsed_url.path == "/api/articles":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            title = data.get("title", "").strip()
            badge = data.get("badge", "СТАТЬЯ").strip()
            read_time = data.get("read_time", "5 МИН ЧТЕНИЯ").strip()
            author = data.get("author", "ГЛАВНЫЙ ИНЖЕНЕР").strip()
            created_at = data.get("created_at") or datetime.now().strftime("%d АВГУСТА %Y").upper()
            blocks = data.get("blocks", [])

            if not title:
                self._send_json({"success": False, "error": "Заполните название статьи."}, status=400)
                return

            slug, url = save_article(title, badge, read_time, author, created_at, blocks)
            self._send_json({"success": True, "slug": slug, "url": url, "message": "Статья успешно создана!"})
            return

        elif parsed_url.path == "/api/articles/update":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            article_id = data.get("id")
            title = data.get("title", "").strip()
            badge = data.get("badge", "СТАТЬЯ").strip()
            read_time = data.get("read_time", "5 МИН ЧТЕНИЯ").strip()
            author = data.get("author", "ГЛАВНЫЙ ИНЖЕНЕР").strip()
            created_at = data.get("created_at") or datetime.now().strftime("%d АВГУСТА %Y").upper()
            blocks = data.get("blocks", [])

            if not article_id or not title:
                self._send_json({"success": False, "error": "Заполните данные для обновления."}, status=400)
                return

            slug = update_article(article_id, title, badge, read_time, author, created_at, blocks)
            if slug:
                self._send_json({"success": True, "slug": slug, "message": "Статья успешно обновлена!"})
            else:
                self._send_json({"success": False, "error": "Статья не найдена."}, status=44)
            return

        elif parsed_url.path == "/api/articles/delete":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            article_id = data.get("id")
            if article_id:
                delete_article(article_id)
                self._send_json({"success": True, "message": "Статья успешно удалена!"})
            else:
                self._send_json({"success": False, "error": "Не указан ID статьи."}, status=400)
            return

        self._send_json({"success": False, "error": "Not Found"}, status=404)

    def do_GET(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/api/leads":
            # Admin Leads API
            leads = get_all_leads()
            self._send_json({"success": True, "leads": leads})
            return

        elif parsed_url.path == "/api/articles":
            # Articles API
            articles = get_all_articles()
            self._send_json({"success": True, "articles": articles})
            return

        elif parsed_url.path == "/api/leads/export":
            # Export Leads to CSV (Excel readable)
            leads = get_all_leads()
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8-sig')
            self.send_header('Content-Disposition', 'attachment; filename="leads_profexpert.csv"')
            self.end_headers()

            writer = csv.writer(self.wfile)
            self.wfile.write('\ufeff'.encode('utf-8'))
            writer.writerow(["ID", "Дата и время", "Имя клиента", "Телефон", "Компания", "Источник", "Статус"])
            for l in leads:
                writer.writerow([l["id"], l["created_at"], l["name"], l["phone"], l["company"], l["source"], l["status"]])
            return

        super().do_GET()

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

if __name__ == "__main__":
    init_db()
    print(f"==================================================")
    print(f"ООО «ПрофЭксперт» Backend Server Started on Port {PORT}")
    print(f"Serving Static Site + API Endpoints:")
    print(f"  - http://localhost:{PORT}/")
    print(f"  - http://localhost:{PORT}/admin/")
    print(f"==================================================")
    httpd = HTTPServer(('0.0.0.0', PORT), CustomHandler)
    httpd.serve_forever()
