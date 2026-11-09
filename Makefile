.PHONY: install install-dev test smoke run ui site validate clean lint

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest -q

smoke:
	python -m investment_agent.cli run --mock --max-components 3

run:
	python -m investment_agent.cli run

ui:
	streamlit run streamlit_app.py

lint:
	ruff check src tests scripts

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

site:
	python scripts/export_demo_data.py

validate:
	python scripts/validate_site_data.py
