import sqlite3

# Database file path, ensure this matches the path used in your Flask application
DATABASE = '/nfs/employees.db'

def connect_db():
    """Connect to the SQLite database."""
    return sqlite3.connect(DATABASE)

def clear_test_employees():
    """Clear only the test employees from the database."""
    db = connect_db()
    # Delete time logs for test employees first to avoid foreign key conflicts
    db.execute("DELETE FROM time_logs WHERE employee_id LIKE 'EMP%'")
    # Delete test employees
    db.execute("DELETE FROM employees WHERE employee_id LIKE 'EMP%'")
    db.commit()
    print('Test employees and their time logs have been deleted from the database.')
    db.close()

if __name__ == '__main__':
    clear_test_employees()
