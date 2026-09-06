"""
To-do — Streamlit + Supabase

Local run:
    pip install -r requirements.txt
    streamlit run todo_app.py

Connection details live in .streamlit/secrets.toml (local) or
Streamlit Cloud > App settings > Secrets.
"""

import json
from datetime import date, datetime, timezone

import anthropic
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


def log(action: str, todo_id: str | None, detail: str) -> None:
    sb.table("todo_log").insert(
        {"action": action, "todo_id": todo_id, "todo_name": detail}
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


def save_text(todo_id: str, field: str, key: str) -> None:
    val = st.session_state[key].strip()
    sb.table("todos").update({field: val}).eq("id", todo_id).execute()
    log("edited", todo_id, f"{field}: {val}")


def save_due(todo_id: str, key: str) -> None:
    d = st.session_state[key]
    if d is None:
        return
    sb.table("todos").update({"due": d.isoformat()}).eq("id", todo_id).execute()
    log("edited", todo_id, f"due: {d.isoformat()}")


# ---------- quick add (AI parsing) ----------
PARSE_PROMPT = """You extract a to-do item from one short sentence written in Turkish or English.
Today is {today} ({weekday}).

Return ONLY a JSON object, no prose, no code fences:
{{"who": "...", "job": "...", "due": "YYYY-MM-DD"}}

Rules:
- "who": the person responsible. Give the bare name as it would appear in a list
  (strip Turkish case suffixes: "Ahmet'e" -> "Ahmet", "Ayşe'ye" -> "Ayşe").
  If nobody is named, use "".
- "job": the task, short, same language as the input, without the person's name
  and without the date words.
- "due": resolve relative dates ("yarın", "haftaya salı", "ay sonu", "next Friday",
  "in 3 days") to an absolute date. If no date is mentioned, use today.
"""


def parse_task(text: str) -> dict:
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=PARSE_PROMPT.format(today=date.today().isoformat(),
                                   weekday=date.today().strftime("%A")),
        messages=[{"role": "user", "content": text}],
    )
    raw = msg.content[0].text.strip()
    raw = raw[raw.find("{"): raw.rfind("}") + 1]
    data = json.loads(raw)
    try:
        due = date.fromisoformat(str(data.get("due", "")))
    except ValueError:
        due = date.today()
    return {"who": str(data.get("who", "")).strip(),
            "job": str(data.get("job", "")).strip(), "due": due}


def run_quick_add() -> None:
    text = st.session_state.get("quick_text", "").strip()
    if not text:
        return
    try:
        parsed = parse_task(text)
    except Exception as e:  # noqa: BLE001
        st.session_state["quick_error"] = f"Couldn't parse that: {e}"
        return
    st.session_state["nt_who"] = parsed["who"]
    st.session_state["nt_job"] = parsed["job"]
    st.session_state["nt_due"] = parsed["due"]
    st.session_state["quick_text"] = ""
    st.session_state.pop("quick_error", None)


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
.block-container { max-width: 780px; padding-top: 2.4rem; padding-bottom: 5rem; }

.hdr { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 1.4rem; }
.hdr .day  { font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1; }
.hdr .date { font-size: 0.95rem; color: #8A8A8E; }

.add-h, .col-h { font-size: 0.78rem; font-weight: 600; color: #8A8A8E; letter-spacing: 0.02em; }
.add-h { margin-bottom: 0.3rem; }
.col-h { padding-bottom: 0.35rem; border-bottom: 1px solid #DEDEDA; margin-bottom: 0.2rem; }

/* form inputs */
div[data-testid="stTextInput"] input, div[data-testid="stDateInput"] input {
    border-radius: 6px; }

/* editable rows: inputs look like plain text until hovered */
.st-key-rows div[data-baseweb="input"], .st-key-rows div[data-baseweb="base-input"] {
    background: transparent !important; border-color: transparent !important; }
.st-key-rows div[data-baseweb="input"]:hover,
.st-key-rows div[data-baseweb="input"]:focus-within {
    border-color: #E0E0DC !important; background: #FFFFFF !important; }
.st-key-rows input { padding-left: 0.4rem !important; font-size: 0.95rem !important; }
.st-key-rows div[data-testid="stTextInput"], .st-key-rows div[data-testid="stDateInput"] {
    margin-bottom: 0; }

/* row states */
[class*="st-key-row_done"] input,
[class*="st-key-row_done"] div[data-testid="stDateInput"] input,
[class*="st-key-row_done"] div[data-testid="stDateInput"] div[data-baseweb="base-input"],
[class*="st-key-row_done"] div[data-testid="stDateInput"] div[data-baseweb="input"] {
    color: #B0B0B3 !important; text-decoration: line-through !important; }
[class*="st-key-row_late"] div[data-testid="stDateInput"] input { color: #B24A3A !important; font-weight: 600; }
[class*="st-key-row_today"] div[data-testid="stDateInput"] input { color: #2F4F6F !important; font-weight: 600; }

/* grouped rows: pull each sub row up against the row above */
.st-key-rows [data-testid="stVerticalBlock"] { gap: 0.6rem !important; }
[class*="_sub_"] { margin-top: -0.55rem !important; }

/* status toggle */
[class*="st-key-stat_"] div[data-testid="stButton"] { width: 100%; }
[class*="st-key-stat_"] div[data-testid="stButton"] button {
    width: 100% !important; min-height: 2.6rem !important; font-weight: 600 !important;
    border-radius: 6px !important; font-size: 0.95rem !important; }
[class*="st-key-stat_yes"] button { background: #EAF3DE !important; color: #27500A !important;
    border: 1px solid #97C459 !important; }
[class*="st-key-stat_yes"] button:hover { background: #DDEECA !important; }
[class*="st-key-stat_no"] button { background: #FCEBEB !important; color: #791F1F !important;
    border: 1px solid #F09595 !important; }
[class*="st-key-stat_no"] button:hover { background: #F8DADA !important; }
[class*="st-key-stat_"] button p { color: inherit !important; }

/* delete */
div[data-testid="stButton"]:has(button[kind="tertiary"]) { width: 100%; }
div[data-testid="stButton"] button[kind="tertiary"] {
    color: #9A9A9E !important; padding: 0 !important; font-size: 1.05rem !important;
    min-width: 0 !important; width: 100% !important; border: none !important;
    min-height: 2.6rem !important; display: flex; justify-content: center; }
div[data-testid="stButton"] button[kind="tertiary"] p { text-align: center; width: 100%; }
div[data-testid="stButton"] button[kind="tertiary"]:hover {
    color: #B24A3A !important; background: transparent !important; }

hr { margin: 0.5rem 0 !important; border-color: #EDEDEA !important; }
[class*="st-key-del_"] div[data-testid="stPopover"] { width: 100%; }
[class*="st-key-del_"] button {
    width: 100% !important; min-height: 2.6rem !important; padding: 0 !important;
    border: none !important; background: transparent !important; box-shadow: none !important;
    color: #9A9A9E !important; font-size: 1.05rem !important; justify-content: center; }
[class*="st-key-del_"] button:hover, [class*="st-key-del_"] button:focus { color: #B24A3A !important; }
[class*="st-key-del_"] button p { color: inherit !important; }
[class*="st-key-del_"] button svg, [class*="st-key-del_"] button span[data-testid="stIconMaterial"],
[class*="st-key-del_"] button [data-testid*="Icon"] { display: none !important; }
div[data-testid="stPopoverBody"] { min-width: 150px !important; max-width: 170px; padding: 0.7rem 0.8rem !important;
    border-radius: 10px; }
.confirm { font-size: 0.9rem; font-weight: 600; margin: 0 0 0.5rem 0; text-align: center; }
.empty { color: #A0A0A3; font-size: 0.95rem; padding: 1.2rem 0; }

/* ---------- phone layout: keep the 5 columns side by side ---------- */
@media (max-width: 640px) {
    .block-container { padding: 1.2rem 0.8rem 4rem !important; }
    .hdr { margin-bottom: 1rem; }
    .hdr .day { font-size: 1.5rem; }
    .hdr .date { font-size: 0.8rem; }

    div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.3rem !important; }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        min-width: 0 !important; width: auto !important; }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(1) { flex: 0 0 21% !important; }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) { flex: 1 1 0 !important; }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(3) { flex: 0 0 26% !important; }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(4) { flex: 0 0 14% !important; }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(5) { flex: 0 0 7% !important; }

    div[data-baseweb="input"], div[data-baseweb="base-input"] { min-width: 0 !important; }
    input { font-size: 0.8rem !important; padding-left: 0.35rem !important; padding-right: 0.2rem !important; }
    div[data-testid="stDateInput"] input { letter-spacing: -0.02em; }
    .col-h, .add-h { font-size: 0.7rem; }
    [class*="st-key-stat_"] div[data-testid="stButton"] button { font-size: 0.8rem !important; padding: 0 !important; }
    div[data-testid="stFormSubmitButton"] button { padding: 0 !important; font-size: 0.8rem !important; min-height: 2.6rem !important; }
    [class*="st-key-del_"] button { font-size: 0.95rem !important; }
}
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

WIDTHS = [1.7, 3.6, 1.5, 1.1, 0.5]  # Who, Job, Due, Status/Add, delete

# ---------- load ----------
try:
    todos = fetch_todos()
except Exception as e:
    st.error(f"Could not reach the database: {e}")
    st.stop()

# ---------- quick add ----------
if "ANTHROPIC_API_KEY" in st.secrets:
    st.markdown("<div class='add-h'>Quick add</div>", unsafe_allow_html=True)
    q_txt, q_btn = st.columns([WIDTHS[0] + WIDTHS[1] + WIDTHS[2], WIDTHS[3] + WIDTHS[4]],
                              vertical_alignment="bottom")
    q_txt.text_input("Quick add", key="quick_text", label_visibility="collapsed",
                     placeholder="Say or type it: \"Ahmet yarın kirayı ödesin\"",
                     on_change=run_quick_add)
    q_btn.button("Fill in", key="quick_btn", on_click=run_quick_add, use_container_width=True)
    if st.session_state.get("quick_error"):
        st.caption(f":red[{st.session_state['quick_error']}]")
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

# ---------- add row ----------
st.session_state.setdefault("nt_who", "")
st.session_state.setdefault("nt_job", "")
st.session_state.setdefault("nt_due", today)
st.markdown("<div class='add-h'>New task</div>", unsafe_allow_html=True)
with st.form("new_task", clear_on_submit=True, border=False):
    a_who, a_job, a_due, a_btn, _ = st.columns(WIDTHS, vertical_alignment="bottom")
    who = a_who.text_input("Who", key="nt_who", placeholder="Who", label_visibility="collapsed")
    job = a_job.text_input("Job", key="nt_job", placeholder="Job", label_visibility="collapsed")
    due = a_due.date_input("Due", key="nt_due", format="DD.MM.YYYY",
                           label_visibility="collapsed")
    if a_btn.form_submit_button("Add", type="primary", use_container_width=True):
        if who.strip() or job.strip():
            add_todo(who, job, due)
            st.rerun()
        else:
            st.warning("Enter a name or a job first.")

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

def group_rows(tasks: list[dict]) -> list[tuple[dict, bool]]:
    """Insertion order, but a task whose Who matches an earlier task
    is placed right after that group. Second value = True when the name
    should be hidden (it repeats the row above)."""
    ordered: list[tuple[dict, bool]] = []
    for t in tasks:
        key = t["name"].strip().casefold()
        pos = None
        if key:
            for i in range(len(ordered) - 1, -1, -1):
                if ordered[i][0]["name"].strip().casefold() == key:
                    pos = i
                    break
        if pos is None:
            ordered.append((t, False))
        else:
            ordered.insert(pos + 1, (t, True))
    return ordered


rows = group_rows(todos)

# ---------- table ----------
def header_row() -> None:
    cols = st.columns(WIDTHS, vertical_alignment="bottom")
    for col, label in zip(cols, ["Who", "Job", "Due", "Status", "&nbsp;"]):
        col.markdown(f"<div class='col-h'>{label}</div>", unsafe_allow_html=True)


def render(todo: dict, hide_name: bool = False, divider: bool = True) -> None:
    tid = todo["id"]
    due = date.fromisoformat(todo["due"])
    done = todo["done"]
    label = f"{todo['name']} — {todo['description']}"

    state = "done" if done else "late" if due < today else "today" if due == today else "open"
    with st.container(key=f"row_{state}_{'sub' if hide_name else 'top'}_{tid}"):
        c_who, c_job, c_due, c_stat, c_del = st.columns(WIDTHS, vertical_alignment="center")

        if hide_name:
            c_who.empty()
        else:
            c_who.text_input("Who", value=todo["name"], key=f"who_{tid}",
                             label_visibility="collapsed", placeholder="Who",
                             on_change=save_text, args=(tid, "name", f"who_{tid}"))
        c_job.text_input("Job", value=todo["description"], key=f"job_{tid}",
                         label_visibility="collapsed", placeholder="Job",
                         on_change=save_text, args=(tid, "description", f"job_{tid}"))
        c_due.date_input("Due", value=due, key=f"due_{tid}", format="DD.MM.YYYY",
                         label_visibility="collapsed",
                         on_change=save_due, args=(tid, f"due_{tid}"))

        with c_stat.container(key=f"stat_{'yes' if done else 'no'}_{tid}"):
            if st.button("Yes" if done else "No", key=f"tog_{tid}", use_container_width=True):
                set_done(tid, label, not done)
                st.rerun()

        with c_del.container(key=f"del_{tid}"):
            with st.popover("✕", help="Delete", use_container_width=True):
                st.markdown("<p class='confirm'>Are you sure?</p>", unsafe_allow_html=True)
                if st.button("Delete", key=f"delok_{tid}", type="primary",
                             use_container_width=True):
                    delete_todo(tid, label)
                    st.rerun()

        if divider:
            st.divider()


header_row()
with st.container(key="rows"):
    if not todos:
        st.markdown("<div class='empty'>Nothing here yet. Add a task above.</div>",
                    unsafe_allow_html=True)
    for i, (t, hide) in enumerate(rows):
        next_is_sub = i + 1 < len(rows) and rows[i + 1][1]
        render(t, hide, divider=not next_is_sub)
