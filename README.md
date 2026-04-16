# Hampden Haul — Working Website

This package turns the landing page into a working site with a live backend.

## What is included
- Conversion-focused landing page
- Working quote form
- Backend endpoint at `/api/quote`
- Server-side validation
- SQLite lead storage (`leads.db`)
- Optional SMTP email notifications
- Mobile menu, sticky mobile CTA, clickable call/text/email links
- SEO improvements, pricing section, trust signals, reviews, service area, hours

## Local setup

No third-party Python packages are required.

Run:
```bash
python app.py
```

Then open:
```text
http://127.0.0.1:8000
```

## Optional email notification settings
Set these as environment variables before you start the server:

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=you@example.com
export SMTP_PASSWORD=your-app-password
export SMTP_USE_TLS=true
export NOTIFICATION_TO=hello@hampdenhaul.com
```

For Gmail, use an app password, not your normal login password.

## Deployment options
- Any VPS that can run Python 3
- Render / Railway / Fly.io via a simple Python service
- Replit or similar environments that let you expose a port

## Notes
- Quote requests are always stored in SQLite, even if email notifications are not configured.
- Replace placeholder reviews and contact details before launch.
- Replace the canonical URL with your real domain.
