import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, time

st.set_page_config(page_title="Construction Finance", layout="wide")

# ================= DB =================
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.executescript("""
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);

CREATE TABLE IF NOT EXISTS employee (
    id INTEGER PRIMARY KEY,
    name TEXT,
    daily_salary REAL
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    emp_id INTEGER,
    work_date TEXT,
    in_time TEXT,
    out_time TEXT,
    late_minutes INTEGER,
    ot_minutes INTEGER,
    salary REAL
);
""")
conn.commit()

# ================= HELPERS =================
def parse_time(t):
    try:
        return datetime.strptime(t, "%H:%M").time()
    except:
        return None

WORK_START = time(8,0)
WORK_END = time(17,0)

# ================= SIDEBAR =================
st.sidebar.title("🏗 Construction Finance")
menu = st.sidebar.radio(
    "Menu",
    ["Projects", "Employees", "Attendance Import", "Labor Summary"]
)

# ================= PROJECT =================
if menu == "Projects":
    st.header("📁 Projects")

    name = st.text_input("Project name")
    if st.button("➕ Add Project"):
        c.execute("INSERT INTO project (name) VALUES (?)", (name,))
        conn.commit()
        st.success("Added")

    df = pd.read_sql("SELECT * FROM project", conn)
    st.dataframe(df)

# ================= EMPLOYEE =================
elif menu == "Employees":
    st.header("👷 Employees")

    emp_id = st.number_input("Employee ID", step=1)
    emp_name = st.text_input("Name")
    daily = st.number_input("Daily Salary", step=50)

    if st.button("➕ Save Employee"):
        c.execute(
            "REPLACE INTO employee (id, name, daily_salary) VALUES (?,?,?)",
            (emp_id, emp_name, daily)
        )
        conn.commit()
        st.success("Saved")

    st.dataframe(pd.read_sql("SELECT * FROM employee", conn))

# ================= ATTENDANCE =================
elif menu == "Attendance Import":
    st.header("📥 Import Attendance")

    projects = pd.read_sql("SELECT * FROM project", conn)
    pid = st.selectbox("Select Project", projects["id"], format_func=lambda x:
        projects.set_index("id").loc[x]["name"]
    )

    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(file, header=None)

        emp_id = None
        emp_name = None
        daily_salary = 0

        for _, row in df.iterrows():
            row_str = " ".join(row.astype(str))

            if "ID:" in row_str:
                emp_id = int(row_str.split("ID:")[1].split()[0])

            if "Name:" in row_str:
                emp_name = row_str.split("Name:")[1].split("Department")[0].strip()

            if "Daily Salary:" in row_str:
                daily_salary = float(row_str.split("Daily Salary:")[1].split()[0])

            if str(row[0]).startswith("01-"):
                date = row[0]
                in_t = parse_time(str(row[2]))
                out_t = parse_time(str(row[3]))

                if in_t:
                    late = max(0, (datetime.combine(datetime.today(), in_t) -
                                   datetime.combine(datetime.today(), WORK_START)).seconds // 60)

                    ot = 0
                    if out_t and out_t > WORK_END:
                        ot = (datetime.combine(datetime.today(), out_t) -
                              datetime.combine(datetime.today(), WORK_END)).seconds // 60

                    salary = daily_salary - late

                    c.execute("""
                        INSERT INTO attendance
                        (project_id, emp_id, work_date, in_time, out_time, late_minutes, ot_minutes, salary)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (pid, emp_id, date, str(in_t), str(out_t), late, ot, salary))

        conn.commit()
        st.success("Imported")

# ================= SUMMARY =================
elif menu == "Labor Summary":
    st.header("💰 Labor Summary")

    projects = pd.read_sql("SELECT * FROM project", conn)
    pid = st.selectbox("Select Project", projects["id"], format_func=lambda x:
        projects.set_index("id").loc[x]["name"]
    )

    summary = pd.read_sql("""
        SELECT e.name,
               COUNT(a.work_date) AS work_days,
               SUM(a.salary) AS total_salary,
               SUM(a.late_minutes) AS late_min,
               SUM(a.ot_minutes) AS ot_min
        FROM attendance a
        JOIN employee e ON a.emp_id = e.id
        WHERE a.project_id = ?
        GROUP BY e.id, e.name
    """, conn, params=(pid,))

    st.dataframe(summary)
