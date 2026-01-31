import streamlit as st
import sqlite3
import pandas as pd

# ----------------------
# DATABASE
# ----------------------
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

# Project table
c.execute("""
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contract_value INTEGER
)
""")

# Income table (รุ่นใหม่)
c.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    phase TEXT,
    percent INTEGER,
    amount INTEGER
)
""")
conn.commit()

# ----------------------
# MIGRATION (สำคัญมาก)
# เพิ่ม project_id ถ้า income เก่ามีแต่ยังไม่มี
# ----------------------
c.execute("PRAGMA table_info(income)")
columns = [col[1] for col in c.fetchall()]

if "project_id" not in columns:
    c.execute("ALTER TABLE income ADD COLUMN project_id INTEGER")
    conn.commit()

# ----------------------
# INIT DEFAULT PROJECT
# ----------------------
c.execute("SELECT COUNT(*) FROM project")
if c.fetchone()[0] == 0:
    c.execute(
        "INSERT INTO project (name, contract_value) VALUES (?, ?)",
        ("Water Tank & Fire Pump", 3_900_000)
    )
    conn.commit()

# ดึง project ปัจจุบัน (ตอนนี้มีแค่อันเดียว)
c.execute("SELECT id, name, contract_value FROM project LIMIT 1")
project = c.fetchone()
PROJECT_ID = project[0]
PROJECT_NAME = project[1]
CONTRACT_VALUE = project[2]

# ----------------------
# FIX DATA เก่า (ถ้า project_id ว่าง)
# ----------------------
c.execute(
    "UPDATE income SET project_id = ? WHERE project_id IS NULL",
    (PROJECT_ID,)
)
conn.commit()

# ----------------------
# PAGE CONFIG
# ----------------------
st.set_page_config(page_title="ระบบการเงินบริษัทก่อสร้าง", layout="wide")

# ----------------------
# LOGIN
# ----------------------
if "login" not in st.session_state:
    st.session_state.login = False

def login_page():
    st.title("🔐 เข้าสู่ระบบ")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "ncon2559" and pw == "1234":
            st.session_state.login = True
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

if not st.session_state.login:
    login_page()
    st.stop()

# ----------------------
# SIDEBAR
# ----------------------
st.sidebar.title("📁 เมนูระบบ")
menu = st.sidebar.radio(
    "เลือกเมนู",
    ["Dashboard", "บันทึกรับเงิน", "รายการย้อนหลัง / แก้ไข"]
)

st.sidebar.divider()
st.sidebar.write(f"📌 โครงการ: {PROJECT_NAME}")
st.sidebar.write("👤 ผู้ใช้: ncon2559")

if st.sidebar.button("ออกจากระบบ"):
    st.session_state.login = False
    st.rerun()

# ----------------------
# SUMMARY
# ----------------------
c.execute(
    "SELECT SUM(amount) FROM income WHERE project_id = ?",
    (PROJECT_ID,)
)
received = c.fetchone()[0]
received = received if received else 0

# ----------------------
# DASHBOARD
# ----------------------
if menu == "Dashboard":
    st.title("📊 Dashboard การเงิน")
    st.success("เข้าสู่ระบบสำเร็จ ✅")

    col1, col2, col3 = st.columns(3)
    col1.metric("มูลค่าสัญญา", f"{CONTRACT_VALUE:,.0f} บาท")
    col2.metric("รับเงินแล้ว", f"{received:,.0f} บาท")
    col3.metric("คงเหลือ", f"{CONTRACT_VALUE - received:,.0f} บาท")

    st.write(f"โครงการ: **{PROJECT_NAME}**")

# ----------------------
# ADD INCOME
# ----------------------
elif menu == "บันทึกรับเงิน":
    st.title("➕ บันทึกรับเงินงวดงาน")

    phase = st.text_input("งวดงาน (เช่น งวดที่ 1)")
    percent = st.number_input("เปอร์เซ็นต์ผลงาน", 0, 100)
    amount = st.number_input("จำนวนเงิน (บาท)", step=1000)

    if st.button("บันทึกข้อมูล"):
        if phase and amount > 0:
            c.execute(
                """
                INSERT INTO income (project_id, phase, percent, amount)
                VALUES (?, ?, ?, ?)
                """,
                (PROJECT_ID, phase, percent, amount)
            )
            conn.commit()
            st.success("บันทึกข้อมูลเรียบร้อย ✅")
            st.rerun()
        else:
            st.warning("กรุณากรอกข้อมูลงวดและจำนวนเงิน")

# ----------------------
# HISTORY + EDIT
# ----------------------
elif menu == "รายการย้อนหลัง / แก้ไข":
    st.title("📋 รายการรับเงินย้อนหลัง")

    df = pd.read_sql_query(
        "SELECT id, phase, percent, amount FROM income WHERE project_id = ?",
        conn,
        params=(PROJECT_ID,)
    )
    st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("✏️ แก้ไขรายการ")

    if len(df) > 0:
        edit_id = st.selectbox("เลือกรายการ (id)", df["id"])
        row = df[df["id"] == edit_id].iloc[0]

        new_phase = st.text_input("งวดงาน", row["phase"])
        new_percent = st.number_input("เปอร์เซ็นต์", 0, 100, int(row["percent"]))
        new_amount = st.number_input("จำนวนเงิน", step=1000, value=int(row["amount"]))

        if st.button("บันทึกการแก้ไข"):
            c.execute(
                """
                UPDATE income
                SET phase = ?, percent = ?, amount = ?
                WHERE id = ?
                """,
                (new_phase, new_percent, new_amount, edit_id)
            )
            conn.commit()
            st.success("แก้ไขข้อมูลเรียบร้อย ✅")
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูล")
