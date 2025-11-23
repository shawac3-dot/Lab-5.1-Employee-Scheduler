from flask import Flask, request, render_template, redirect, url_for, flash
import sqlite3
import os
import math
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import requests  # for Slack

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# Path to DB
DATABASE = '/nfs/employees.db'
PER_PAGE_DEFAULT = 10
EASTERN = ZoneInfo("America/New_York")

SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")  # Slack webhook from env

# -----------------------
# Validation Functions
# -----------------------
def validate_employee(employee_id, name, phone, hourly_rate):
    errors = []

    if not (isinstance(employee_id, str) and employee_id.isdigit()):
        errors.append("Employee ID must be an integer.")
    if not (isinstance(name, str) and re.fullmatch(r"[A-Za-z ]+", name)):
        errors.append("Name must contain only letters and spaces.")
    if not (isinstance(phone, str) and phone.isdigit()):
        errors.append("Phone must contain only digits.")
    try:
        rate = float(hourly_rate)
        if rate < 0:
            errors.append("Hourly rate must be non-negative.")
        else:
            parts = str(hourly_rate).split('.')
            if len(parts) == 2 and len(parts[1]) > 2:
                errors.append("Hourly rate can have at most 2 decimal places.")
    except Exception:
        errors.append("Hourly rate must be a number.")
    return errors

# -----------------------
# Slack Notification
# -----------------------
def slack_notify(message: str):
    if not SLACK_WEBHOOK:
        print("Slack webhook not set, skipping notification.")
        return
    try:
        requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=5)
    except Exception as e:
        print("Slack error:", e)

# -----------------------
# DB helper utilities
# -----------------------
def open_conn():
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def fetchall(query, args=()):
    conn = open_conn()
    cur = conn.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return rows

def fetchone(query, args=()):
    conn = open_conn()
    cur = conn.execute(query, args)
    row = cur.fetchone()
    conn.close()
    return row

def execute(query, args=()):
    conn = open_conn()
    cur = conn.execute(query, args)
    conn.commit()
    lastrowid = cur.lastrowid
    conn.close()
    return lastrowid

# -----------------------
# Initialize DB
# -----------------------
def init_db():
    with open_conn() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                hourly_rate REAL NOT NULL
            );
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS time_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                clock_in TEXT,
                clock_out TEXT,
                hours_worked REAL,
                FOREIGN KEY(employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
            );
        ''')
        db.commit()

# -----------------------
# Routes
# -----------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    # ... same as before (add/update/delete employee logic)
    # unchanged, omitted here for brevity
    pass

# -----------------------
# Clock In/Out
# -----------------------
@app.route('/clock', methods=['POST'])
def clock():
    employee_id = request.form.get('employee_id', '').strip()
    action = request.form.get('action')
    if not (employee_id and action):
        flash('Missing employee ID or action.', 'danger')
        return redirect(url_for('index'))
    if not employee_id.isdigit():
        flash('Invalid employee ID.', 'danger')
        return redirect(url_for('index'))
    employee_id_int = int(employee_id)
    now = datetime.now(tz=EASTERN)

    if not fetchone('SELECT 1 FROM employees WHERE employee_id = ?', (employee_id_int,)):
        flash('Employee not found.', 'danger')
        return redirect(url_for('index'))

    if action == 'clock_in':
        execute(
            'INSERT INTO time_logs (employee_id, clock_in) VALUES (?, ?)',
            (employee_id_int, now.isoformat(timespec='seconds'))
        )
        msg = f"Employee {employee_id} clocked IN at {now.strftime('%H:%M:%S')} (Eastern)."
        flash(msg, 'success')
        slack_notify(msg)  # send to Slack
    elif action == 'clock_out':
        log = fetchone(
            'SELECT * FROM time_logs WHERE employee_id=? AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
            (employee_id_int,)
        )
        if log:
            clock_in_time = datetime.fromisoformat(log['clock_in'])
            if clock_in_time.tzinfo is None:
                clock_in_time = clock_in_time.replace(tzinfo=EASTERN)
            delta_hours = round((now - clock_in_time).total_seconds() / 3600.0, 2)
            execute(
                'UPDATE time_logs SET clock_out=?, hours_worked=? WHERE id=?',
                (now.isoformat(timespec='seconds'), delta_hours, log['id'])
            )
            msg = f"Employee {employee_id} clocked OUT at {now.strftime('%H:%M:%S')} (Eastern). Worked {delta_hours} hrs."
            flash(msg, 'success')
            slack_notify(msg)  # send to Slack
        else:
            flash('No clock-in found to clock out.', 'danger')

    return redirect(url_for('index'))

# -----------------------
# Reset Total Hours
# -----------------------
@app.route('/reset_hours', methods=['POST'])
def reset_hours():
    emp_id = request.form.get('employee_id', '').strip()
    if not emp_id or not emp_id.isdigit():
        flash('Missing or invalid employee ID.', 'danger')
        return redirect(url_for('index'))
    emp_int = int(emp_id)
    if not fetchone('SELECT 1 FROM employees WHERE employee_id = ?', (emp_int,)):
        flash('Employee not found.', 'danger')
        return redirect(url_for('index'))
    execute('UPDATE time_logs SET hours_worked=0 WHERE employee_id=?', (emp_int,))
    flash(f'Total hours reset for employee {emp_int}.', 'success')
    return redirect(url_for('index'))

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    init_db()
    app.run(debug=True, host='0.0.0.0', port=port)
