import json
import os
import re
import sqlite3
import smtplib
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "leads.db"


def init_db() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quote_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                service TEXT NOT NULL,
                location TEXT NOT NULL,
                timeline TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def validate_payload(data: dict) -> dict:
    required_fields = [
        "name", "phone", "email", "service", "location", "timeline", "details"
    ]
    cleaned = {}

    for field in required_fields:
        value = str(data.get(field, "")).strip()
        if not value:
            raise ValueError(f"{field.title()} is required.")
        cleaned[field] = value

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", cleaned["email"]):
        raise ValueError("Please enter a valid email address.")

    digits = re.sub(r"\D", "", cleaned["phone"])
    if len(digits) < 10:
        raise ValueError("Please enter a valid phone number.")

    return cleaned


def save_quote(data: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO quote_requests (name, phone, email, service, location, timeline, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data["phone"],
                data["email"],
                data["service"],
                data["location"],
                data["timeline"],
                data["details"],
            ),
        )
        conn.commit()


def send_email_notification(data: dict) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    notification_to = os.getenv("NOTIFICATION_TO")

    if not all([smtp_host, smtp_port, smtp_user, smtp_password, notification_to]):
        return False

    message = EmailMessage()
    message["Subject"] = f"New Hampden Haul Quote Request — {data['service']}"
    message["From"] = smtp_user
    message["To"] = notification_to
    message["Reply-To"] = data["email"]
    message.set_content(
        f"""
New quote request received

Name: {data['name']}
Phone: {data['phone']}
Email: {data['email']}
Service: {data['service']}
Location: {data['location']}
Timeline: {data['timeline']}

Details:
{data['details']}
""".strip()
    )

    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    with smtplib.SMTP(smtp_host, int(smtp_port), timeout=20) as server:
        if use_tls:
            server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    return True


class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ["/", "/index.html"]:
            self._send_html(TEMPLATE_PATH.read_text(encoding="utf-8"))
        elif path == "/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/quote":
            self._send_json({"error": "Not found"}, status=404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(raw or "{}")
            cleaned = validate_payload(data)
            save_quote(cleaned)
            emailed = send_email_notification(cleaned)

            message = "Thanks. Your quote request was received."
            if emailed:
                message += " A notification email was also sent."

            self._send_json({"ok": True, "message": message}, status=201)
        except ValueError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "Invalid JSON payload."}, status=400)
        except Exception:
            self._send_json(
                {
                    "ok": False,
                    "error": "Unable to process your request right now. Please call or text instead.",
                },
                status=500,
            )

    def log_message(self, format, *args):
        return


def run() -> None:
    init_db()
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), RequestHandler)
    print(f"Server running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
