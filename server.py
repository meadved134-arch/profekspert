import os
import json
import sqlite3
import smtplib
import csv
import sys
import re
import threading
import io
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.request
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

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def seed_default_articles(cursor):
    default_articles = [
        (
            "25 АВГУСТА 2026",
            "Изменения в законодательстве по охране труда в 2026 году",
            "СОУТ и ЛНА",
            "7 МИН ЧТЕНИЯ",
            "Главный инженер ООО «ПрофЭксперт»",
            "article-template",
            json.dumps([
                {"type": "h2", "value": "1. Главные законодательные акценты 2026 года"},
                {"type": "p", "value": "В 2026 году вступил в силу обновленный комплекс требований Роструда и Минтруда РФ, касающийся порядка проведения СОУТ, учета микротравм и автоматизации ЛНА."},
                {"type": "quote", "value": "Главный приоритет 2026 года — переориентация от формального ведения журналов к реальной оценке рисков на каждом рабочем месте.", "author": "Эксперт по аутсорсингу охраны труда"}
            ], ensure_ascii=False)
        ),
        (
            "24 АВГУСТА 2026",
            "Подготовка к проверкам ГИТ и Роструда: пошаговый чек-лист",
            "Проверки ГИТ",
            "6 МИН ЧТЕНИЯ",
            "Ведущий аудитор ООО «ПрофЭксперт»",
            "podgotovka-k-proverkam",
            json.dumps([
                {"type": "h2", "value": "1. С чего начать подготовку к инспекции"},
                {"type": "p", "value": "Плановые и внеплановые проверки Государственной инспекции труда (ГИТ) требуют тщательной сверки наличия и корректности заполнения кадровых и охранотрудовых документов."},
                {"type": "quote", "value": "Качественно подготовленный комплект документов предотвращает штрафы до 200 000 рублей.", "author": "Ведущий аудитор"}
            ], ensure_ascii=False)
        ),
        (
            "23 АВГУСТА 2026",
            "Производственная безопасность на предприятии: как исключить травматизм",
            "Безопасность",
            "8 МИН ЧТЕНИЯ",
            "Специалист по техбезопасности",
            "proizvodstvennaya-bezopasnost",
            json.dumps([
                {"type": "h2", "value": "1. Системный подход к нулевому травматизму"},
                {"type": "p", "value": "Внедрение международных и национальных стандартов Vision Zero позволяет сократить производственный травматизм на 95%."},
                {"type": "quote", "value": "Безопасность труда — это экономия бюджета предприятия и защита персонала.", "author": "Специалист по техбезопасности"}
            ], ensure_ascii=False)
        )
    ]
    for a in default_articles:
        cursor.execute('''
            INSERT OR IGNORE INTO articles (created_at, title, badge, read_time, author, slug, content_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', a)

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
    seed_default_articles(cursor)
    conn.commit()
    conn.close()

def save_lead(name, phone, company, source="Сайт"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
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
        body = f"""Новая заявка с сайта ООО «ПрофЭксперт»
-----------------------------------------
Имя клиента: {name}
Телефон: {phone}
Компания / Отрасль: {company if company else 'Не указано'}
Дата и время: {created_at}
Источник: {source}
-----------------------------------------
Заявка также сохранена в панели управления: http://localhost:8085/admin/
"""
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(f"🔥 Новая заявка: {name} ({phone}) — ООО «ПрофЭксперт»", 'utf-8')
        recipients = [r.strip() for r in str(config.get("recipient_email", "")).split(',') if r.strip()]
        msg['To'] = ", ".join(recipients)

        smtp_server = config.get("smtp_server", "smtp.yandex.ru")
        smtp_port = config.get("smtp_port", 465)

        try:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=8)
            server.login(config["smtp_user"], config["smtp_password"])
            server.sendmail(config["smtp_user"], recipients, msg.as_string())
            server.quit()
            print(f"[SMTP SUCCESS] Notification email sent to {config['recipient_email']}")
            return
        except Exception as e1:
            # Fallback to port 587 STARTTLS
            try:
                server = smtplib.SMTP(smtp_server, 587, timeout=8)
                server.starttls()
                server.login(config["smtp_user"], config["smtp_password"])
                server.sendmail(config["smtp_user"], recipients, msg.as_string())
                server.quit()
                print(f"[SMTP SUCCESS via 587] Notification email sent to {config['recipient_email']}")
            except Exception as e2:
                print(f"[SMTP ERROR] Failed to send email via 465 ({e1}) and 587 ({e2})")
    except Exception as e:
        print(f"[SMTP ERROR] Failed to prepare email: {e}")

def send_telegram_notification(name, phone, company, created_at, source):
    config = get_config()
    if not config.get("telegram_enabled"):
        return
    token = config.get("telegram_bot_token", "").strip()
    raw_chat_ids = config.get("telegram_chat_id", "")
    if not token or not raw_chat_ids:
        return

    # Support single ID, comma-separated string, or list
    if isinstance(raw_chat_ids, list):
        chat_ids = [str(cid).strip() for cid in raw_chat_ids if str(cid).strip()]
    else:
        chat_ids = [cid.strip() for cid in str(raw_chat_ids).split(',') if cid.strip()]

    text = f"""🔥 *НОВАЯ ЗАЯВКА С САЙТА*
━━━━━━━━━━━━━━━━━━━━
👤 *Имя клиента:* {name}
📞 *Телефон:* `{phone}`
🏢 *Компания:* {company if company else 'Не указано'}
📅 *Дата и время:* {created_at}
📍 *Источник:* {source}
━━━━━━━━━━━━━━━━━━━━
💾 Заявка сохранена в базе данных"""

    for chat_id in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = json.dumps({
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }).encode('utf-8')
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as res:
                res_data = json.loads(res.read().decode('utf-8'))
                if res_data.get("ok"):
                    print(f"[TG SUCCESS] Telegram notification sent to chat_id {chat_id}")
                else:
                    print(f"[TG ERROR] Telegram response error for {chat_id}: {res_data}")
        except Exception as e:
            print(f"[TG ERROR] Failed to send telegram notification to {chat_id}: {e}")

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

CYRILLIC_TO_LATIN = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i','й':'y',
    'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f',
    'х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'
}

def make_slug(title):
    res = ""
    for ch in title.lower():
        if ch in CYRILLIC_TO_LATIN:
            res += CYRILLIC_TO_LATIN[ch]
        elif ch.isalnum() and ch.isascii():
            res += ch
        else:
            res += '-'
    res = re.sub(r'-+', '-', res).strip('-')
    if not res:
        res = "article"
    return f"{res[:40]}-{int(datetime.now().timestamp()) % 10000}"

def save_article(title, badge, read_time, author, created_at, blocks):
    slug = make_slug(title)
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

def update_article(article_id, title, badge, read_time, author, created_at, blocks):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT slug FROM articles WHERE id = ?', (article_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    slug = row[0]
    generate_article_html(title, badge, read_time, author, created_at, blocks, slug)
    cursor.execute('''
        UPDATE articles SET title=?, badge=?, read_time=?, author=?, created_at=?, content_json=?
        WHERE id=?
    ''', (title, badge, read_time, author, created_at, json.dumps(blocks, ensure_ascii=False), article_id))
    conn.commit()
    conn.close()
    return slug

def delete_article(article_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT slug FROM articles WHERE id = ?', (article_id,))
    row = cursor.fetchone()
    if row:
        slug = row[0]
        # Delete the HTML file from blog/
        html_path = os.path.join(os.path.dirname(__file__), 'blog', f'{slug}.html')
        if os.path.exists(html_path):
            os.remove(html_path)
        cursor.execute('DELETE FROM articles WHERE id = ?', (article_id,))
        conn.commit()
    conn.close()


class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def end_headers(self):
        # Disable browser caching for JS and CSS so changes apply immediately
        path = urlparse(self.path).path
        if path.endswith('.js') or path.endswith('.css') or path.endswith('.html'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()

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
            threading.Thread(target=send_email_notification, args=(name, phone, company, created_at, source), daemon=True).start()
            threading.Thread(target=send_telegram_notification, args=(name, phone, company, created_at, source), daemon=True).start()

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

        elif parsed_url.path == "/api/admin/settings":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            cfg = get_config()
            for key in ["admin_password", "email_enabled", "smtp_server", "smtp_port", "smtp_user", "smtp_password", "recipient_email", "telegram_enabled", "telegram_bot_token", "telegram_chat_id"]:
                if key in data:
                    cfg[key] = data[key]
            save_config(cfg)
            self._send_json({"success": True, "message": "Настройки успешно сохранены!"})
            return

        elif parsed_url.path == "/api/admin/test_notification":
            test_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            threading.Thread(target=send_email_notification, args=("Тестовый клиент", "+7 (999) 000-00-00", "ООО «Тест»", test_time, "Тест из панели управления"), daemon=True).start()
            threading.Thread(target=send_telegram_notification, args=("Тестовый клиент", "+7 (999) 000-00-00", "ООО «Тест»", test_time, "Тест из панели управления"), daemon=True).start()
            self._send_json({"success": True, "message": "Тестовые уведомления отправлены в Telegram и на Email!"})
            return

        self._send_json({"success": False, "error": "Not Found"}, status=404)

    def do_GET(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/api/leads":
            # Admin Leads API
            leads = get_all_leads()
            self._send_json({"success": True, "leads": leads})
            return

        elif parsed_url.path == "/api/admin/settings":
            cfg = get_config()
            self._send_json({"success": True, "config": cfg})
            return

        elif parsed_url.path == "/api/articles":
            # Articles API
            articles = get_all_articles()
            self._send_json({"success": True, "articles": articles})
            return

        elif parsed_url.path == "/api/leads/export":
            # Export Leads to CSV (Excel readable with semicolon separator)
            leads = get_all_leads()
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8-sig')
            self.send_header('Content-Disposition', 'attachment; filename="leads_profexpert.csv"')
            self.end_headers()

            string_buffer = io.StringIO()
            writer = csv.writer(string_buffer, delimiter=';')
            writer.writerow(["ID", "Дата и время", "Имя клиента", "Телефон", "Компания", "Источник", "Статус"])
            for l in leads:
                raw_date = l.get("created_at") or ""
                try:
                    if "-" in raw_date and len(raw_date) >= 19:
                        dt = datetime.strptime(raw_date[:19], "%Y-%m-%d %H:%M:%S")
                        formatted_date = dt.strftime("%d.%m.%Y %H:%M:%S")
                    else:
                        formatted_date = raw_date
                except Exception:
                    formatted_date = raw_date
                writer.writerow([l["id"], formatted_date, l["name"], l["phone"], l["company"], l["source"], l["status"]])

            csv_bytes = string_buffer.getvalue().encode('utf-8-sig')
            self.wfile.write(csv_bytes)
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
