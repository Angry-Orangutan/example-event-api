.PHONY: install install-dev install-prod run send-event test-unit test-int test-e2e test format clean

install: install-dev install-prod

install-dev:
	pip install -r ./requirements_dev.txt

install-prod:
	pip install -r ./requirements.txt

run:
	fastapi dev app/main.py --port 5000
# python app/main.py 

send-event:
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "deposit", "amount": "42.00", "user_id": 1, "t": 0}'

test-unit:
	pytest tests/unit/

test-int:
	pytest tests/integration/

test-e2e:
	pytest tests/e2e/

test: test-unit test-int test-e2e

format:
	ruff check --fix
	ruff check --select I --fix
	ruff format
	mypy app/

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete