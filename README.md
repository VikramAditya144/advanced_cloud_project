# Advanced Cloud Project

This is my todo-list API for the Advanced DevOps project. I built it with FastAPI and SQLite. It runs as one instance, so I can keep the setup small and avoid running a separate database service.

## Run locally

You need Python 3.12 or newer.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) to try the API. Todos are saved in `./data/todos.db`. Set `TODO_DB_PATH` if you want to use a different location.

To run the project checks:

```sh
pytest -q
ruff check app tests
ruff format --check app tests
pip-audit -r requirements-dev.txt
```

## API

- `GET /todos` lists all todos.
- `POST /todos` adds one. Send `{"title":"Read the project guide"}`.
- `GET /todos/{id}` gets one todo.
- `PATCH /todos/{id}` changes its title or sets `completed` to `true` or `false`.
- `DELETE /todos/{id}` removes it.
- `GET /health/live` checks that the app is responding.
- `GET /health/ready` checks that SQLite is available.
- `GET /metrics` returns Prometheus request counts and durations.

There is no login or user separation, so keep the app on your own machine or inside a private cluster. Don't expose it directly to the internet.
