# TaskFlow - Internal Task Management System

TaskFlow is a Django-based internal task management application with role-based access for Admin and Employee users.

It supports:
- Admin task assignment and tracking
- Employee task status updates
- Admin-only employee account creation
- Role-restricted dashboards and actions

## 1. Current Project Status

- Public employee registration is disabled.
- Only Admin can create employee accounts (from a dedicated Add Employee page).
- Employee login supports both username and email.
- Django development server defaults to `127.0.0.1:8001` when no port is provided.

## 2. Tech Stack

- Python 3.x (tested in this workspace with Python 3.11)
- Django 5.2.x
- SQLite (`db.sqlite3`)
- HTML/CSS templates (no React/Vue build step)

## 3. Project Structure

```text
Task_Manager/
  README.md
  task/
    taskapp/
      manage.py
      db.sqlite3
      taskapp/                  # Project config (settings, urls, wsgi, asgi)
      taskapp1/                 # Core app (models, views, urls, migrations)
      templates/
        taskapp1/               # HTML templates
```

## 4. Setup Instructions

From project root (`Task_Manager`):

### Windows (PowerShell)

```powershell
cd task\taskapp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install django==5.2.5
python manage.py migrate
```

### macOS/Linux

```bash
cd task/taskapp
python3 -m venv .venv
source .venv/bin/activate
pip install django==5.2.5
python manage.py migrate
```

## 5. Create First Admin User (Important)

This project requires a `UserProfile` with role=`admin` for admin login.

### Step A: Create Django user

```powershell
python manage.py createsuperuser
```

### Step B: Set role to admin in `UserProfile`

```powershell
python manage.py shell
```

```python
from django.contrib.auth.models import User
from taskapp1.models import UserProfile

u = User.objects.get(username="your_admin_username")
profile, _ = UserProfile.objects.get_or_create(user=u)
profile.role = "admin"
profile.save()
exit()
```

If admin password needs reset:

```powershell
python manage.py changepassword your_admin_username
```

## 6. Run the Project

Inside `task/taskapp`:

```powershell
python manage.py runserver
```

Because of `manage.py` customization, this starts at:
- `http://127.0.0.1:8001/`

To use another port:

```powershell
python manage.py runserver 127.0.0.1:8000
```

## 7. Role Model and Access Rules

### Admin
- Can log in at `/task-admin/login/`
- Can access admin dashboard and all admin task management pages
- Can add employee accounts from `/task-admin/employees/add/`

### Employee
- Can log in at `/employee/login/` using username or email
- Can access employee dashboard
- Can update only their own assigned tasks

### Public
- Landing page only
- No public employee registration route

## 8. URL Map

### Public / Auth
- `/` -> landing page
- `/task-admin/login/` -> admin login
- `/employee/login/` -> employee login
- `/logout/` -> logout current user

### Admin Routes
- `/task-admin/dashboard/`
- `/task-admin/assign-task/`
- `/task-admin/tasks/`
- `/task-admin/employees/` (view/filter employees)
- `/task-admin/employees/add/` (create employee account)
- `/task-admin/task/<task_id>/edit/`
- `/task-admin/task/<task_id>/delete/`

### Employee Routes
- `/employee/dashboard/`
- `/employee/task/<task_id>/update/`

### Shared (permission-checked)
- `/task/<task_id>/` -> task details

## 9. Core Data Models

### `UserProfile`
- `user` (OneToOne with Django User)
- `role` (`admin` or `employee`)
- `employee_id` (auto-generated for employees: `EMP001`, `EMP002`, ...)
- `phone` (optional)
- `department` (optional)
- `created_at`

### `Task`
- `title`, `description`
- `assigned_to`, `assigned_by`
- `status` (`pending`, `in_progress`, `completed`)
- `priority` (`low`, `medium`, `high`)
- `due_date`, `created_at`, `updated_at`
- Ordered by latest created first

### `TaskUpdate`
- `task`, `updated_by`
- `update_message` (optional short message)
- `comment`
- `previous_status`, `new_status`
- `timestamp`

## 10. Admin Employee Creation Rules

When creating employee from admin page:
- At least one of `username` or `email` is required
- `password` is required
- `password` and `confirm_password` must match
- Username and email must be unique (if provided)
- If username is not provided, system auto-generates one
- Department max length: 50
- Phone max length: 15

## 11. Typical Workflow

1. Admin logs in.
2. Admin creates employee accounts.
3. Admin assigns tasks to employees.
4. Employee logs in with username/email + password.
5. Employee updates task status.
6. Admin monitors progress via dashboard/all tasks/employees views.

## 12. Useful Commands

```powershell
# From task/taskapp
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py changepassword <username>
python manage.py shell
```

## 13. Troubleshooting

### Problem: Wrong project opens on `127.0.0.1:8000`
- Another server is likely running on port 8000.
- This project defaults to `127.0.0.1:8001`.

### Problem: Admin login fails even with correct credentials
- Ensure the user has a `UserProfile` and `role='admin'`.

### Problem: Access denied on admin pages
- You are logged in as non-admin or missing profile role.

### Problem: Template/URL mismatch after pulling updates
- Run:
```powershell
python manage.py check
python manage.py migrate
```

## 14. Notes for Production

Current settings are development defaults:
- `DEBUG = True`
- hardcoded `SECRET_KEY`
- SQLite DB

Before production:
- set `DEBUG=False`
- configure secure secret key via environment variable
- set `ALLOWED_HOSTS`
- move to PostgreSQL/MySQL (recommended)
- serve static files properly

