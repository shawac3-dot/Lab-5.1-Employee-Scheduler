from flask import Flask, request, render_template, redirect, url_for, flash
import sqlite3
import os
import math
from datetime import datetime
from zoneinfo import ZoneInfo
import re

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# Path to DB (keep same as you used)
DATABASE = '/nfs/employees.db'
PER_PAGE_DEFAULT = 10
EASTERN = ZoneInfo("America/New_York")

# -----------------------
# Validation Functions
# -----------------------
def validate_employee(employee_id, name, phone, hourly_rate):
    errors = []

    # Employee ID must be integer (non-empty)
    if not (isinstance(employee_id, str) and employee_id.isdigit()):
        errors.append("Employee ID must be an integer.")

    # Name must contain only letters and spaces
    if not (isinstance(name, str) and re.fullmatch(r"[A-Za-z ]+", name)):
        errors.append("Name must contain only letters and spaces.")

    # Phone must be integer (digits only)
    if not (isinstance(phone, str) and phone.isdigit()):
        errors.append("Phone must contain only digits.")

    # Hourly rate must be float with up to 2 decimals
    try:
        # Accept numeric strings like '15' or '15.5' or '15.50'
        rate = float(hourly_rate)
        if rate < 0:
            errors.append("Hourly rate must be non-negative.")
        else:
            # check decimals (works if hourly_rate is string with decimal part)
            parts = str(hourly_rate).split('.')
            if len(parts) == 2 and len(parts[1]) > 2:
                errors.append("Hourly rate can have at most 2 decimal places.")
    except Exception:
        errors.append("Hourly rate must be a number.")

    return errors

# -----------------------
# DB helper utilities (open/close per operation)
# -----------------------
def open_conn():
    # timeout increased to avoid transient locks, check_same_thread=False not strictly required
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    # Helpful to enforce foreign keys if you rely on them
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
# Initialize DB (with UNIQUE integer employee_id)
# -----------------------
def init_db():
    with open_conn() as db:
        # employees.employee_id stored as INTEGER and UNIQUE to enforce uniqueness at DB level.
        # Keep employee internal id (id) as autoincrement primary key.
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
    if request.method == 'POST':
        action = request.form.get('action')

        # ----------------- DELETE EMPLOYEE -----------------
        if action == 'delete':
            emp_row_id = request.form.get('id')
            if emp_row_id and emp_row_id.isdigit():
                # fetch the employee_id value so we can remove time_logs correctly
                emp = fetchone('SELECT employee_id FROM employees WHERE id = ?', (emp_row_id,))
                if emp:
                    employee_id_val = emp['employee_id']
                    # Delete time_logs for that employee_id and then employee row
                    execute('DELETE FROM time_logs WHERE employee_id = ?', (employee_id_val,))
                    execute('DELETE FROM employees WHERE id = ?', (emp_row_id,))
                    flash('Employee deleted successfully.', 'success')
                else:
                    flash('Employee not found.', 'danger')
            else:
                flash('Missing or invalid employee id.', 'danger')
            return redirect(url_for('index'))

        # ----------------- UPDATE EMPLOYEE -----------------
        if action == 'update':
            emp_row_id = request.form.get('id')
            employee_id = request.form.get('employee_id', '').strip()
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            hourly_rate = request.form.get('hourly_rate', '').strip()

            if not (emp_row_id and emp_row_id.isdigit() and employee_id and name and phone and hourly_rate):
                flash('Missing fields for update.', 'danger')
                return redirect(url_for('index'))

            errors = validate_employee(employee_id, name, phone, hourly_rate)
            if errors:
                flash(" | ".join(errors), "danger")
                return redirect(url_for('index'))

            # convert and round
            employee_id_int = int(employee_id)
            hourly_rate_val = round(float(hourly_rate), 2)

            # Ensure uniqueness: check if another row has same employee_id
            existing = fetchone('SELECT id FROM employees WHERE employee_id = ? AND id != ?', (employee_id_int, emp_row_id))
            if existing:
                flash('Another employee with that Employee ID already exists.', 'danger')
                return redirect(url_for('index'))

            try:
                execute('''
                    UPDATE employees
                    SET employee_id=?, name=?, phone=?, hourly_rate=?
                    WHERE id=?
                ''', (employee_id_int, name, phone, hourly_rate_val, emp_row_id))
                flash('Employee updated successfully.', 'success')
            except sqlite3.IntegrityError:
                flash('Employee ID must be unique.', 'danger')
            return redirect(url_for('index'))

        # ----------------- ADD EMPLOYEE -----------------
        # Note: form uses action="add" hidden input in your template earlier
        employee_id = request.form.get('employee_id', '').strip()
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        hourly_rate = request.form.get('hourly_rate', '').strip()

        if not (employee_id and name and phone and hourly_rate):
            flash('Missing fields for new employee.', 'danger')
            return redirect(url_for('index'))

        errors = validate_employee(employee_id, name, phone, hourly_rate)
        if errors:
            flash(" | ".join(errors), "danger")
            return redirect(url_for('index'))

        # convert types
        employee_id_int = int(employee_id)
        hourly_rate_val = round(float(hourly_rate), 2)

        # check uniqueness before attempting insert to provide nicer message
        if fetchone('SELECT 1 FROM employees WHERE employee_id = ?', (employee_id_int,)):
            flash('Employee ID already exists.', 'danger')
            return redirect(url_for('index'))

        try:
            execute('''
                INSERT INTO employees (employee_id, name, phone, hourly_rate)
                VALUES (?, ?, ?, ?)
            ''', (employee_id_int, name, phone, hourly_rate_val))
            flash('Employee added successfully.', 'success')
        except sqlite3.IntegrityError:
            # fallback if race condition creates duplicate
            flash('Employee ID must be unique.', 'danger')
        return redirect(url_for('index'))

    # ----------------- GET EMPLOYEES -----------------
    try:
        page = max(int(request.args.get('page', 1)), 1)
    except ValueError:
        page = 1
    try:
        per_page = max(int(request.args.get('per', PER_PAGE_DEFAULT)), 1)
    except ValueError:
        per_page = PER_PAGE_DEFAULT
    offset = (page - 1) * per_page

    total_row = fetchone('SELECT COUNT(*) as c FROM employees')
    total = total_row['c'] if total_row else 0

    employees = fetchall(
        'SELECT * FROM employees ORDER BY id DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    )

    employees_with_hours = []
    for emp in employees:
        # Sum of hours_worked (treat NULL as 0)
        total_hours_row = fetchone('SELECT SUM(hours_worked) AS s FROM time_logs WHERE employee_id = ?', (emp['employee_id'],))
        total_hours = total_hours_row['s'] if total_hours_row and total_hours_row['s'] is not None else 0
        emp_dict = dict(emp)
        emp_dict['total_hours'] = round(float(total_hours), 2)
        emp_dict['hourly_rate'] = round(float(emp_dict['hourly_rate']), 2)
        employees_with_hours.append(emp_dict)

    pages = max(1, math.ceil(total / per_page)) if per_page else 1
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
    employee_id = request.form.get('employee_id', '').strip()
    action = request.form.get('action')  # clock_in or clock_out

    if not (employee_id and action):
        flash('Missing employee ID or action.', 'danger')
        return redirect(url_for('index'))

    if not employee_id.isdigit():
        flash('Invalid employee ID.', 'danger')
        return redirect(url_for('index'))

    employee_id_int = int(employee_id)
    now = datetime.now(tz=EASTERN)

    # ensure employee exists
    if not fetchone('SELECT 1 FROM employees WHERE employee_id = ?', (employee_id_int,)):
        flash('Employee not found.', 'danger')
        return redirect(url_for('index'))

    if action == 'clock_in':
        try:
            execute(
                'INSERT INTO time_logs (employee_id, clock_in) VALUES (?, ?)',
                (employee_id_int, now.isoformat(timespec='seconds'))
            )
            flash(f'Employee {employee_id} clocked in at {now.strftime("%H:%M:%S")}.', 'success')
        except Exception as e:
            flash('Error clocking in.', 'danger')

    elif action == 'clock_out':
        # find most recent clock_in row without clock_out
        log = fetchone(
            'SELECT * FROM time_logs WHERE employee_id=? AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
            (employee_id_int,)
        )
        if log:
            # parse stored ISO. datetime.fromisoformat handles timezone offset if present.
            clock_in_time = datetime.fromisoformat(log['clock_in'])
            # ensure both are timezone-aware or naive consistently; our now is timezone-aware
            if clock_in_time.tzinfo is None:
                clock_in_time = clock_in_time.replace(tzinfo=EASTERN)
            delta_hours = (now - clock_in_time).total_seconds() / 3600.0
            delta_hours = round(delta_hours, 2)
            try:
                execute(
                    'UPDATE time_logs SET clock_out=?, hours_worked=? WHERE id=?',
                    (now.isoformat(timespec='seconds'), delta_hours, log['id'])
                )
                flash(f'Employee {employee_id} clocked out at {now.strftime("%H:%M:%S")} ({delta_hours:.2f} hours).', 'success')
            except Exception:
                flash('Error recording clock out.', 'danger')
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
    # ensure employee exists
    if not fetchone('SELECT 1 FROM employees WHERE employee_id = ?', (emp_int,)):
        flash('Employee not found.', 'danger')
        return redirect(url_for('index'))

    try:
        execute('UPDATE time_logs SET hours_worked=0 WHERE employee_id=?', (emp_int,))
        flash(f'Total hours reset for employee {emp_int}.', 'success')
    except Exception:
        flash('Error resetting hours.', 'danger')
    return redirect(url_for('index'))

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    init_db()
    app.run(debug=True, host='0.0.0.0', port=port)
