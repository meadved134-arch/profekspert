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

        self._send_json({"success": False, "error": "Not Found"}, status=404)

    def do_GET(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/api/leads":
            # Admin Leads API
            leads = get_all_leads()
            self._send_json({"success": True, "leads": leads})
            return

        elif parsed_url.path == "/api/leads/export":
            # Export Leads to CSV (Excel readable)
            leads = get_all_leads()
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8-sig')
            self.send_header('Content-Disposition', 'attachment; filename="leads_profexpert.csv"')
            self.end_headers()

            writer = csv.writer(self.wfile)
            # Write BOM for Excel UTF-8 recognition
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
