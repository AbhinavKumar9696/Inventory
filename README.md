# Inventory Management Backend

FastAPI-based backend for inventory management with JWT auth, role-based access control, PostgreSQL persistence, Redis caching, and Celery background jobs.

## Current Status

The project is currently organized as a layered backend:

- `app/api/v1/` exposes HTTP routes
- `app/core/` handles config, security, dependency injection, logging, and app exceptions
- `app/db/` manages SQLAlchemy sessions, Redis client setup, and default admin seeding
- `app/repositories/` encapsulates database access
- `app/services/` contains business logic
- `app/tasks/` contains Celery configuration and async jobs
- `tests/` contains service-layer unit tests with mocked dependencies

Implemented capabilities include:

- JWT login using OAuth2 password form
- role-based authorization for `admin`, `manager`, and `staff`
- user registration and lookup
- inventory item listing, creation, retrieval, and update
- stock in/out movement tracking
- Redis-backed item caching
- low-stock background alert dispatch through Celery
- default admin seeding on startup

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 async ORM
- PostgreSQL
- Alembic
- Redis
- Celery
- Poetry
- Pytest + pytest-asyncio
- Docker + Docker Compose

## Project Structure

```text
.
|-- alembic/
|-- app/
|   |-- api/v1/
|   |-- core/
|   |-- db/
|   |-- models/
|   |-- repositories/
|   |-- schemas/
|   |-- services/
|   `-- tasks/
|-- tests/
|-- celery_worker.py
|-- docker-compose.yml
|-- Dockerfile
|-- pyproject.toml
|-- .env.example
`-- PROJECT_FILES_GUIDE.md
```

## Requirements

Recommended path:

- Docker Desktop or Docker Engine with Compose

Local path:

- Python 3.12+
- Poetry 1.8+
- PostgreSQL
- Redis

## Configuration

Copy the example environment file:

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Important settings used by the app:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `DEFAULT_ADMIN_EMAIL`
- `DEFAULT_ADMIN_PASSWORD`

The app loads settings from `.env` via `pydantic-settings`.

## Run with Docker

Start the API, worker, PostgreSQL, and Redis:

```bash
docker compose up --build -d
```

Apply migrations:

```bash
docker compose exec api alembic upgrade head
```

Open:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/api/v1/health`

Stop services:

```bash
docker compose down
```

Reset database and Redis volumes:

```bash
docker compose down -v
```

## Run Locally

Make sure PostgreSQL and Redis are running and your `.env` points to them.

Install dependencies:

```bash
poetry install
```

Apply migrations:

```bash
poetry run alembic upgrade head
```

Start the API:

```bash
poetry run uvicorn app.main:app --reload
```

Start the Celery worker in another terminal:

```bash
poetry run celery -A celery_worker.celery_app worker --loglevel=INFO
```

## Startup Behavior

On application startup:

- Redis connectivity is checked
- a database session is opened
- a default admin user is created if it does not already exist

The default admin credentials come from:

- `DEFAULT_ADMIN_EMAIL`
- `DEFAULT_ADMIN_PASSWORD`

## Authentication

Authentication uses bearer tokens, not server-side login sessions.

- Login endpoint: `POST /api/v1/auth/login`
- Content type: OAuth2 password form
- `username` field should contain the user email
- `password` field should contain the user password
- Use the returned token as `Authorization: Bearer <token>`

User registration is protected and requires an authenticated `admin` or `manager`.

## API Overview

Base prefix: `/api/v1`

Health:

- `GET /health`

Authentication:

- `POST /auth/register`
- `POST /auth/login`

Users:

- `GET /users/me`
- `GET /users/`
- `GET /users/{user_id}`
- `DELETE /users/{user_id}?full_name=...`

Items:

- `GET /items/`
- `POST /items/`
- `GET /items/{item_id}`
- `PATCH /items/{item_id}`

Inventory:

- `POST /inventory/movements`
- `GET /inventory/items/total-quantity`
- `GET /inventory/items/{item_id}/movements`

## Background Jobs

Celery is configured in `app/tasks/celery_app.py`.

The current background task is:

- `send_low_stock_alert`

Right now that task logs a warning when stock falls to or below the reorder level.

## Testing

The current test suite is focused on fast unit tests for the service layer.

What is covered:

- `AuthService`
- `UserService`
- `ItemService`
- `InventoryService`

How tests work:

- repositories are replaced with `AsyncMock`
- Redis is mocked
- service methods are called directly
- business rules and side effects are asserted

Run tests:

```bash
poetry run pytest -q
```

Current scope of testing:

- unit tests only
- no real PostgreSQL or Redis usage
- no API integration tests yet
- no end-to-end HTTP flow tests yet

## Useful Commands

Format and lint:

```bash
poetry run ruff check .
```

Type check:

```bash
poetry run mypy app
```

Create a new migration:

```bash
poetry run alembic revision --autogenerate -m "describe change"
```

## Troubleshooting

- If `pytest` fails with missing modules such as `redis` or `jose`, run it through Poetry so the project environment is used: `poetry run pytest -q`
- If Docker services start but the schema is missing, run `docker compose exec api alembic upgrade head`
- If port `8000` is already in use, change the API port mapping in `docker-compose.yml`
- If you want a clean local reset in Docker, use `docker compose down -v`

## Production Notes

- change `JWT_SECRET_KEY` before any real deployment
- use managed PostgreSQL and Redis where possible
- place the API behind TLS and a reverse proxy
- add monitoring, metrics, and centralized logging

## Additional Documentation

For a file-by-file walkthrough of the repository, see `PROJECT_FILES_GUIDE.md`.
