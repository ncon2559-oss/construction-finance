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
# DA
