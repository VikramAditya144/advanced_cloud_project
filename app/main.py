"""A small, single-process-friendly Todo API backed by SQLite."""

import os
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, ConfigDict, Field, field_validator

DB_PATH = Path(os.getenv("TODO_DB_PATH", "./data/todos.db"))
REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "path"])


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )""")


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Plain Todo API", version="1.0.0", lifespan=lifespan)


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title cannot be blank")
        return value


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    completed: bool | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("title cannot be blank")
        return value


class Todo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    completed: bool
    created_at: str


def as_todo(row: sqlite3.Row) -> Todo:
    return Todo(id=row["id"], title=row["title"], completed=bool(row["completed"]), created_at=row["created_at"])


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    LATENCY.labels(request.method, path).observe(time.perf_counter() - started)
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    return response


@app.get("/health/live", include_in_schema=False)
def liveness():
    return {"status": "ok"}


@app.get("/health/ready", include_in_schema=False)
def readiness():
    try:
        with connect() as db:
            db.execute("SELECT 1")
        return {"status": "ready"}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/todos", response_model=list[Todo])
def list_todos():
    with connect() as db:
        rows = db.execute("SELECT * FROM todos ORDER BY id").fetchall()
    return [as_todo(row) for row in rows]


@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate):
    with connect() as db:
        cursor = db.execute("INSERT INTO todos (title) VALUES (?)", (payload.title.strip(),))
        row = db.execute("SELECT * FROM todos WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return as_todo(row)


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    with connect() as db:
        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="todo not found")
    return as_todo(row)


@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, payload: TodoUpdate):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="provide title or completed")
    values = {"completed": int(value) if key == "completed" else value for key, value in updates.items()}
    assignments = ", ".join(f"{key} = ?" for key in values)
    with connect() as db:
        cursor = db.execute(f"UPDATE todos SET {assignments} WHERE id = ?", (*values.values(), todo_id))
        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="todo not found")
    return as_todo(row)


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int):
    with connect() as db:
        cursor = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="todo not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
