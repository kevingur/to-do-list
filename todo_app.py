"""
To-do — Streamlit + Supabase

Local run:
    pip install -r requirements.txt
    streamlit run todo_app.py

Connection details live in .streamlit/secrets.toml (local) or
Streamlit Cloud > App settings > Secrets.
"""

from datetime import date, datetime, timezone

import streamlit as st
from supabase import Client, create_client

# ---------- connection ----------


@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


sb = get_client()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- data ----------
def fetch_todos() -> list[dict]:
    return sb.table("todos").select("*").order("due").execute().data


def log(action: str, todo_id: str | None, todo_name: str) -> None:
    sb.table("todo_log").insert(
        {"action": action, "todo_id": todo_id, "todo_name": todo_name}
    ).execute()


def fetch_log(limit: int = 50) -> list[dict]:
    return (
        sb.table("todo_log").select("*").order("ts", desc=True).limit(limit).execute().data
    )


# ---------- actions ----------
def add_todo(name: str, description: str, due: date) -> None:
    row = (
        sb.table("todos")
        .insert(
            {"name": name.strip(), "description": description.strip(), "due": due.isoformat()}
        )
        .execute()
        .data[0]
    )
    log("added", row["id"], row["name"])


def toggle_done(todo_id: str, todo_name: str) -> None:
    done = st.session_state[f"chk_{todo_id}"]
    sb.table("todos").update(
        {"done": done, "completed_at": now_iso() if done else None}
    ).eq("id", todo_id).execute()
    log("completed" if done else "reopened", todo_id, todo_name)


def delete_todo(todo_id: str, todo_name: str) -> None:
    sb.table("todos").delete().eq("id", todo_id).execute()
    log("deleted", todo_id, todo_name)


# ---------- page & styling ----------
st.set_page_config(page_title="To-do", page_icon="✓", layout="centered")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap');

.stApp, .stApp p, .stApp label, .stApp input, .stApp textarea,
.stApp button p, .stApp button div, .stApp .stMarkdown,
.stApp summary span:not([data-testid="stIconMaterial"]) {
    font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
/* keep Streamlit's icon font intact (expander arrows, popover chevron, etc.) */
span[data-testid="stIconMaterial"], .material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
}

header[data-testid="stHeader"], #MainMenu, footer { display: none; }
.block-container { max-width: 620px; padding-top: 2.4rem; padding-bottom: 5rem; }

/* header */
.hdr { display: flex; align-items: baseline; justify-content: space-between;
       margin-bottom: 0.4rem; }
.hdr .day  { font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1; }
.hdr .date { font-size: 0.95rem; color: #8A8A8E; }

/* section labels */
.sec { font-size: 0.8rem; font-weight: 600; color: #8A8A8E; letter-spacing: 0.02em;
       margin: 1.6rem 0 0.3rem 0; padding-bottom: 0.35rem; border-bottom: 1px solid #E5E5E1; }
.sec.overdue { color: #B24A3A; }

/* task rows */
.task-name { font-size: 1rem; font-weight: 500; line-height: 1.35; margin: 0; }
.task-name.done { color: #A0A0A3; text-decoration: line-through; font-weight: 400; }
.task-desc { font-size: 0.86rem; color: #7A7A7E; margin: 0.1rem 0 0 0; line-height: 1.4; }
.task-date { font-size: 0.8rem; color: #8A8A8E; text-align: right; white-space: nowrap;
             padding-top: 0.25rem; }
.task-date.overdue { color: #B24A3A; }
.task-date.today   { color: #2F4F6F; font-weight: 600; }
hr { margin: 0.55rem 0 !important; border-color: #EDEDEA !important; }

/* checkbox: tidy vertical alignment */
div[data-testid="stCheckbox"] { padding-top: 0.15rem; }
div[data-testid="stCheckbox"] label { min-height: 0; }

/* delete button: quiet until hovered */
button[kind="tertiary"] { color: #C4C4C6 !important; padding: 0 0.3rem !important;
                          min-height: 0 !important; }
button[kind="tertiary"]:hover { color: #B24A3A !important; background: transparent !important; }

/* inputs */
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea,
div[data-testid="stDateInput"] input {
    border-radius: 6px; border-color: #E0E0DC;
}
.empty { color: #A0A0A3; font-size: 0.95rem; padding: 1.2rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

today = date.today()

# ---------- header + new task ----------
col_h, col_add = st.columns([5, 1.6], vertical_alignment="bottom")
col_h.markdown(
    f"<div class='hdr'><span class='day'>{today.strftime('%A')}</span>"
    f"<span class='date'>{today.day} {today.strftime('%B %Y')}</span></div>",
    unsafe_allow_html=True,
)
with col_add.popover("New task", use_container_width=True):
    with st.form("new_task", clear_on_submit=True, border=False):
        name = st.text_input("Task", placeholder="What needs doing?")
        description = st.text_area("Notes", placeholder="Optional", height=70)
        due = st.date_input("Due", value=today, format="DD.MM.YYYY")
        if st.form_submit_button("Add task", type="primary", use_container_width=True):
            if name.strip():
                add_todo(name, description, due)
                st.rerun()
            else:
                st.warning("Give the task a name.")

# ---------- load ----------
try:
    todos = fetch_todos()
except Exception as e:
    st.error(f"Could not reach the database: {e}")
    st.stop()

open_tasks = [t for t in todos if not t["done"]]
overdue = [t for t in open_tasks if date.fromisoformat(t["due"]) < today]
due_today = [t for t in open_tasks if date.fromisoformat(t["due"]) == today]
upcoming = [t for t in open_tasks if date.fromisoformat(t["due"]) > today]
done_tasks = sorted(
    (t for t in todos if t["done"]), key=lambda t: t["completed_at"] or "", reverse=True
)


def fmt_date(d: date) -> str:
    return f"{d:%a} {d.day} {d:%b}" if d.year == today.year else f"{d.day} {d:%b %Y}"


def render(todo: dict) -> None:
    due = date.fromisoformat(todo["due"])
    is_overdue = not todo["done"] and due < today
    is_today = not todo["done"] and due == today

    c_chk, c_body, c_date, c_del = st.columns([0.5, 6, 1.9, 0.5], vertical_alignment="top")
    c_chk.checkbox(
        "done",
        value=todo["done"],
        key=f"chk_{todo['id']}",
        on_change=toggle_done,
        args=(todo["id"], todo["name"]),
        label_visibility="collapsed",
    )
    desc = f"<p class='task-desc'>{todo['description']}</p>" if todo["description"] else ""
    c_body.markdown(
        f"<p class='task-name{' done' if todo['done'] else ''}'>{todo['name']}</p>{desc}",
        unsafe_allow_html=True,
    )
    date_cls = "overdue" if is_overdue else "today" if is_today else ""
    date_txt = "Today" if is_today else fmt_date(due)
    c_date.markdown(f"<div class='task-date {date_cls}'>{date_txt}</div>", unsafe_allow_html=True)
    c_del.button(
        "×",
        key=f"del_{todo['id']}",
        on_click=delete_todo,
        args=(todo["id"], todo["name"]),
        type="tertiary",
        help="Delete",
    )
    st.divider()


def section(label: str, tasks: list[dict], cls: str = "") -> None:
    if not tasks:
        return
    st.markdown(f"<div class='sec {cls}'>{label}</div>", unsafe_allow_html=True)
    for t in tasks:
        render(t)


if not open_tasks:
    st.markdown("<div class='empty'>Nothing to do. Add a task to get started.</div>",
                unsafe_allow_html=True)

section("Overdue", overdue, "overdue")
section("Today", due_today)
section("Upcoming", upcoming)

if done_tasks:
    with st.expander(f"Completed · {len(done_tasks)}"):
        for t in done_tasks:
            render(t)

with st.expander("Activity"):
    rows = fetch_log()
    if rows:
        lines = [
            f"{datetime.fromisoformat(r['ts']).astimezone().strftime('%d %b %H:%M')}  "
            f"{r['action']:<10} {r['todo_name']}"
            for r in rows
        ]
        st.code("\n".join(lines), language=None)
    else:
        st.caption("No activity yet")
