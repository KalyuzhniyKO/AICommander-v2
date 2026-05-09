.PHONY: install dev test smoke

install:
	pip install -r requirements.txt

dev:
	python -m backend.app.main

test:
	pytest

smoke:
	python -m compileall backend
	python -c "import backend.app.main; print('ok')"
