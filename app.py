import streamlit as st
import sqlite3
import pandas as pd

# ----------------------
# DATABASE
# ----------------------
conn = sqlite3.connect("finance.db", check_same_thread=False)
c = conn.cursor()

# Project table
c.execute("""
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contract_value INTEGER
)
""")

# Income table (รุ่นใหม่)
c.execute("""
CREATE TABLE IF NOT EXISTS income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    phase TEXT,
    percent INTEGER,
    amount INTEGER
)
""")
conn.commit()

# ----------------------
# MIGRATION (สำคัญมาก)
# เพิ่ม project_id ถ้า income เก่ามีแต่ยังไม่มี
# ----------------------
c.execute("PRAGMA table_info(income)")
columns = [col[1] for col in c.fetchall()]

if "project_id" not in columns:
    c.execute("ALTER TABLE income ADD COLUMN project_id INTEGER")
    conn.commit()

# ----------------------
# INIT DEFAULT PROJECT
# ----------------------
c.execute("SELECT COUNT(*) FROM project")
if c.fetchone()[0] == 0:
    c.execute(
        "INSERT INTO project (name, contract_value) VALUES (?, ?)",
        ("Water Tank & Fire Pump", 3_900_000)
    )
    conn.commit()

# ดึง project ปัจจุบัน (ตอนนี้มีแค่อันเดียว)
c.execute("SELECT id, name, contract_value FROM project LIMIT 1")
project = c.fetchone()
PROJECT_ID = project[0]
PROJECT_NAME = project[1]
CONTRACT_VALUE = project[2]

# ----------------------
# FIX DATA เก่า (ถ้า project_id ว่าง)
# ----------------------
c.execute(
    "UPDATE income SET project_id = ? WHERE project_id IS NULL",
    (PROJECT_ID,)
)
conn.commit()

# ----------------------
# PAGE CONFIG
# ----------------------
st.set_page_config(page_title="ระบบการเงินบริษัทก่อสร้าง", layout="wide")

# -----------
