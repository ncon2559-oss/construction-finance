import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, time

# --------------------
# CONFIG
# --------------------
st.set_page_config(page_title="Labor Summary", layout="wide")
DB = "labor.db"
WORK_START = time(8, 0)
WORK_END = time(17, 0)

# --------------------
# DB
# --------------------
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS employee (
    id INTEGER,
    name TEXT,
    daily_salary REAL,
    project TEXT,
    PRIMARY KEY (id, project)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    emp_id INTEGER,
    project TEXT,
    work_date TEXT,
    late_minutes INTEGER,
    ot_minutes INTEGER
)
""")
conn.commit()

# --------------------
# HELPER
# --------------------
def parse_time(t):
    try:
        return datetime.strptime(t, "%H:%M").time()
    except:
        return None

def calc_late_minutes(in_time):
    if not in_time:
        return 0
    late = (
        datetime.combine(datetime.today(), in_time)
        - datetime.combine(datetime.today(), WORK_START)
    ).seconds // 60
    return max(late, 0)

# --------------------
# UI
# --------------------
st.title("👷 Labor / Attendance System")

project = st.text_input("Project / Site", "DEFAULT")

uploaded = st.file_uploader("Drag and drop attendance excel", type=["xlsx"])

# --------------------
# IMPORT EXCEL
# --------------------
if uploaded:
    df = pd.read_excel(uploaded, header=None)

    # ดึงข้อมูลหัวพนักงาน
    emp_id = int(str(df.iloc[1, 0]).split(":")[1])
    name = str(df.iloc[1, 1]).split(":")[1].strip()
    daily_salary = float(str(df.iloc[3, 0]).split(":")[1])

    cur.execute("""
        INSERT OR IGNORE INTO employee (id, name, daily_salary, project)
        VALUES (?, ?, ?, ?)
    """, (emp_id, name, daily_salary, project))

    # ตารางเวลาเริ่มที่ row 6
    for i in range(6, len(df)):
        date_raw = df.iloc[i, 0]
        in_raw = df.iloc[i, 2]

        if pd.isna(date_raw) or pd.isna(in_raw):
            continue

        work_date = datetime.strptime(date_raw, "%m-%d").replace(year=2025)
        in_time = parse_time(str(in_raw))

        late = calc_late_minutes(in_time)

        cur.execute("""
            INSERT INTO attendance (emp_id, project, work_date, late_minutes, ot_minutes)
            VALUES (?, ?, ?, ?, ?)
        """, (emp_id, project, work_date.strftime("%Y-%m-%d"), late, 0))

    conn.commit()
    st.success(f"Imported {name} สำเร็จ")

# --------------------
# SUMMARY
# --------------------
st.header("📊 Summary")

summary = pd.read_sql("""
    SELECT 
        e.id,
        e.name,
        e.daily_salary,
        COUNT(a.work_date) AS days,
        IFNULL(SUM(a.late_minutes),0) AS late
    FROM employee e
    LEFT JOIN attendance a 
        ON e.id = a.emp_id AND e.project = a.project
    WHERE e.project = ?
    GROUP BY e.id, e.name, e.daily_salary
""", conn, params=(project,))

if not summary.empty:
    summary["ค่าแรงพื้นฐาน"] = summary["days"] * summary["daily_salary"]
    summary["หักสาย"] = summary["late"] * 1
    summary["ค่าแรงสุทธิ"] = summary["ค่าแรงพื้นฐาน"] - summary["หักสาย"]

    st.dataframe(
        summary[[
            "name",
            "days",
            "daily_salary",
            "ค่าแรงพื้นฐาน",
            "late",
            "หักสาย",
            "ค่าแรงสุทธิ"
        ]],
        use_container_width=True
    )
else:
    st.info("ยังไม่มีข้อมูลใน project นี้")
