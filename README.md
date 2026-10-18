# Todo API

A small REST API for a personal todo list. It uses FastAPI and stores todos in SQLite. The Kubernetes setup runs one API pod and keeps the database file on a persistent volume.

## Run it locally

You need Python 3.12 or newer.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

The API is at `http://localhost:8000`; its interactive docs are at `/docs`. By default, SQLite writes to `./data/todos.db`. Set `TODO_DB_PATH` to use another file.

Run the checks with:

```sh
pytest -q
ruff check app tests
ruff format --check app tests
pip-audit -r requirements-dev.txt
```

## Endpoints

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/todos` | List todos |
| `POST` | `/todos` | Add a todo, for example `{"title":"Read the guide"}` |
| `GET` | `/todos/{id}` | Get one todo |
| `PATCH` | `/todos/{id}` | Change its title or completion state |
| `DELETE` | `/todos/{id}` | Delete it |
| `GET` | `/health/live` | Check that the process is responding |
| `GET` | `/health/ready` | Check that SQLite can be reached |
| `GET` | `/metrics` | Read Prometheus request counts and durations |

There is no login or user separation. Keep the API on your machine or inside a private cluster; it is not ready for public access.
