all: format lint mypy test

format:
	poetry run ruff format .

lint:
	poetry run ruff check . --unsafe-fixes --fix

mypy:
	poetry run mypy .

test:
	poetry run pytest -v