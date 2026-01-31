import streamlit as st
import sqlite3
import pandas as pd

# ----------------------
# DATABASE
# ----------------------
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY,
    name TEXT,
    contract_value INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY,
    phase TEXT,
    percent INTEGER,
    amount INTEGER
)
""")

conn.commit()

# ----------------------
# LOGIN
# ----------------------
st.set_page_config(page_title="ระบบการเงินบริษัทก่อสร้าง", layout="wide")

if "login" not in st.session_state:
    st.session_state.login = False

def login():
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
    login()
    st.stop()

# ----------------------
# DASHBOARD
# ----------------------
st.title("📊 ระบบการเงินโครงการก่อสร้าง")
st.subheader("โครงการ: Water Tank & Fire Pump")

contract = 3_900_000

c.execute("SELECT SUM(amount)

