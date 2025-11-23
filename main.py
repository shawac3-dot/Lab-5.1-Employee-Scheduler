from flask import Flask, request, render_template, redirect, url_for, flash
import sqlite3
import os
import math
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

DATABASE = '/nfs/employees.db'
PER_PAGE_DEFAULT = 10
EASTERN = ZoneInfo("America/New_York")

# -----------------------
# Slack Notification
# -----------------------
def slack_notify(text):
    webhook = os.environ.get("SLACK_WEBHOOK")
    if not webhook:
        print("Slack webhook not set.")
        return
    try:
        requests.post(webhook, json={"text": text}, timeout=5)
    except Exception as e:
        print("Slack error:", e)

# -----------------------
# Validation Functions
# -----------------------
def validate_employee(employee_id, name, phone, hourly_rate):
    errors = []

    if not employee_id.isdigit():
        errors.append("Employee ID must be an integer.")
    if not re.fullmatch(r"[A-Za-z ]+", name):
        errors.append("Name must contain only letters and spaces.")
    if not phone.isdigit():
        errors.append("Phone must contain only digits.")
    try:
        rate = float(hourly_rate)
        if rate < 0:
            errors.append("Hourly rate must be non-negative.")
        elif len(hourly_rate.split('.')[-1]) > 2:
            errors.append("Hourly rate can have at most 2 decimal places.")
    except ValueError:
        errors.append("Hourly rate must be a number.")

    return errors

# -----------------------
# Database Functions
# -----------------------
def get_db():
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                hourly_rate REAL NOT NULL
            );
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS time_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                clock_in TEXT,
                clock_out TEXT,
                hours_worked REAL,
                FOREIGN KEY(employee_id) REFERENCES employees(employee_id)
            );
        ''')
        db.commit()
        db.close()

# -----------------------
# Routes
# -----------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')

        # DELETE EMPLOYEE
        if action == 'delete':
            emp_id = request.form.get('id')
            if emp_id:
                db = get_db()
                db.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
                db.execute('DELETE FROM time_logs WHERE employee_id = ?', (emp_id,))
                db.commit(); db.close()
                flash('Employee deleted successfully.', 'success')
            else:
                flash('Missing employee id.', 'danger')
            return redirect(url_for('index'))

        # UPDATE EMPLOYEE
        if action == 'update':
            emp_id = request.form.get('id')
            employee_id = request.form.get('employee_id')
            name = request.form.get('name')
            phone = request.form.get('phone')
            hourly_rate = request.form.get('hourly_rate')

            if not (emp_id and employee_id and name and phone and hourly_rate):
                flash('Missing fields for update.', 'danger')
            else:
                errors = validate_employee(employee_id, name, phone, hourly_rate)
                if errors:
                    flash(" | ".join(errors), "danger")
                else:
                    hourly_rate = round(float(hourly_rate), 2)
                    db = get_db()
                    try:
                        db.execute('''
                            UPDATE employees
                            SET employee_id=?, name=?, phone=?, hourly_rate=?
                            WHERE id=?
                        ''', (employee_id, name, phone, hourly_rate, emp_id))
                        db.commit()
                        flash('Employee updated successfully.', 'success')
                    except sqlite3.IntegrityError:
                        flash('Employee ID must be unique.', 'danger')
                    db.close()
            return redirect(url_for('index'))

        # ADD EMPLOYEE
        employee_id = request.form.get('employee_id')
        name = request.form.get('name')
        phone = request.form.get('phone')
        hourly_rate = request.form.get('hourly_rate')

        if employee_id and name and phone and hourly_rate:
            errors = validate_employee(employee_id, name, phone, hourly_rate)
            if errors:
                flash(" | ".join(errors), "danger")
            else:
                hourly_rate = round(float(hourly_rate), 2)
                db = get_db()
                try:
                    db.execute('''
                        INSERT INTO employees (employee_id, name, phone, hourly_rate)
                        VALUES (?, ?, ?, ?)
                    ''', (employee_id, name, phone, hourly_rate))
                    db.commit()
                    flash('Employee added successfully.', 'success')
                except sqlite3.IntegrityError:
                    flash('Employee ID must be unique.', 'danger')
                db.close()
        else:
            flash('Missing fields for new employee.', 'danger')
        return redirect(url_for('index'))

    # GET EMPLOYEES
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except ValueError:
        page = 1
    try:
        per_page = max(int(request.args.get('per', PER_PAGE_DEFAULT)), 1)
    except ValueError:
        per_page = PER_PAGE_DEFAULT
    offset = (page - 1) * per_page

    db = get_db()
    total = db.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    employees = db.execute(
        'SELECT * FROM employees ORDER BY id DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()

    employees_with_hours = []
    for emp in employees:
        total_hours = db.execute(
            'SELECT SUM(hours_worked) FROM time_logs WHERE employee_id=?',
            (emp['employee_id'],)
        ).fetchone()[0] or 0
        emp_dict = dict(emp)
        emp_dict['total_hours'] = round(total_hours, 2)
        emp_dict['hourly_rate'] = round(emp_dict['hourly_rate'], 2)
        employees_with_hours.append(emp_dict)
    db.close()

    pages = max(1, math.ceil(total / per_page))
    has_prev = page > 1
    has_next = page < pages
    start_page = max(1, page - 2)
    end_page = min(pages, page + 2)

    return render_template(
        'index.html',
        employees=employees_with_hours,
        page=page, pages=pages, per_page=per_page,
        has_prev=has_prev, has_next=has_next, total=total,
        start_page=start_page, end_page=end_page
    )

# -----------------------
# Clock In/Out
# -----------------------
@app.route('/clock', methods=['POST'])
def clock():
    employee_id = request.form.get('employee_id')
    action = request.form.get('action')  # clock_in or clock_out

    if not employee_id or not action:
        flash('Missing employee ID or action.', 'danger')
        return redirect(url_for('index'))

    db = get_db()
    now = datetime.now(tz=EASTERN)

    if action == 'clock_in':
        db.execute(
            'INSERT INTO time_logs (employee_id, clock_in) VALUES (?, ?)',
            (employee_id, now.isoformat(timespec='seconds'))
        )
        db.commit()
        slack_notify(f"Employee {employee_id} CLOCKED IN at {now.strftime('%H:%M:%S')} EST")
        flash(f'Employee {employee_id} clocked in at {now.strftime("%H:%M:%S")}.', 'success')

    elif action == 'clock_out':
        log = db.execute(
            'SELECT * FROM time_logs WHERE employee_id=? AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
            (employee_id,)
        ).fetchone()
        if log:
            clock_in_time = datetime.fromisoformat(log['clock_in']).replace(tzinfo=EASTERN)
            delta_hours = (now - clock_in_time).total_seconds() / 3600
            db.execute(
                'UPDATE time_logs SET clock_out=?, hours_worked=? WHERE id=?',
                (now.isoformat(timespec='seconds'), round(delta_hours, 2), log['id'])
            )
            db.commit()
            slack_notify(f"Employee {employee_id} CLOCKED OUT at {now.strftime('%H:%M:%S')} EST — worked {delta_hours:.2f} hrs")
            flash(f'Employee {employee_id} clocked out at {now.strftime("%H:%M:%S")} ({delta_hours:.2f} hours).', 'success')
        else:
            flash('No clock-in found to clock out.', 'danger')
    db.close()
    return redirect(url_for('index'))

# -----------------------
# Reset Total Hours
# -----------------------
@app.route('/reset_hours', methods=['POST'])
def reset_hours():
    emp_id = request.form.get('employee_id')
    if emp_id:
        db = get_db()
        db.execute('UPDATE time_logs SET hours_worked=0 WHERE employee_id=?', (emp_id,))
        db.commit(); db.close()
        flash(f'Total hours reset for employee {emp_id}.', 'success')
    else:
        flash('Missing employee ID.', 'danger')
    return redirect(url_for('index'))

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    init_db()
    app.run(debug=True, host='0.0.0.0', port=port)
