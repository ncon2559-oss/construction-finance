import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time

# ======================
# CONFIG
# ======================
st.set_page_config("Construction Finance", layout="wide")

# ======================
# DATABASE
# ======================
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS project(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contract INTEGER,
    active INTEGER DEFAULT 1
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS income(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    phase TEXT,
    percent REAL,
    amount INTEGER,
    status TEXT,
    receive_date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS expense(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    category TEXT,
    description TEXT,
    amount INTEGER,
    expense_date TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS employee(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    emp_code TEXT,
    name TEXT,
    daily_salary INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    emp_id INTEGER,
    work_date TEXT,
    in_time TEXT,
    out_time TEXT,
    late_minutes INTEGER,
    work_minutes INTEGER,
    ot_minutes INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS document(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    filename TEXT,
    upload_date TEXT
)
""")

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
# PROJECT SELECT
# ======================
st.sidebar.header("📁 โครงการ")

projects = pd.read_sql("SELECT * FROM project WHERE active=1", conn)

with st.sidebar.expander("➕ เพิ่มโครงการ"):
    pname = st.text_input("ชื่อโครงการ")
    pcontract = st.number_input("มูลค่าสัญญา", step=100000)
    if st.button("บันทึกโครงการ"):
        c.execute(
            "INSERT INTO project(name,contract) VALUES(?,?)",
            (pname, pcontract)
        )
        conn.commit()
        st.rerun()

if projects.empty:
    st.warning("ยังไม่มีโครงการ")
    st.stop()

pname = st.sidebar.selectbox("เลือกโครงการ", projects["name"])
project = projects[projects["name"] == pname].iloc[0]
PID = int(project["id"])
CONTRACT = int(project["contract"])

menu = st.sidebar.radio(
    "เมนู",
    ["Dashboard", "Income", "Expense", "Labor", "Documents"]
)

# ======================
# DASHBOARD
# ======================
if menu == "Dashboard":
    st.title("📊 Dashboard")

    inc = pd.read_sql(
        "SELECT SUM(amount) t FROM income WHERE project_id=? AND status='รับเงินแล้ว'",
        conn, params=(PID,)
    )["t"].iloc[0] or 0

    exp = pd.read_sql(
        "SELECT SUM(amount) t FROM expense WHERE project_id=?",
        conn, params=(PID,)
    )["t"].iloc[0] or 0

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("มูลค่าสัญญา", f"{CONTRACT:,.0f}")
    col2.metric("รับเงินแล้ว", f"{inc:,.0f}")
    col3.metric("ค่าใช้จ่าย", f"{exp:,.0f}")
    col4.metric("คงเหลือ", f"{CONTRACT-inc:,.0f}")

# ======================
# INCOME
# ======================
elif menu == "Income":
    st.title("💰 Income")

    with st.form("income"):
        phase = st.text_input("งวด")
        percent = st.number_input("%", 0.0, 100.0)
        status = st.selectbox("สถานะ", ["ยังไม่ถึง", "เบิกได้", "รับเงินแล้ว"])
        rdate = st.date_input("วันที่", date.today())
        if st.form_submit_button("บันทึก"):
            amount = int(CONTRACT * percent / 100)
            c.execute("""
                INSERT INTO income(project_id,phase,percent,amount,status,receive_date)
                VALUES(?,?,?,?,?,?)
            """,(PID,phase,percent,amount,status,rdate.isoformat()))
            conn.commit()
            st.rerun()

    df = pd.read_sql(
        "SELECT phase,percent,amount,status FROM income WHERE project_id=?",
        conn, params=(PID,)
    )
    st.dataframe(df, use_container_width=True)

# ======================
# EXPENSE
# ======================
elif menu == "Expense":
    st.title("📉 Expense")

    with st.form("expense"):
        cat = st.selectbox("หมวด", ["Labor","Material","Other"])
        desc = st.text_input("รายละเอียด")
        amt = st.number_input("จำนวนเงิน", step=1000)
        d = st.date_input("วันที่", date.today())
        if st.form_submit_button("บันทึก"):
            c.execute("""
                INSERT INTO expense(project_id,category,description,amount,expense_date)
                VALUES(?,?,?,?,?)
            """,(PID,cat,desc,amt,d.isoformat()))
            conn.commit()
            st.rerun()

    df = pd.read_sql(
        "SELECT category,description,amount FROM expense WHERE project_id=?",
        conn, params=(PID,)
    )
    st.dataframe(df, use_container_width=True)

# ======================
# LABOR / ATTENDANCE
# ======================
elif menu == "Labor":
    st.title("👷 ค่าแรงคนงาน")

    file = st.file_uploader("Import Attendance Excel", type=["xlsx"])
    if file:
        df = pd.read_excel(file, header=None)

        emp_code = str(df.iloc[1,0]).split(":")[1].strip()
        name = str(df.iloc[1,1]).split(":")[1].strip()
        daily = int(str(df.iloc[3,0]).split(":")[1].strip())

        c.execute("""
            INSERT OR IGNORE INTO employee(project_id,emp_code,name,daily_salary)
            VALUES(?,?,?,?)
        """,(PID,emp_code,name,daily))
        conn.commit()

        emp_id = pd.read_sql(
            "SELECT id FROM employee WHERE emp_code=? AND project_id=?",
            conn, params=(emp_code,PID)
        ).iloc[0]["id"]

        start = df[df.iloc[:,0]=="Date"].index[0]+1

        for i in range(start, len(df)):
            d = df.iloc[i,0]
            if pd.isna(d): continue

            tin = df.iloc[i,2]
            tout = df.iloc[i,5]
            if pd.isna(tin) or pd.isna(tout): continue

            tin = datetime.strptime(str(tin), "%H:%M").time()
            tout = datetime.strptime(str(tout), "%H:%M").time()

            late = max(0, (datetime.combine(date.today(), tin) -
                            datetime.combine(date.today(), time(8,0))).seconds//60)

            work = (datetime.combine(date.today(), tout) -
                    datetime.combine(date.today(), tin)).seconds//60

            ot = max(0, work - 540)

            c.execute("""
                INSERT INTO attendance
                (project_id,emp_id,work_date,in_time,out_time,late_minutes,work_minutes,ot_minutes)
                VALUES(?,?,?,?,?,?,?,?)
            """,(PID,emp_id,str(d),tin.strftime("%H:%M"),
                 tout.strftime("%H:%M"),late,work,ot))
        conn.commit()
        st.success("Import สำเร็จ")

    summary = pd.read_sql("""
        SELECT e.name,
               COUNT(a.id) days,
               SUM(e.daily_salary) salary,
               SUM(a.late_minutes) late,
               SUM(a.ot_minutes) ot
        FROM employee e
        LEFT JOIN attendance a ON e.id=a.emp_id
        WHERE e.project_id=?
        GROUP BY e.id
    """, conn, params=(PID,))

    summary["หักสาย"] = summary["late"] * 1
    summary["ค่าแรงสุทธิ"] = summary["salary"] - summary["หักสาย"]

    st.dataframe(summary, use_container_width=True)

# ======================
# DOCUMENTS
# ======================
elif menu == "Documents":
    st.title("📎 Documents")
    f = st.file_uploader("Upload file")
    if f:
        c.execute(
            "INSERT INTO document(project_id,filename,upload_date) VALUES(?,?,?)",
            (PID,f.name,date.today().isoformat())
        )
        conn.commit()
        st.success("อัปโหลดแล้ว")

    df = pd.read_sql(
        "SELECT filename,upload_date FROM document WHERE project_id=?",
        conn, params=(PID,)
    )
    st.dataframe(df, use_container_width=True)
