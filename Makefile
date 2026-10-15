.PHONY: install test dev
install:
	pip install -r requirements-dev.txt
test:
	pytest -q
dev:
	python -m backend.app.main
