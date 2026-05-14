.PHONY: install install-dev test smoke run ui clean lint

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
	streamlit run app/streamlit_app.py

lint:
	ruff check src tests app

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
