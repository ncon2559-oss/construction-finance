import streamlit as st
import sqlite3
from datetime import date
import pandas as pd

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Construction Finance", layout="wide")

# ======================
# DATABASE
# ======================
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contract_value INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    phase TEXT,
    percent REAL,
    amount INTEGER,
    status TEXT,
    receive_date TEXT
)
""")

conn.commit()

# ======================
# INIT PROJECT
# ======================
c.execute("SELECT COUNT(*) FROM project")
if c.fetchone()[0] == 0:
    c.execute(
        "INSERT INTO project (name, contract_value) VALUES (?, ?)",
        ("Water Tank & Fire Pump", 3_900_000)
    )
    conn.commit()

# ======================
# LOGIN
# ======================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u == "ncon2559" and p == "1234":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Login ไม่ถูกต้อง")
    st.stop()

# ======================
# SELECT PROJECT
# ======================
projects = pd.read_sql_query("SELECT * FROM project", conn)
project_name = st.selectbox("📁 เลือกโครงการ", projects["name"])
project = projects[projects["name"] == project_name].iloc[0]
PROJECT_ID = project["id"]
CONTRACT = project["contract_value"]

st.divider()

# ======================
# OVERVIEW
# ======================
st.header("📊 Income – งวดงาน")

income_df = pd.read_sql_query(
    "SELECT * FROM income WHERE project_id=?",
    conn, params=(PROJECT_ID,)
)

received = income_df[income_df["status"] == "รับเงินแล้ว"]["amount"].sum()
remaining = CONTRACT - received

col1, col2, col3 = st.columns(3)
col1.metric("มูลค่าสัญญา", f"{CONTRACT:,.0f}")
col2.metric("รับเงินแล้ว", f"{received:,.0f}")
col3.metric("คงเหลือ", f"{remaining:,.0f}")

st.divider()

# ======================
# ADD PHASE
# ======================
st.subheader("➕ เพิ่มงวดงาน")

with st.form("add_income"):
    phase = st.text_input("ชื่องวด (เช่น งวดที่ 1)")
    percent = st.number_input("เปอร์เซ็นต์ของสัญญา (%)", min_value=0.0, max_value=100.0)
    status = st.selectbox("สถานะ", ["ยังไม่ถึง", "เบิกได้", "รับเงินแล้ว"])
    r_date = st.date_input("วันที่รับเงิน", value=date.today())

    submit = st.form_submit_button("บันทึกงวด")

    if submit:
        amount = int(CONTRACT * percent / 100)
        c.execute(
            """
            INSERT INTO income (project_id, phase, percent, amount, status, receive_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (PROJECT_ID, phase, percent, amount, status, r_date.isoformat())
        )
        conn.commit()
        st.success("เพิ่มงวดงานแล้ว ✅")
        st.rerun()

# ======================
# TABLE
# ======================
st.subheader("📋 ตารางงวดงาน")

if income_df.empty:
    st.info("ยังไม่มีข้อมูลงวดงาน")
else:
    show_df = income_df[[
        "phase", "percent", "amount", "status", "receive_date"
    ]]
    show_df.columns = ["งวด", "%", "จำนวนเงิน", "สถานะ", "วันที่รับ"]
    st.dataframe(show_df, use_container_width=True)
