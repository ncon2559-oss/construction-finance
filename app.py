import streamlit as st
import sqlite3
import pandas as pd

# ----------------------
# DATABASE
# ----------------------
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase TEXT,
    percent INTEGER,
    amount INTEGER
)
""")
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
    st.title("เข้าสู่ระบบ")
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
# DASHBOARD
# ----------------------
st.title("📊 ระบบการเงินโครงการก่อสร้าง")
st.subheader("โครงการ: Water Tank & Fire Pump")

CONTRACT_VALUE = 3_900_000

c.execute("SELECT SUM(amount) FROM income")
received = c.fetchone()[0]
received = received if received else 0

col1, col2, col3 = st.columns(3)
col1.metric("มูลค่าสัญญา", f"{CONTRACT_VALUE:,.0f} บาท")
col2.metric("รับเงินแล้ว", f"{received:,.0f} บาท")
col3.metric("คงเหลือ", f"{CONTRACT_VALUE - received:,.0f} บาท")

st.divider()

# ----------------------
# INPUT INCOME
# ----------------------
st.subheader("➕ บันทึกรับเงินงวดงาน")

phase = st.text_input("งวดงาน (เช่น งวดที่ 1)")
percent = st.number_input("เปอร์เซ็นต์ผลงาน", min_value=0, max_value=100)
amount = st.number_input("จำนวนเงิน (บาท)", step=1000)

if st.button("บันทึกข้อมูล"):
    if phase and amount > 0:
        c.execute(
            "INSERT INTO income (phase, percent, amount) VALUES (?, ?, ?)",
            (phase, percent, amount)
        )
        conn.commit()
        st.success("บันทึกข้อมูลเรียบร้อย ✅")
        st.rerun()
    else:
        st.warning("กรุณากรอกข้อมูลงวดและจำนวนเงิน")

st.divider()

# ----------------------
# TABLE
# ----------------------
st.subheader("📋 รายการรับเงินทั้งหมด")
df = pd.read_sql_query("SELECT phase, percent, amount FROM income", conn)
st.dataframe(df, use_container_width=True)
