<!doctype html>
<html lang="en" data-bs-theme="auto" id="html-root">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Employee Management</title>

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Oswald:wght@400;500;600&display=swap" rel="stylesheet">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
  </head>
  <body>
    <div class="container">

      <header class="mb-4 py-3 border-bottom d-flex align-items-center">
        <div>
          <div class="miami-title">Employee Management</div>
          <div class="miami-subtitle">by Austin Shaw</div>
        </div>
      </header>

      <!-- Flash messages -->
      {% with msgs = get_flashed_messages(with_categories=True) %}
        {% if msgs %}
          <div class="mb-3">
            {% for category, m in msgs %}
              {% set bs = 'success' if category=='success' else 'danger' if category=='danger' else 'primary' %}
              <div class="alert alert-{{ bs }} alert-dismissible fade show" role="alert">
                {{ m }}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
              </div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <!-- Add employee form -->
      <div class="card shadow-sm form-card mb-4">
        <div class="card-body">
          <h2 class="h5 mb-3">Add Employee</h2>
          <form method="POST" action="{{ url_for('index') }}" class="row g-3">
            <input type="hidden" name="action" value="add">
            <div class="col-md-3">
              <label for="employee_id" class="form-label">Employee ID</label>
              <input class="form-control" id="employee_id" name="employee_id" required>
            </div>
            <div class="col-md-3">
              <label for="name" class="form-label">Name</label>
              <input class="form-control" id="name" name="name" required>
            </div>
            <div class="col-md-3">
              <label for="phone" class="form-label">Phone</label>
              <input class="form-control" id="phone" name="phone" required
                     pattern="^[0-9()+\\-\\s]+$" title="Digits, spaces, (), - and + only">
            </div>
            <div class="col-md-3">
              <label for="hourly_rate" class="form-label">Hourly Rate</label>
              <input type="number" step="0.01" class="form-control" id="hourly_rate" name="hourly_rate" required>
            </div>
            <div class="col-12">
              <button class="btn btn-primary" type="submit">Add Employee</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Search + heading -->
      <div class="d-flex justify-content-between align-items-center mb-2">
        <h2 class="h5 m-0">All Employees</h2>
        <input id="filter" class="form-control" style="max-width: 280px;" placeholder="Search…">
      </div>

      <!-- Employees table -->
      <div class="card shadow-sm mb-3">
        <div class="table-responsive">
          <table class="table align-middle mb-0 table-striped">
            <thead>
              <tr>
                <th>ID</th>
                <th>Employee ID</th>
                <th>Name</th>
                <th>Phone</th>
                <th>Hourly Rate</th>
                <th>Total Hours</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody id="rows">
              {% for e in employees %}
              <tr>
                <td class="id text-secondary">{{ e['id'] }}</td>
                <td class="employee_id">{{ e['employee_id'] }}</td>
                <td class="name">{{ e['name'] }}</td>
                <td class="phone text-nowrap">{{ e['phone'] }}</td>
                <td class="hourly_rate">${{ e['hourly_rate'] }}</td>
                <td class="total_hours">{{ e['total_hours'] }}</td>
                <td class="text-end">
                  <div class="d-inline-flex gap-2">
                    <!-- Edit button -->
                    <button
                      type="button"
                      class="btn btn-sm btn-outline-secondary"
                      data-bs-toggle="modal"
                      data-bs-target="#editModal"
                      data-id="{{ e['id'] }}"
                      data-employee_id="{{ e['employee_id'] }}"
                      data-name="{{ e['name'] }}"
                      data-phone="{{ e['phone'] }}"
                      data-hourly_rate="{{ e['hourly_rate'] }}"
                    >Edit</button>

                    <!-- Delete form -->
                    <form method="POST" action="{{ url_for('index') }}" onsubmit="return confirm('Delete this employee?')">
                      <input type="hidden" name="id" value="{{ e['id'] }}">
                      <input type="hidden" name="action" value="delete">
                      <button class="btn btn-sm btn-outline-danger">Delete</button>
                    </form>

                    <!-- Clock in/out form -->
                    <form method="POST" action="{{ url_for('clock') }}" class="d-inline-flex gap-1">
                      <input type="hidden" name="employee_id" value="{{ e['employee_id'] }}">
                      <button type="submit" name="action" value="clock_in" class="btn btn-sm btn-success">Clock In</button>
                      <button type="submit" name="action" value="clock_out" class="btn btn-sm btn-warning">Clock Out</button>
                    </form>
                  </div>
                </td>
              </tr>
              {% endfor %}
              {% if not employees %}
              <tr><td colspan="7" class="text-center text-secondary py-4">No employees found.</td></tr>
              {% endif %}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <nav aria-label="Employees pagination" class="d-flex justify-content-between align-items-center">
        <div class="text-secondary small">
          Page <strong>{{ page }}</strong> of <strong>{{ pages }}</strong> · {{ total }} total
        </div>
        <ul class="pagination mb-0">
          <li class="page-item {% if not has_prev %}disabled{% endif %}">
            <a class="page-link" href="{{ url_for('index', page=page-1, per=per_page) if has_prev else '#' }}">Previous</a>
          </li>
          {% for p in range(start_page, end_page + 1) %}
            <li class="page-item {% if p==page %}active{% endif %}">
              <a class="page-link" href="{{ url_for('index', page=p, per=per_page) }}">{{ p }}</a>
            </li>
          {% endfor %}
          <li class="page-item {% if not has_next %}disabled{% endif %}">
            <a class="page-link" href="{{ url_for('index', page=page+1, per=per_page) if has_next else '#' }}">Next</a>
          </li>
        </ul>
      </nav>

      <footer class="py-4 text-center text-secondary small">
        &copy; {{ 2025 }} Austin Shaw
      </footer>
    </div>

    <!-- Edit Modal -->
    <div class="modal fade" id="editModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <form method="POST" action="{{ url_for('index') }}" class="modal-content">
          <input type="hidden" name="action" value="update">
          <input type="hidden" name="id" id="edit-id">
          <div class="modal-header">
            <h5 class="modal-title">Edit Employee</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body row g-3">
            <div class="col-6">
              <label class="form-label">Employee ID</label>
              <input class="form-control" name="employee_id" id="edit-employee_id" required>
            </div>
            <div class="col-6">
              <label class="form-label">Name</label>
              <input class="form-control" name="name" id="edit-name" required>
            </div>
            <div class="col-6">
              <label class="form-label">Phone</label>
              <input class="form-control" name="phone" id="edit-phone" required
                     pattern="^[0-9()+\\-\\s]+$" title="Digits, spaces, (), - and + only">
            </div>
            <div class="col-6">
              <label class="form-label">Hourly Rate</label>
              <input type="number" step="0.01" class="form-control" name="hourly_rate" id="edit-hourly_rate" required>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Cancel</button>
            <button class="btn btn-primary" type="submit">Save changes</button>
          </div>
        </form>
      </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
      // Prefill edit modal with employee data
      const editModal = document.getElementById('editModal')
      editModal.addEventListener('show.bs.modal', event => {
        const button = event.relatedTarget
        document.getElementById('edit-id').value = button.getAttribute('data-id')
        document.getElementById('edit-employee_id').value = button.getAttribute('data-employee_id')
        document.getElementById('edit-name').value = button.getAttribute('data-name')
        document.getElementById('edit-phone').value = button.getAttribute('data-phone')
        document.getElementById('edit-hourly_rate').value = button.getAttribute('data-hourly_rate')
      })
    </script>
  </body>
</html>
