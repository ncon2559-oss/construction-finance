# app.py
# แอปการเงินบริษัทก่อสร้าง (ใช้งานจริง) ด้วย Streamlit
# งาน: Water Tank & Fire Pump
# มูลค่าสัญญา: 3,900,000 บาท (ไม่รวม VAT)

import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --------------------
# Database (SQLite)
# --------------------
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
""
)

c.execute("""
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contract REAL
)
""
)

c.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    phase TEXT,
    percent REAL,
    amount REAL,
    received_date TEXT
)
""
)

c.execute("""
CREATE TABLE IF NOT EXISTS expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    category TEXT,
    description TEXT,
    amount REAL,
    expense_date TEXT
)
""
)

conn.commit()

# --------------------
# Init Data (ครั้งแรก)
# --------------------
c.execute("INSERT OR IGNORE INTO users VALUES ('ncon2559','1234','admin')")
c.execute("INSERT OR IGNORE INTO project VALUES (1,'Water Tank & Fire Pump',3900000)")
conn.commit()

# --------------------
# Login
# --------------------
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("ระบบการเงินบริษัทก่อสร้าง")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("เข้าสู่ระบบ"):
        user = c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if user:
            st.session_state.login = True
            st.experimental_rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

# --------------------
# Dashboard
# --------------------
st.title("Dashboard การเงิน")
project = c.execute("SELECT * FROM project WHERE id=1").fetchone()

income_df = pd.read_sql("SELECT * FROM income", conn)
expense_df = pd.read_sql("SELECT * FROM expense", conn)

received = income_df["amount"].sum() if not income_df.empty else 0
spent = expense_df["amount"].sum() if not expense_df.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("มูลค่าสัญญา", f"฿{project[2]:,.0f}")
col2.metric("รับเงินแล้ว", f"฿{received:,.0f}")
col3.metric("รายจ่าย", f"฿{spent:,.0f}")
col4.metric("คงเหลือเบิก", f"฿{project[2]-received:,.0f}")

st.divider()

# --------------------
# Add Income (Progress)
# --------------------
st.subheader("บันทึกรับเงินตามผลงาน")
with st.form("income_form"):
    phase = st.selectbox("งวด", ["งวดที่ 1","งวดที่ 2","งวดที่ 3","งวดที่ 4"])
    percent = st.number_input("% ผลงาน", 0.0, 100.0)
    amount = st.number_input("จำนวนเงิน", 0.0)
    d = st.date_input("วันที่รับเงิน", date.today())
    if st.form_submit_button("บันทึก"):
        c.execute("INSERT INTO income (project_id,phase,percent,amount,received_date) VALUES (1,?,?,?,?)",
                  (phase, percent, amount, str(d)))
        conn.commit()
        st.success("บันทึกเรียบร้อย")
        st.experimental_rerun()

# --------------------
# Add Expense
# --------------------
st.subheader("บันทึกรายจ่าย")
with st.form("expense_form"):
    cat = st.selectbox("หมวด", ["ค่าแรง","ค่าวัสดุ","ค่าเช่าเครื่องจักร","อื่นๆ"])
    desc = st.text_input("รายละเอียด")
    amt = st.number_input("จำนวนเงิน", 0.0)
    ed = st.date_input("วันที่จ่าย", date.today())
    if st.form_submit_button("บันทึก"):
        c.execute("INSERT INTO expense (project_id,category,description,amount,expense_date) VALUES (1,?,?,?,?)",
                  (cat, desc, amt, str(ed)))
        conn.commit()
        st.success("บันทึกเรียบร้อย")
        st.experimental_rerun()

# --------------------
# Tables
# --------------------
st.subheader("ประวัติรับเงิน")
st.dataframe(income_df)

st.subheader("ประวัติรายจ่าย")
st.dataframe(expense_df)
