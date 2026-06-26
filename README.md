# SalonTrack — Employee Attendance Management System

A Django-based web application for managing employee attendance, leaves, and holidays in a salon or small business environment. 
It provides role-based access for admins and employees, automatic attendance status calculation, leave request workflows, and calendar/report views.

---

## Features

**Admin**
- Add, edit, and manage employees (profile photo, salary, status)
- Mark and manage daily attendance
- Approve or reject leave requests
- Configure holidays and working Sundays
- View attendance reports and dashboard analytics

**Employee (Self-Service)**
- Check in / check out to record attendance
- View personal attendance history and calendar
- Apply for leave (Sick, Casual, Annual, Emergency, Unpaid)
- View leave status and profile

**Attendance Rules**
| Condition | Status |
| Check-in ≤ 10:00 AM & total hours ≥ 4 | Present |
| Check-in > 10:00 AM | Late |
| Total hours < 4 | Half Day |
| No check-in | Absent |

---

## Tech Stack

- **Backend:** Python / Django 5.0.6
- **Database:** SQLite (default; swap for PostgreSQL in production)
- **Storage:** Pillow for image handling (profile photos)
- **Server:** Gunicorn (production), WhiteNoise (static files)
- **Frontend:** HTML templates with Bootstrap (via base template)

---

## Project Structure

```
salontrack/
├── attendance/               # Main Django app
│   ├── models.py             # Employee, Attendance, LeaveRequest, Holiday, SundayException
│   ├── views.py              # All business logic and views
│   ├── forms.py              # Django forms
│   ├── urls.py               # URL routing
│   ├── admin.py              # Admin site configuration
│   └── templates/attendance/ # HTML templates
│       ├── dashboard.html
│       ├── employee_list.html
│       ├── employee_detail.html
│       ├── attendance_list.html
│       ├── my_calendar.html
│       ├── leave_list.html
│       ├── reports.html
│       └── ...
├── salontrack_project/       # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/
│   └── base.html             # Shared base layout
├── static/                   # CSS / JS assets
├── media/                    # Uploaded files (profile photos)
├── manage.py
├── requirements.txt
└── Procfile                  # For deployment (e.g. Heroku)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/salontrack.git
cd salontrack



# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py makemigrations attendance
python manage.py migrate

# 4. Create a superuser (Admin account)
python manage.py createsuperuser

# 5. Start the development server
python manage.py runserver
```

Open your browser at **http://127.0.0.1:8000**

---

## Default Login Credentials

| Role | Username | Password |
|---|---|---|
| Admin | *(your superuser)* | *(set during createsuperuser)* |
| Employee | Email prefix (e.g. `john` for `john@salon.com`) | `salon@123` |

---

## Adding Employees

1. Log in as admin
2. Navigate to **Employees → Add Employee**
3. Fill in the employee details and save
4. The employee can immediately log in using their email prefix as the username and `salon@123` as the default password

---

## Data Models

| Model | Description |
|---|---|
| `Employee` | Staff profile: ID, name, email, phone, salary, status, photo |
| `Attendance` | Daily record: check-in/out times, total hours, status |
| `LeaveRequest` | Leave applications with type, dates, reason, and approval status |
| `Holiday` | Public/company holidays (excluded from attendance) |
| `SundayException` | Specific Sundays marked as working days |

---

## Deployment

The project includes a `Procfile` for platforms like Heroku or Railway:

```
web: gunicorn salontrack_project.wsgi --log-file -
```

**Before deploying to production:**

1. Set `DEBUG = False` in `settings.py`
2. Add your domain to `ALLOWED_HOSTS`
3. Set a strong `SECRET_KEY` via an environment variable
4. Configure a production database (e.g. PostgreSQL)
5. Run `python manage.py collectstatic`

---

## Dependencies

```
Django==5.0.6
Pillow==10.4.0
gunicorn==21.2.0
whitenoise==6.6.0
```

---

## License

This project is open source. Feel free to use and adapt it for your own business needs.

## Developed By

**Raj Popatani**

B.tech in Computer Science&Engineering

Python & Django Developer
