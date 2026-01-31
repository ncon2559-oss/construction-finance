import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Construction Finance System", layout="wide")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    percent INTEGER,
    amount INTEGER,
    receive_date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    category TEXT,
    description TEXT,
    amount INTEGER,
    expense_date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    worker_name TEXT,
    work_date TEXT,
    time_in TEXT,
    time_out TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    expense_id INTEGER,
    filename TEXT,
    filepath TEXT,
    upload_date TEXT
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
# PROJECT SELECT
# ======================
projects = pd.read_sql_query("SELECT * FROM project", conn)
project_name = st.sidebar.selectbox("📌 โครงการ", projects["name"])
proj = projects[projects["name"] == project_name].iloc[0]
PROJECT_ID = proj["id"]
CONTRACT_VALUE = proj["contract_value"]

# ======================
# SIDEBAR (GROUPED)
# ======================
st.sidebar.markdown("### 📊 ภาพรวม")
main_menu = st.sidebar.radio("", ["Overview"])

st.sidebar.markdown("### 📁 โครงการ")
project_menu = st.sidebar.radio(
    "",
    ["Income", "Documents"]
)

st.sidebar.markdown("### 💰 ค่าใช้จ่าย")
expense_menu = st.sidebar.radio(
    "",
    ["ค่าแรง", "ค่าใช้จ่ายอื่น"]
)

st.sidebar.markdown("### 🕒 เวลาเข้างาน")
time_menu = st.sidebar.radio("", ["Attendance"])

# ======================
# OVERVIEW
# ======================
if main_menu == "Overview":
    st.title("📊 ภาพรวมโครงการ")

    income = pd.read_sql_query(
        "SELECT SUM(amount) total FROM income WHERE project_id=?",
        conn, params=(PROJECT_ID,)
    )["total"].iloc[0] or 0

    expense = pd.read_sql_query(
        "SELECT SUM(amount) total FROM expense WHERE project_id=?",
        conn, params=(PROJECT_ID,)
    )["total"].iloc[0] or 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("มูลค่าสัญญา", f"{CONTRACT_VALUE:,.0f}")
    col2.metric("รับเงินแล้ว", f"{income:,.0f}")
    col3.metric("ค่าใช้จ่าย", f"{expense:,.0f}")
    col4.metric("คงเหลือ", f"{CONTRACT_VALUE - income:,.0f}")

# ======================
# INCOME
# ======================
if project_menu == "Income":
    st.title("💵 รายรับ / งวดงาน")

    phase = st.text_input("งวดงาน")
    percent = st.number_input("เปอร์เซ็นต์ผลงาน", 0, 100)
    amount = st.number_input("จำนวนเงิน", step=1000)
    rdate = st.date_input("วันที่รับเงิน", date.today())

    if st.button("บันทึกรายรับ"):
        c.execute(
            """
            INSERT INTO income (project_id, phase, percent, amount, receive_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (PROJECT_ID, phase, percent, amount, rdate.isoformat())
        )
        conn.commit()
        st.success("บันทึกรายรับแล้ว ✅")
        st.rerun()

    df = pd.read_sql_query(
        "SELECT phase, percent, amount, receive_date FROM income WHERE project_id=?",
        conn, params=(PROJECT_ID,)
    )
    st.dataframe(df, use_container_width=True)

# ======================
# LABOR EXPENSE
# ======================
if expense_menu == "ค่าแรง":
    st.title("👷 ค่าแรง")

    desc = st.text_input("งวด / เดือน")
    amount = st.number_input("จำนวนเงิน", step=1000)
    edate = st.date_input("วันที่จ่าย", date.today())

    if st.button("บันทึกค่าแรง"):
        c.execute(
            """
            INSERT INTO expense (project_id, category, description, amount, expense_date)
            VALUES (?, 'Labor', ?, ?, ?)
            """,
            (PROJECT_ID, desc, amount, edate.isoformat())
        )
        conn.commit()
        st.success("บันทึกค่าแรงแล้ว")
        st.rerun()

    df = pd.read_sql_query(
        "SELECT description, amount, expense_date FROM expense WHERE project_id=? AND category='Labor'",
        conn, params=(PROJECT_ID,)
    )
    st.dataframe(df, use_container_width=True)

# ======================
# ATTENDANCE
# ======================
if time_menu == "Attendance":
    st.title("🕒 เวลาเข้างาน (นำเข้าไฟล์)")
    file = st.file_uploader("ไฟล์จากเครื่องสแกนนิ้ว", type=["xlsx", "csv"])
    if file:
        df = pd.read_excel(file)
        st.dataframe(df.head())
        st.info("รอบหน้าจะ map ลงฐานข้อมูลอัตโนมัติ")

# ======================
# DOCUMENTS
# ======================
if project_menu == "Documents":
    st.title("📎 เอกสารโครงการ / ค่าแรง")

    upload = st.file_uploader("อัปโหลดไฟล์", type=["pdf", "jpg", "png"])
    if upload:
        path = os.path.join(UPLOAD_DIR, upload.name)
        with open(path, "wb") as f:
            f.write(upload.getbuffer())

        c.execute(
            """
            INSERT INTO document (project_id, filename, filepath, upload_date)
            VALUES (?, ?, ?, ?)
            """,
            (PROJECT_ID, upload.name, path, date.today().isoformat())
        )
        conn.commit()
        st.success("อัปโหลดไฟล์แล้ว")

    docs = pd.read_sql_query(
        "SELECT filename, upload_date FROM document WHERE project_id=?",
        conn, params=(PROJECT_ID,)
    )
    st.dataframe(docs, use_container_width=True)
