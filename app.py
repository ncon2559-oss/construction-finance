import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Construction Finance System", layout="wide")

# ======================
# DATABASE
# ======================
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS project(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contract INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS income(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    phase TEXT,
    percent REAL,
    amount INTEGER,
    status TEXT,
    receive_date TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS expense(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    category TEXT,
    description TEXT,
    amount INTEGER,
    expense_date TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS document(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    filename TEXT,
    upload_date TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    worker TEXT,
    work_date TEXT,
    time_in TEXT,
    time_out TEXT
)""")

conn.commit()

# ======================
# AUTH
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
# PROJECT MANAGER
# ======================
st.sidebar.header("📁 โครงการ")

projects = pd.read_sql_query("SELECT * FROM project", conn)

with st.sidebar.expander("➕ เพิ่มโครงการ"):
    name = st.text_input("ชื่อโครงการ")
    contract = st.number_input("มูลค่าสัญญา", step=100000)
    if st.button("เพิ่มโครงการ"):
        c.execute("INSERT INTO project (name, contract) VALUES (?,?)",(name,contract))
        conn.commit()
        st.rerun()

if projects.empty:
    st.info("ยังไม่มีโครงการ")
    st.stop()

project_name = st.sidebar.selectbox("เลือกโครงการ", projects["name"])
project = projects[projects["name"]==project_name].iloc[0]
PID = int(project["id"])
CONTRACT = int(project["contract"])

menu = st.sidebar.radio("เมนู", [
    "Dashboard",
    "Income",
    "Expense",
    "Documents",
    "Attendance"
])

# ======================
# DASHBOARD
# ======================
if menu == "Dashboard":
    st.title("📊 Dashboard")
    inc = pd.read_sql_query("SELECT SUM(amount) t FROM income WHERE project_id=? AND status='รับเงินแล้ว'",conn,params=(PID,))["t"].iloc[0] or 0
    exp = pd.read_sql_query("SELECT SUM(amount) t FROM expense WHERE project_id=?",conn,params=(PID,))["t"].iloc[0] or 0
    col1,col2,col3,col4 = st.columns(4)
    col1.metric("มูลค่าสัญญา", f"{CONTRACT:,.0f}")
    col2.metric("รับเงินแล้ว", f"{inc:,.0f}")
    col3.metric("ค่าใช้จ่าย", f"{exp:,.0f}")
    col4.metric("คงเหลือ", f"{CONTRACT-inc:,.0f}")

# ======================
# INCOME
# ======================
elif menu == "Income":
    st.title("💰 Income (งวดงาน)")
    with st.form("add_income"):
        phase = st.text_input("งวด")
        percent = st.number_input("% ของสัญญา",0.0,100.0)
        status = st.selectbox("สถานะ",["ยังไม่ถึง","เบิกได้","รับเงินแล้ว"])
        rdate = st.date_input("วันที่รับเงิน", date.today())
        if st.form_submit_button("บันทึก"):
            amount = int(CONTRACT*percent/100)
            c.execute("""INSERT INTO income(project_id,phase,percent,amount,status,receive_date)
                         VALUES(?,?,?,?,?,?)""",
                      (PID,phase,percent,amount,status,rdate.isoformat()))
            conn.commit()
            st.rerun()
    df = pd.read_sql_query("SELECT phase,percent,amount,status,receive_date FROM income WHERE project_id=?",conn,params=(PID,))
    st.dataframe(df,use_container_width=True)

# ======================
# EXPENSE
# ======================
elif menu == "Expense":
    st.title("📉 Expense")
    with st.form("add_exp"):
        cat = st.selectbox("หมวด",["Labor","Material","Other"])
        desc = st.text_input("รายละเอียด")
        amt = st.number_input("จำนวนเงิน",step=1000)
        d = st.date_input("วันที่",date.today())
        if st.form_submit_button("บันทึก"):
            c.execute("""INSERT INTO expense(project_id,category,description,amount,expense_date)
                         VALUES(?,?,?,?,?)""",(PID,cat,desc,amt,d.isoformat()))
            conn.commit()
            st.rerun()
    df = pd.read_sql_query("SELECT category,description,amount,expense_date FROM expense WHERE project_id=?",conn,params=(PID,))
    st.dataframe(df,use_container_width=True)

# ======================
# DOCUMENTS
# ======================
elif menu == "Documents":
    st.title("📎 Documents")
    f = st.file_uploader("อัปโหลดไฟล์")
    if f:
        c.execute("INSERT INTO document(project_id,filename,upload_date) VALUES(?,?,?)",
                  (PID,f.name,date.today().isoformat()))
        conn.commit()
        st.success("บันทึกแล้ว")
    df = pd.read_sql_query("SELECT filename,upload_date FROM document WHERE project_id=?",conn,params=(PID,))
    st.dataframe(df,use_container_width=True)

# ======================
# ATTENDANCE
# ======================
elif menu == "Attendance":
    st.title("🕒 Attendance (Import)")
    up = st.file_uploa_
