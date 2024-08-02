# db.py
# This file is responsible for database initialization and operations.
# It includes functions to initialize the database, save data to the database, and fetch data from the database.

import sqlite3
from contextlib import closing
import json
import pandas as pd

# Initialize SQLite database
def init_db():
    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_data (
                report TEXT,
                business_date TEXT,
                data TEXT,
                PRIMARY KEY (report, business_date)
            )
        ''')
        conn.commit()

# Save fetched data to the database
def save_data_to_db(report, date, data_str):
    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO report_data (report, business_date, data) VALUES (?, ?, ?)",
                       (report, date, data_str))
        conn.commit()

# Fetch data from the database
def fetch_data_from_db(report, date):
    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM report_data WHERE report = ? AND business_date = ?", (report, date))
        row = cursor.fetchone()
        if row:
            data_json = json.loads(row[0])
            return pd.json_normalize(data_json['value'])
        else:
            return pd.DataFrame()
