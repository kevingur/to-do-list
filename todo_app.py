"""
Yapılacaklar listesi — Streamlit + Supabase

Yerelde çalıştırma:
    pip install -r requirements.txt
    streamlit run todo_app.py

Bağlantı bilgileri .streamlit/secrets.toml içinde (yerel) veya
Streamlit Cloud > App settings > Secrets alanında tutulur.
"""

from datetime import date, datetime, timezone

import streamlit as st
from supabase import Client, create_client


# ---------- bağlantı ----------
@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


sb = get_client()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- veri ----------
def fetch_todos() -> list[dict]:
    return sb.table("todos").select("*").order("due").execute().data


def log(action: str, todo_id: str | None, todo_name: str) -> None:
    sb.table("todo_log").insert(
        {"action": action, "todo_id": todo_id, "todo_name": todo_name}
    ).execute()


def fetch_log(limit: int = 50) -> list[dict]:
    return (
        sb.table("todo_log")
        .select("*")
        .order("ts", desc=True)
        .limit(limit)
        .execute()
        .data
    )


# ---------- işlemler ----------
def add_todo(name: str, description: str, due: date) -> None:
    row = (
        sb.table("todos")
        .insert(
            {
                "name": name.strip(),
                "description": description.strip(),
                "due": due.isoformat(),
            }
        )
        .execute()
        .data[0]
    )
    log("EKLENDİ", row["id"], row["name"])


def toggle_done(todo_id: str, todo_name: str) -> None:
    done = st.session_state[f"chk_{todo_id}"]
    sb.table("todos").update(
        {"done": done, "completed_at": now_iso() if done else None}
    ).eq("id", todo_id).execute()
    log("TAMAMLANDI" if done else "GERİ AÇILDI", todo_id, todo_name)


def delete_todo(todo_id: str, todo_name: str) -> None:
    sb.table("todos").delete().eq("id", todo_id).execute()
    log("SİLİNDİ", todo_id, todo_name)


# ---------- arayüz ----------
st.set_page_config(page_title="Yapılacaklar", page_icon="✓", layout="centered")
st.title("Yapılacaklar")

with st.form("yeni_gorev", clear_on_submit=True):
    name = st.text_input("Görev adı", placeholder="Ne yapılacak?")
    description = st.text_area("Açıklama", placeholder="İsteğe bağlı detay", height=80)
    due = st.date_input("Tarih", value=date.today())
    if st.form_submit_button("Ekle", type="primary", use_container_width=True):
        if name.strip():
            add_todo(name, description, due)
            st.rerun()
        else:
            st.warning("Görev adı boş olamaz.")

try:
    todos = fetch_todos()
except Exception as e:
    st.error(f"Veritabanına bağlanılamadı: {e}")
    st.stop()

open_tasks = [t for t in todos if not t["done"]]
done_tasks = sorted(
    (t for t in todos if t["done"]), key=lambda t: t["completed_at"] or "", reverse=True
)


def render(todo: dict) -> None:
    due = date.fromisoformat(todo["due"])
    overdue = not todo["done"] and due < date.today()
    with st.container(border=True):
        col_chk, col_body, col_del = st.columns([0.6, 8, 0.8], vertical_alignment="top")
        col_chk.checkbox(
            "Tamamlandı",
            value=todo["done"],
            key=f"chk_{todo['id']}",
            on_change=toggle_done,
            args=(todo["id"], todo["name"]),
            label_visibility="collapsed",
        )
        col_body.markdown(f"~~{todo['name']}~~" if todo["done"] else f"**{todo['name']}**")
        if todo["description"]:
            col_body.caption(todo["description"])
        date_str = due.strftime("%d.%m.%Y")
        if overdue:
            col_body.markdown(f":red[Gecikti — {date_str}]")
        elif due == date.today() and not todo["done"]:
            col_body.markdown(f":orange[Bugün — {date_str}]")
        else:
            col_body.caption(date_str)
        col_del.button(
            "🗑",
            key=f"del_{todo['id']}",
            on_click=delete_todo,
            args=(todo["id"], todo["name"]),
            help="Sil",
        )


st.subheader(f"Açık görevler ({len(open_tasks)})")
if not open_tasks:
    st.info("Açık görev yok. Yukarıdan yeni bir görev ekle.")
for t in open_tasks:
    render(t)

if done_tasks:
    with st.expander(f"Tamamlananlar ({len(done_tasks)})"):
        for t in done_tasks:
            render(t)

st.divider()
with st.expander("İşlem geçmişi (log)"):
    rows = fetch_log()
    if rows:
        lines = [
            f"{datetime.fromisoformat(r['ts']).astimezone().strftime('%d.%m.%Y %H:%M:%S')} | "
            f"{r['action']:<11} | {r['todo_name']}"
            for r in rows
        ]
        st.code("\n".join(lines), language=None)
    else:
        st.caption("Henüz kayıt yok")
