"""
Daily push notification (ntfy) for today's and overdue tasks.

Runs on a schedule via GitHub Actions (.github/workflows/notify.yml).
Needs env vars: SUPABASE_URL, SUPABASE_KEY, NTFY_TOPIC (optional: NTFY_SERVER).
"""

import os
from datetime import date, datetime, timedelta, timezone

import requests
from supabase import create_client

TZ = timezone(timedelta(hours=3))  # Türkiye
today = datetime.now(TZ).date()

sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
rows = (
    sb.table("todos").select("name, description, due")
    .eq("done", False).lte("due", today.isoformat())
    .order("due").order("created_at").execute().data
)

due_today = [r for r in rows if date.fromisoformat(r["due"]) == today]
overdue = [r for r in rows if date.fromisoformat(r["due"]) < today]

SEND_WHEN_EMPTY = False  # True -> "Nothing today" mesajı da gelsin

if not due_today and not overdue and not SEND_WHEN_EMPTY:
    print("nothing to send")
    raise SystemExit(0)


def line(r: dict) -> str:
    who = r["name"] or "—"
    job = r["description"] or "—"
    return f"• {who} — {job}"


parts = []
if due_today:
    parts.append("\n".join(line(r) for r in due_today))
if overdue:
    parts.append("Overdue:\n" + "\n".join(
        f"{line(r)} ({date.fromisoformat(r['due']).strftime('%d.%m')})" for r in overdue))
body = "\n\n".join(parts) if parts else "Nothing today."

n_today, n_over = len(due_today), len(overdue)
title = f"{today.strftime('%a %d %b')} · {n_today} today" + (f", {n_over} overdue" if n_over else "")

server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
resp = requests.post(
    f"{server}/{os.environ['NTFY_TOPIC']}",
    data=body.encode("utf-8"),
    headers={
        "Title": title.encode("utf-8"),
        "Priority": "high" if n_over else "default",
        "Tags": "clipboard",
    },
    timeout=15,
)
resp.raise_for_status()
print("sent:", title)
