# Django Todo Tutorial

A first Django project: personal todos, a monthly calendar, search and filters, user accounts, a small blog, and a REST API.

## Features

- Sign up, log in, log out, and edit your profile
- Create todos with a title, optional notes, start/end dates, and recurrence
- Priorities (low/medium/high) and tags (work, personal, health, learning, errands)
- Subtasks / checklist items on each todo
- Soft archive (keeps history) plus optional permanent delete
- Due-soon reminders on Home for tasks ending today or tomorrow
- Activity dashboard with weekly chart, streak, and completion history
- Recurring tasks (daily, weekly, monthly, yearly) spawn the next occurrence when completed
- Calendar shows repeating todos on every matching day, including future months
- Search, status/date/priority/tag filters, sorting, and pagination
- Auto-complete todos after their end date passes
- Magazine-style blog
- Token-authenticated REST API for auth, todos, tags, and posts

## How to run

### Prerequisites

- **Python 3.12+**
- **pip** (usually included with Python)
- A terminal in the project root (`djangotutorial/`)

### 1. Get the project

```bash
cd djangotutorial
```

If you cloned the repo, `cd` into the folder where `manage.py` lives.

### 2. Create and activate a virtual environment

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

You should see `(.venv)` at the start of your terminal prompt.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the database

The app uses SQLite by default (`db.sqlite3` in the project root). Create the tables with:

```bash
python manage.py migrate
```

### 5. Start the development server

```bash
python manage.py runserver
```

You should see output like:

```text
Starting development server at http://127.0.0.1:8000/
```

Open the app in your browser:

- **Web app:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **API:** [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

To use a different port:

```bash
python manage.py runserver 8080
```

Then visit [http://127.0.0.1:8080/](http://127.0.0.1:8080/).

### 6. Create an account

1. Go to [http://127.0.0.1:8000/signup/](http://127.0.0.1:8000/signup/) and register, **or**
2. Create a superuser for the Django admin:

```bash
python manage.py createsuperuser
```

Then log in at [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/) or `/admin/`.

### 7. Stop the server

In the terminal where `runserver` is running, press **Ctrl+C**.

To run again later:

```bash
source .venv/bin/activate   # or Windows equivalent
python manage.py runserver
```

### Run tests

```bash
python manage.py test
```

### Troubleshooting

| Problem | What to try |
| --- | --- |
| `python: command not found` | Use `python3` instead of `python` |
| `No module named django` | Activate the virtual environment and run `pip install -r requirements.txt` |
| Port already in use | Run on another port: `python manage.py runserver 8080` |
| Database errors after pulling changes | Run `python manage.py migrate` again |

## Pages

| URL | Description |
| --- | --- |
| `/` | Home dashboard |
| `/about/` | About the app |
| `/signup/` `/login/` `/logout/` | Accounts |
| `/profile/` | Profile and password |
| `/calendar/` | Monthly planner |
| `/search/` | Search and filters |
| `/activity/` | Completions, streak, due soon |
| `/edit-todos/` | Edit, complete, archive, or restore |
| `/blog/` | Blog list and posts |
| `/api/` | REST API |

## REST API

Browsable API: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

### Auth

| Method | URL | Notes |
| --- | --- | --- |
| `POST` | `/api/auth/signup/` | `{ "username", "password", "email?" }` |
| `POST` | `/api/auth/login/` | returns `{ "token", "user" }` |
| `POST` | `/api/auth/logout/` | requires token |
| `GET` / `PATCH` | `/api/auth/me/` | current user |

Send the token on later requests:

```http
Authorization: Token YOUR_TOKEN
```

### Todos

Your todos only. Fields include `title`, `notes`, `completed`, `priority`, `tag_slugs`, `subtasks`, `archived`, `start_date`, `end_date`, `recurrence`, and `recurrence_until`.  
`priority`: `low` · `medium` · `high`.  
`recurrence`: `""` (none) · `daily` · `weekly` · `monthly` · `yearly`. Completing a recurring todo creates the next occurrence.  
`DELETE /api/todos/<id>/` archives. Use `POST .../restore/` or `POST .../purge/` to restore or hard-delete.  
`GET /api/tags/` lists available tags.  
Search `q` matches title, notes, tags, or subtasks. Also supports `status`, `when`, `sort`, `priority`, `tag`, `archived=1`, and `page`.

| Method | URL |
| --- | --- |
| `GET` `POST` | `/api/todos/` |
| `GET` `PATCH` `PUT` `DELETE` | `/api/todos/<id>/` |

`status`: `all` · `pending` · `completed`  
`when`: `all` · `today` · `week` · `month` · `upcoming` · `undated` · `due_soon`  
`sort`: `status` · `newest` · `oldest` · `title` · `start` · `priority`  
`priority`: `all` · `low` · `medium` · `high`  
`tag`: tag slug such as `work` or `personal`

### Blog

Public, read-only.

| Method | URL |
| --- | --- |
| `GET` | `/api/posts/` |
| `GET` | `/api/posts/<slug>/` |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "yourname", "password": "yourpassword"}'

curl http://127.0.0.1:8000/api/todos/ \
  -H "Authorization: Token YOUR_TOKEN"
```


## Project layout

```text
config/              Django project settings and root URLs
accounts/            Signup, login, profile, and auth API views
todos/               Todo models, services, views package, and todo API
blog/                Blog app and post API viewset
api/                 REST API root and URL routes
templates/partials/  Shared nav, banner, pagination
static/                Favicon and shared CSS
```
