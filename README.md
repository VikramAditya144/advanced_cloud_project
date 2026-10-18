# Plain Todo API

A small FastAPI service for creating, listing, updating, and deleting todos. SQLite keeps the project easy to run locally; a mounted volume stores data in Kubernetes.

## Run locally

Requires Python 3.11 or newer.

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the interactive API. The database defaults to `./data/todos.db`; set `TODO_DB_PATH` to change it. Run `pytest -q` and `ruff check app tests` to check the API and style.

## API

- `GET /todos` lists todos.
- `POST /todos` with `{"title":"Read the project guide"}` creates one.
- `GET /todos/{id}` reads one.
- `PATCH /todos/{id}` with `{"completed":true}` or `{"title":"New title"}` updates one.
- `DELETE /todos/{id}` deletes one.
- `GET /health/live` and `/health/ready` report process and database health.
- `GET /metrics` exposes Prometheus request counts and latency.

The service binds to port 8000. It has no authentication and is intended for a private learning environment, not direct public exposure.
