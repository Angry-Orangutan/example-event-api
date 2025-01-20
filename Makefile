.PHONY: install install-dev install-prod run send-event test-unit test-int test-e2e test format clean clear-state trigger-rule-1100 trigger-rule-30 trigger-rule-300 trigger-rule-123

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

clear-state:
	@echo "🧹 Clearing state manager..."
	curl -XPOST http://127.0.0.1:5000/clear -s
	@echo "✨ State cleared\n"

# Rule test commands
trigger-rule-1100:
	@make clear-state
	@echo "\n🚨 Testing Rule 1100 - Large Withdrawal Detection (>£100)"
	@echo "Sending withdrawal of £150.00..."
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "withdraw", "amount": "150.00", "user_id": 1, "t": 0}'
	@echo "\n✅ Rule 1100 test complete\n"
	@make clear-state

trigger-rule-30:
	@make clear-state
	@echo "\n🚨 Testing Rule 30 - Three Consecutive Withdrawals"
	@echo "Sending withdrawal 1/3 (£10.00)..."
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 0}' && \
	echo "Sending withdrawal 2/3 (£20.00)..." && \
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "withdraw", "amount": "20.00", "user_id": 1, "t": 1}' && \
	echo "Sending withdrawal 3/3 (£30.00)..." && \
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "withdraw", "amount": "30.00", "user_id": 1, "t": 2}'
	@echo "\n✅ Rule 30 test complete\n"
	@make clear-state

trigger-rule-300:
	@make clear-state
	@echo "\n🚨 Testing Rule 300 - Three Consecutive Increasing Deposits"
	@echo "Sending deposit 1/3 (£10.00)..."
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "deposit", "amount": "10.00", "user_id": 1, "t": 0}' && \
	echo "Sending deposit 2/3 (£20.00)..." && \
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "deposit", "amount": "20.00", "user_id": 1, "t": 1}' && \
	echo "Sending deposit 3/3 (£30.00)..." && \
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "deposit", "amount": "30.00", "user_id": 1, "t": 2}'
	@echo "\n✅ Rule 300 test complete\n"
	@make clear-state

trigger-rule-123:
	@make clear-state
	@echo "\n🚨 Testing Rule 123 - High Volume Deposits in 30s Window (>£200)"
	@echo "Sending first deposit (£150.00)..."
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "deposit", "amount": "150.00", "user_id": 1, "t": 0}' && \
	echo "Sending second deposit (£60.00)..." && \
	curl -XPOST http://127.0.0.1:5000/event -H 'Content-Type: application/json' -s \
	-d '{"type": "deposit", "amount": "60.00", "user_id": 1, "t": 15}'
	@echo "\n✅ Rule 123 test complete\n"
	@make clear-state