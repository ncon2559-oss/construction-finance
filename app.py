import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, time

# =====================
# CONFIG
# =====================
st.set_page_config(page_title="Construction Payroll", layout="wide")

# =====================
# DATABASE
# =====================
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS employee(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_code TEXT,
    name TEXT,
    daily_salary INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id INTEGER,
    work_date TEXT,
    time_in TEXT,
    late_min INTEGER,
    FOREIGN KEY(emp_id) REFERENCES employee(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS payroll(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id INTEGER,
    work_days INTEGER,
    late_deduct INTEGER,
    total_salary INTEGER,
    FOREIGN KEY(emp_id) REFERENCES employee(id)
)
""")

conn.commit()

# =====================
# HELPER FUNCTIONS
# =====================
def parse_time(t):
    try:
        return datetime.strptime(t, "%H:%M").time()
    except:
        return None

def calc_late_minutes(t_in):
    if not t_in:
        return 0
    start = time(8, 0)
    if t_in <= start:
        return 0
    return int(
        (datetime.combine(datetime.today(), t_in) -
         datetime.combine(datetime.today(), start)).seconds / 60
    )

# =====================
# UI
# =====================
st.title("👷 ระบบค่าแรงจากเครื่องแสกนนิ้ว")

file = st.file_uploader("📤 อัปโหลดไฟล์ Attendance (.xlsx)", type=["xlsx"])

if file:
    raw = pd.read_excel(file, header=None)

    results = []

    i = 0
    while i < len(raw):
        row = str(raw.iloc[i, 0])

        # ===== เจอหัวพนักงาน =====
        if row.startswith("ID:"):
            emp_code = row.split("ID:")[1].split()[0]
            name = row.split("Name:")[1].split("Department")[0].strip()

            salary_row = raw.iloc[i+1, 0]
            daily_salary = int(
                str(salary_row).split("Daily Salary:")[1].split()[0]
            )

            # upsert employee
            c.execute("SELECT id FROM employee WHERE emp_code=?", (emp_code,))
            emp = c.fetchone()
            if emp:
                emp_id = emp[0]
            else:
                c.execute(
                    "INSERT INTO employee(emp_code,name,daily_salary) VALUES(?,?,?)",
                    (emp_code, name, daily_salary)
                )
                emp_id = c.lastrowid

            # ===== ตารางเข้างาน =====
            work_days = 0
            late_total = 0

            j = i + 4
            while j < len(raw) and not str(raw.iloc[j, 0]).startswith("ID:"):
                date_val = raw.iloc[j, 0]
                time_in = raw.iloc[j, 2]

                if pd.notna(time_in):
                    work_days += 1
                    t_in = parse_time(str(time_in))
                    late = calc_late_minutes(t_in)
                    late_total += late

                    c.execute("""
                        INSERT INTO attendance(emp_id,work_date,time_in,late_min)
                        VALUES(?,?,?,?)
                    """, (emp_id, str(date_val), str(time_in), late))

                j += 1

            total_salary = work_days * daily_salary - late_total

            c.execute("""
                INSERT INTO payroll(emp_id,work_days,late_deduct,total_salary)
                VALUES(?,?,?,?)
            """, (emp_id, work_days, late_total, total_salary))

            results.append({
                "ชื่อ": name,
                "วันทำงาน": work_days,
                "หักสาย (บาท)": late_total,
                "ค่าแรงรวม": total_salary
            })

            i = j
        else:
            i += 1

    conn.commit()

    st.success("✅ ประมวลผลเรียบร้อย")
    st.dataframe(pd.DataFrame(results), use_container_width=True)

# =====================
# VIEW EMPLOYEE
# =====================
st.divider()
st.header("📊 สถิติพนักงาน")

df = pd.read_sql_query("""
SELECT e.name,
       p.work_days,
       p.late_deduct,
       p.total_salary
FROM payroll p
JOIN employee e ON p.emp_id=e.id
ORDER BY p.id DESC
""", conn)

st.dataframe(df, use_container_width=True)
