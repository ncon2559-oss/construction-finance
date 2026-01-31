import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ======================
# DATABASE
# ======================
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

# --- PROJECT
c.execute("""
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contract_value INTEGER
)
""")

# --- INCOME
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

# --- EXPENSE
c.execute("""
CREATE TABLE IF NOT EXISTS expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    category TEXT,          -- Labor / Material / Other
    description TEXT,
    amount INTEGER,
    expense_date TEXT
)
""")

# --- TIME ATTENDANCE (IMPORT ONLY)
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

# --- DOCUMENT
c.execute("""
CREATE TABLE IF NOT EXISTS document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    expense_id INTEGER,
    filename TEXT,
    upload_date TEXT
)
""")

conn.commit()

# ======================
# INIT PROJECT (ถ้ายังไม่มี)
# ======================
c.execute("SELECT COUNT(*) FROM project")
if c.fetchone()[0] == 0:
    c.execute(
        "INSERT INTO project (name, contract_value) VALUES (?, ?)",
        ("Water Tank & Fire Pump", 3_900_000)
    )
    conn.commit()

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="Construction Finance System", layout="wide")

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
project_name = st.sidebar.selectbox(
    "📌 เลือกโครงการ",
    projects["name"]
)
PROJECT_ID = projects[projects["name"] == project_name]["id"].iloc[0]
CONTRACT_VALUE = projects[projects["name"] == project_name]["contract_value"].iloc[0]

# ======================
# SIDEBAR MENU
# ======================
menu = st.sidebar.radio(
    "📁 เมนู",
    [
        "Overview",
        "Income",
        "Expense (Labor)",
        "Expense (Other)",
        "Time Attendance",
        "Documents"
    ]
)

# ======================
# OVERVIEW
# ======================
if menu == "Overview":
    st.title("📊 ภาพรวมโครงการ")

    income = pd.read_sql_query(
        "SELECT SUM(amount) as total FROM income WHERE project_id=?",
        conn, params=(PROJECT_ID,)
    )["total"].iloc[0] or 0

    expense = pd.read_sql_query(
        "SELECT SUM(amount) as total FROM expense WHERE project_id=?",
        conn, params=(PROJECT_ID,)
    )["total"].iloc[0] or 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("มูลค่าสัญญา", f"{CONTRACT_VALUE:,.0f}")
    col2.metric("รับเงินแล้ว", f"{income:,.0f}")
    col3.metric("ค่าใช้จ่าย", f"{expense:,.0f}")
    col4.metric("กำไร / ขาดทุน", f"{income - expense:,.0f}")

# ======================
# EXPENSE - LABOR (SUMMARY)
# ======================
elif menu == "Expense (Labor)":
    st.title("👷 ค่าแรง (สรุป)")

    desc = st.text_input("งวด / เดือน (เช่น มี.ค. 2569)")
    amount = st.number_input("ค่าแรงรวม", step=1000)
    d = st.date_input("วันที่จ่าย", date.today())

    if st.button("บันทึกค่าแรง"):
        c.execute(
            """
            INSERT INTO expense (project_id, category, description, amount, expense_date)
            VALUES (?, 'Labor', ?, ?, ?)
            """,
            (PROJECT_ID, desc, amount, d.isoformat())
        )
        conn.commit()
        st.success("บันทึกค่าแรงแล้ว ✅")
        st.rerun()

    df = pd.read_sql_query(
        "SELECT * FROM expense WHERE project_id=? AND category='Labor'",
        conn, params=(PROJECT_ID,)
    )
    st.dataframe(df, use_container_width=True)

# ======================
# TIME ATTENDANCE (IMPORT ONLY)
# ======================
elif menu == "Time Attendance":
    st.title("🕒 เวลาเข้างาน (อ้างอิงจากเครื่องสแกนนิ้ว)")
    st.info("หน้านี้ใช้เก็บข้อมูลเวลาเท่านั้น ยังไม่คำนวณเงิน")

    uploaded = st.file_uploader("อัปโหลดไฟล์ Excel จากเครื่องสแกนนิ้ว", type=["xlsx", "csv"])
    if uploaded:
        df = pd.read_excel(uploaded)
        st.dataframe(df.head())
        st.success("อ่านไฟล์ได้ (รอบหน้าเราจะ map เข้าระบบให้เต็ม)")

# ======================
# DOCUMENTS
# ======================
elif menu == "Documents":
    st.title("📎 เอกสารโครงการ / ค่าแรง")

    file = st.file_uploader("อัปโหลดไฟล์", type=["pdf", "jpg", "png"])
    if file:
        c.execute(
            """
            INSERT INTO document (project_id, filename, upload_date)
            VALUES (?, ?, ?)
            """,
            (PROJECT_ID, file.name, date.today().isoformat())
        )
        conn.commit()
        st.success("บันทึกชื่อเอกสารแล้ว (ตัวไฟล์เก็บภายนอกได้ในอนาคต)")

    docs = pd.read_sql_query(
        "SELECT * FROM document WHERE project_id=?",
        conn, params=(PROJECT_ID,)
    )
    st.dataframe(docs, use_container_width=True)
