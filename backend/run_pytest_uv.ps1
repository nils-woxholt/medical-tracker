Write-Host "Running pytest inside uv environment (forcing project venv interpreter)..." -ForegroundColor Cyan
uv run python -m pytest
