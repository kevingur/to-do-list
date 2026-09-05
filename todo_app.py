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
    return sb.table("todos").select("*").order("created_at").execute().data


def log(action: str, todo_id: str | None, todo_name: str) -> None:
    sb.table("todo_log").insert(
        {"action": action, "todo_id": todo_id, "todo_name": todo_name}
    ).execute()


# ---------- actions ----------
def add_todo(who: str, job: str, due: date) -> None:
    row = (
        sb.table("todos")
        .insert({"name": who.strip(), "description": job.strip(), "due": due.isoformat()})
        .execute()
        .data[0]
    )
    log("added", row["id"], f"{row['name']} — {row['description']}")


def set_done(todo_id: str, label: str, done: bool) -> None:
    sb.table("todos").update(
        {"done": done, "completed_at": now_iso() if done else None}
    ).eq("id", todo_id).execute()
    log("completed" if done else "reopened", todo_id, label)


def delete_todo(todo_id: str, label: str) -> None:
    sb.table("todos").delete().eq("id", todo_id).execute()
    log("deleted", todo_id, label)


# ---------- page & styling ----------
st.set_page_config(page_title="To-do", page_icon="✓", layout="centered")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600&display=swap');

.stApp, .stApp p, .stApp label, .stApp input, .stApp textarea,
.stApp button p, .stApp button div, .stApp .stMarkdown,
.stApp summary span:not([data-testid="stIconMaterial"]) {
    font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
span[data-testid="stIconMaterial"], .material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
}

header[data-testid="stHeader"], #MainMenu, footer { display: none; }
.block-container { max-width: 760px; padding-top: 2.4rem; padding-bottom: 5rem; }

.hdr { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 1.4rem; }
.hdr .day  { font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1; }
.hdr .date { font-size: 0.95rem; color: #8A8A8E; }

/* column headings */
.col-h { font-size: 0.78rem; font-weight: 600; color: #8A8A8E; letter-spacing: 0.02em;
         padding-bottom: 0.35rem; border-bottom: 1px solid #DEDEDA; margin-bottom: 0.2rem; }

/* cells */
.cell { font-size: 0.95rem; line-height: 1.35; padding-top: 0.35rem; margin: 0;
        overflow-wrap: anywhere; }
.cell.muted { color: #8A8A8E; }
.cell.done { color: #B0B0B3; text-decoration: line-through; }
.cell.overdue { color: #B24A3A; }
.cell.today { color: #2F4F6F; font-weight: 600; }

/* yes / no pills */
.pills { display: flex; gap: 6px; padding-top: 0.3rem; }
.pill { display: inline-block; min-width: 34px; text-align: center; padding: 2px 9px;
        border-radius: 6px; font-size: 0.8rem; font-weight: 600;
        border: 1px solid #E2E2DE; color: #C0C0C3; background: transparent; }
.pill.yes-on { background: #EAF3DE; color: #27500A; border-color: #97C459; }
.pill.no-on  { background: #FCEBEB; color: #791F1F; border-color: #F09595; }

/* row divider */
hr { margin: 0.45rem 0 !important; border-color: #EDEDEA !important; }

/* buttons */
div[data-testid="stButton"] button { min-height: 2rem !important; padding: 0.15rem 0.7rem !important;
                                    font-size: 0.82rem !important; border-radius: 6px; }
div[data-testid="stButton"] button[kind="tertiary"] {
    color: #9A9A9E !important; padding: 0 !important; font-size: 1.1rem !important;
    min-width: 0 !important; width: 100%; border: none !important; }
div[data-testid="stButton"] button[kind="tertiary"]:hover {
    color: #B24A3A !important; background: transparent !important; }

/* add row */
.add-h { font-size: 0.78rem; font-weight: 600; color: #8A8A8E; letter-spacing: 0.02em;
         margin: 0 0 0.3rem 0; }
div[data-testid="stTextInput"] input, div[data-testid="stDateInput"] input {
    border-radius: 6px; border-color: #E0E0DC; }
.empty { color: #A0A0A3; font-size: 0.95rem; padding: 1.2rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

today = date.today()
st.markdown(
    f"<div class='hdr'><span class='day'>{today.strftime('%A')}</span>"
    f"<span class='date'>{today.day} {today.strftime('%B %Y')}</span></div>",
    unsafe_allow_html=True,
)

# ---------- add row ----------
st.markdown("<div class='add-h'>New task</div>", unsafe_allow_html=True)
with st.form("new_task", clear_on_submit=True, border=False):
    a_who, a_job, a_due, a_btn = st.columns([1.7, 3.4, 1.7, 1.0], vertical_alignment="bottom")
    who = a_who.text_input("Who", placeholder="Who", label_visibility="collapsed")
    job = a_job.text_input("Job", placeholder="Job", label_visibility="collapsed")
    due = a_due.date_input("Due", value=today, format="DD.MM.YYYY",
                           label_visibility="collapsed")
    if a_btn.form_submit_button("Add", type="primary", use_container_width=True):
        if who.strip() or job.strip():
            add_todo(who or "—", job, due)
            st.rerun()
        else:
            st.warning("Enter a name or a job first.")

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

# ---------- load ----------
try:
    todos = fetch_todos()
except Exception as e:
    st.error(f"Could not reach the database: {e}")
    st.stop()

open_tasks = [t for t in todos if not t["done"]]
done_tasks = [t for t in todos if t["done"]]

# ---------- table ----------
WIDTHS = [1.7, 3.3, 1.4, 0.95, 1.35, 0.6]


def header_row() -> None:
    cols = st.columns(WIDTHS, vertical_alignment="bottom")
    for col, label in zip(cols, ["Who", "Job", "Due", "Done", "Status", ""]):
        col.markdown(f"<div class='col-h'>{label}</div>", unsafe_allow_html=True)


def render(todo: dict) -> None:
    due = date.fromisoformat(todo["due"])
    done = todo["done"]
    label = f"{todo['name']} — {todo['description']}"
    c_who, c_job, c_due, c_btn, c_status, c_del = st.columns(WIDTHS, vertical_alignment="top")

    cls = "done" if done else ""
    c_who.markdown(f"<p class='cell {cls}'>{todo['name']}</p>", unsafe_allow_html=True)
    c_job.markdown(
        f"<p class='cell {cls or 'muted'}'>{todo['description'] or '—'}</p>",
        unsafe_allow_html=True,
    )

    if done:
        due_cls = "done"
    elif due < today:
        due_cls = "overdue"
    elif due == today:
        due_cls = "today"
    else:
        due_cls = "muted"
    due_txt = "Today" if (due == today and not done) else due.strftime("%d.%m.%Y")
    c_due.markdown(f"<p class='cell {due_cls}'>{due_txt}</p>", unsafe_allow_html=True)

    if c_btn.button("Undo" if done else "Done", key=f"done_{todo['id']}",
                    use_container_width=True):
        set_done(todo["id"], label, not done)
        st.rerun()

    c_status.markdown(
        f"<div class='pills'><span class='pill {'yes-on' if done else ''}'>Yes</span>"
        f"<span class='pill {'' if done else 'no-on'}'>No</span></div>",
        unsafe_allow_html=True,
    )

    if c_del.button("✕", key=f"del_{todo['id']}", type="tertiary", help="Delete"):
        delete_todo(todo["id"], label)
        st.rerun()

    st.divider()


header_row()
if not todos:
    st.markdown("<div class='empty'>Nothing here yet. Add a task above.</div>",
                unsafe_allow_html=True)
for t in open_tasks + done_tasks:
    render(t)
