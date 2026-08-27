.PHONY: setup lint test generate-mock-data

setup:
	python -m venv venv
	./venv/bin/pip install -e ".[dev]"

lint:
	./venv/bin/ruff check .
	./venv/bin/mypy src/

test:
	./venv/bin/pytest tests/

generate-mock-data:
	./venv/bin/python -m src.mock_data.generator

ingest-local:
	./venv/bin/python -m src.ingest.loader

dbt-run:
	cd dbt_project && ../venv/bin/dbt run --profiles-dir .

dbt-test:
	cd dbt_project && ../venv/bin/dbt test --profiles-dir .
