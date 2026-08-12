# Django Todo Tutorial

A first Django project: personal todos, a monthly calendar, search and filters, user accounts, a small blog, and a REST API.

## Features

- Sign up, log in, log out, and edit your profile
- Create todos with a title, optional notes, and start/end dates
- Calendar view with date-range todos and click-to-add popups
- Search, status/date filters, sorting, and pagination
- Auto-complete todos after their end date passes
- Magazine-style blog
- Token-authenticated REST API for auth, todos, and posts

## Setup

Use Python 3.12+ and a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

Create a superuser for `/admin/` if you want:

```bash
python manage.py createsuperuser
```

## Pages

| URL | Description |
| --- | --- |
| `/` | Home dashboard |
| `/about/` | About the app |
| `/signup/` `/login/` `/logout/` | Accounts |
| `/profile/` | Profile and password |
| `/calendar/` | Monthly planner |
| `/search/` | Search and filters |
| `/edit-todos/` | Edit, complete, or delete |
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

Your todos only. Fields include `title`, `notes`, `completed`, `start_date`, and `end_date`.  
Search `q` matches title or notes. Also supports `status`, `when`, `sort`, and `page`.

| Method | URL |
| --- | --- |
| `GET` `POST` | `/api/todos/` |
| `GET` `PATCH` `PUT` `DELETE` | `/api/todos/<id>/` |

`status`: `all` · `pending` · `completed`  
`when`: `all` · `today` · `week` · `month` · `upcoming` · `undated`  
`sort`: `status` · `newest` · `oldest` · `title` · `start`

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

## Tests

```bash
python manage.py test
```

## Project layout

```text
config/          Django project settings and root URLs
todos/           Todo app, templates, and todo API viewset
blog/            Blog app and post API viewset
api/             REST API auth views and URL routes
```
