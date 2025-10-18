# Medical Tracker Backend# Medical Tracker Backend

FastAPI backend for the SaaS Medical Tracker application.FastAPI backend for the SaaS Medical Tracker application.

## Features## Setup

- Daily medication and symptom logging1. Create virtual environment:

- Medication master data management  

- Condition passport and doctor directory```bash

- Feel vs yesterday computationpython -m venv venv

- JWT authentication stubsource venv/bin/activate  # On Windows: venv\Scripts\activate

- Structured logging and metrics```

## Tech Stack1. Install dependencies

- **Framework**: FastAPI```bash

- **Database**: SQLite (development) / PostgreSQL (production)pip install -e ".[dev]"

- **ORM**: SQLModel```

- **Validation**: Pydantic v2

- **Migrations**: Alembic1. Run the application:

- **Testing**: pytest + httpx

- **Linting**: Ruff + mypy```bash

uvicorn app.main:app --reload

## Development Setup```

1. **Python 3.11+ required**## Development

2. **Install dependencies**:- Run tests: `pytest`

   ```bash
   - Run linting: `ruff check .`

   pip install -e ".[dev]"- Run type checking: `mypy .`
   ```

3. **Setup environment**:

   ```bash
   cp ../.env.example .env
   # Edit .env with your settings
   ```

4. **Initialize database**:

   ```bash
   alembic upgrade head
   ```

5. **Run server**:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Documentation

- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Metrics: http://localhost:8000/metrics

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_example.py
```

## Code Quality

```bash
# Lint and format
ruff check .
ruff format .

# Type checking  
mypy .

# Pre-commit hooks
pre-commit run --all-files
```
