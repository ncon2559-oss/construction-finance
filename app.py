import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ======================
# CONFIG
# ======================
st.set_page_config("Construction Finance System", layout="wide")

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
# PROJECT
# ======================
st.sidebar.header("📁 โครงการ")

projects = pd.read_sql(
    "SELECT * FROM project WHERE active=1",
    conn
)

with st.sidebar.expander("➕ เพิ่มโครงการ"):
    name = st.text_input("ชื่อโครงการ")
    contract = st.number_input("มูลค่าสัญญา", step=100000)
    if st.button("เพิ่ม"):
        if name and contract > 0:
            c.execute(
                "INSERT INTO project(name, contract) VALUES (?,?)",
                (name, contract)
            )
            conn.commit()
            st.rerun()

if projects.empty:
    st.warning("ยังไม่มีโครงการ")
    st.stop()

project_name = st.sidebar.selectbox("เลือกโครงการ", projects["name"])
project = projects[projects["name"] == project_name].iloc[0]
PID = int(project["id"])
CONTRACT = int(project["contract"])

if st.sidebar.button("🚫 ปิดโครงการ"):
    c.execute("UPDATE project SET active=0 WHERE id=?", (PID,))
    conn.commit()
    st.rerun()

menu = st.sidebar.radio(
    "เมนู",
    ["Dashboard", "Income", "Expense", "Attendance"]
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("มูลค่าสัญญา", f"{CONTRACT:,.0f}")
    c2.metric("รับเงินแล้ว", f"{inc:,.0f}")
    c3.metric("ค่าใช้จ่าย", f"{exp:,.0f}")
    c4.metric("คงเหลือ", f"{CONTRACT-inc:,.0f}")

# ======================
# INCOME (CRUD)
# ======================
elif menu == "Income":
    st.title("💰 Income")

    with st.form("add_income"):
        phase = st.text_input("งวด")
        percent = st.number_input("%", 0.0, 100.0)
        status = st.selectbox("สถานะ", ["ยังไม่ถึง", "เบิกได้", "รับเงินแล้ว"])
        d = st.date_input("วันที่", date.today())
        if st.form_submit_button("เพิ่ม"):
            amt = int(CONTRACT * percent / 100)
            c.execute("""
                INSERT INTO income(project_id,phase,percent,amount,status,receive_date)
                VALUES (?,?,?,?,?,?)
            """, (PID, phase, percent, amt, status, d.isoformat()))
            conn.commit()
            st.rerun()

    df = pd.read_sql(
        "SELECT * FROM income WHERE project_id=?",
        conn, params=(PID,)
    )

    for _, r in df.iterrows():
        with st.expander(f"{r['phase']} | {r['amount']:,.0f}"):
            phase = st.text_input("งวด", r["phase"], key=f"ip{r['id']}")
            percent = st.number_input("%", value=r["percent"], key=f"ipp{r['id']}")
            status = st.selectbox(
                "สถานะ",
                ["ยังไม่ถึง", "เบิกได้", "รับเงินแล้ว"],
                index=["ยังไม่ถึง","เบิกได้","รับเงินแล้ว"].index(r["status"]),
                key=f"ips{r['id']}"
            )
            if st.button("💾 แก้ไข", key=f"iu{r['id']}"):
                amt = int(CONTRACT * percent / 100)
                c.execute("""
                    UPDATE income SET phase=?,percent=?,amount=?,status=?
                    WHERE id=?
                """, (phase, percent, amt, status, r["id"]))
                conn.commit()
                st.rerun()

            if st.button("🗑 ลบ", key=f"id{r['id']}"):
                c.execute("DELETE FROM income WHERE id=?", (r["id"],))
                conn.commit()
                st.rerun()

# ======================
# EXPENSE (CRUD)
# ======================
elif menu == "Expense":
    st.title("📉 Expense")

    with st.form("add_exp"):
        cat = st.selectbox("หมวด", ["Labor", "Material", "Other"])
        desc = st.text_input("รายละเอียด")
        amt = st.number_input("จำนวนเงิน", step=1000)
        d = st.date_input("วันที่", date.today())
        if st.form_submit_button("เพิ่ม"):
            c.execute("""
                INSERT INTO expense(project_id,category,description,amount,expense_date)
                VALUES (?,?,?,?,?)
            """, (PID, cat, desc, amt, d.isoformat()))
            conn.commit()
            st.rerun()

    df = pd.read_sql(
        "SELECT * FROM expense WHERE project_id=?",
        conn, params=(PID,)
    )

    for _, r in df.iterrows():
        with st.expander(f"{r['category']} | {r['amount']:,.0f}"):
            desc = st.text_input("รายละเอียด", r["description"], key=f"ed{r['id']}")
            amt = st.number_input("จำนวนเงิน", value=r["amount"], step=1000, key=f"ea{r['id']}")
            if st.button("💾 แก้ไข", key=f"eu{r['id']}"):
                c.execute("""
                    UPDATE expense SET description=?,amount=?
                    WHERE id=?
                """, (desc, amt, r["id"]))
                conn.commit()
                st.rerun()

            if st.button("🗑 ลบ", key=f"edl{r['id']}"):
                c.execute("DELETE FROM expense WHERE id=?", (r["id"],))
                conn.commit()
                st.rerun()

# ======================
# ATTENDANCE
# ======================
elif menu == "Attendance":
    st.title("🕒 Attendance → ค่าแรง")

    daily = st.number_input("ค่าแรง/วัน", step=50)
    file = st.file_uploader("Excel", type=["xlsx","xls"])

    if file and daily > 0:
        df = pd.read_excel(file)
        df.columns = [c.strip() for c in df.columns]

        if "Name" not in df.columns or "In" not in df.columns:
            st.error("ไฟล์ต้องมี Name และ In")
            st.stop()

        df = df[df["In"].notna()]

        summary = (
            df.groupby("Name")
            .size()
            .reset_index(name="days")
        )
        summary["wage"] = summary["days"] * daily

        st.dataframe(summary, use_container_width=True)
        total = int(summary["wage"].sum())
        st.metric("ค่าแรงรวม", f"{total:,.0f}")

        if st.button("บันทึกเป็นค่าแรงโครงการ"):
            c.execute("""
                INSERT INTO expense(project_id,category,description,amount,expense_date)
                VALUES (?,?,?,?,?)
            """, (
                PID,
                "Labor",
                f"ค่าแรงจาก Attendance ({len(summary)} คน)",
                total,
                date.today().isoformat()
            ))
            conn.commit()
            st.success("บันทึกแล้ว ✅")
