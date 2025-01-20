# Example Event API

A FastAPI-based service for processing transactions and detecting suspicious patterns.

## Features

- Concurrent transaction handling with distributed locking
- Configurable rules
- RESTful API with OpenAPI documentation
- Health check endpoint for monitoring

## Requirements

- Python 3.10 or higher
- Redis (using FakeRedis for development)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Angry-Orangutan/example-event-api.git
cd example-event-api
```

2. Install dependencies:
```bash
make install-prod  # Installs production dependencies only
make install-dev   # Installs development dependencies
# Or install both:
make install      # Installs both production and development dependencies
```

## Running the Service

Start the service:
```bash
make run  # Starts the service on port 5000
```

The API will be available at:
- API: http://127.0.0.1:5000
- Documentation: http://127.0.0.1:5000/docs
- Alternative docs: http://127.0.0.1:5000/redoc
- Health check: http://127.0.0.1:5000/health

## Development

### Code Style and Linting

Format and lint the code:
```bash
make format  # Runs ruff and mypy
```

### Testing

Run the test suite:
```bash
make test  # Runs all tests
```

Or run specific test suites:
```bash
make test-unit     # Unit tests only
make test-int      # Integration tests only
make test-e2e      # End-to-end tests only
```

### Development Commands

The following utility commands are available:

```bash
make clean         # Clean up cache and compiled files
make format        # Run code formatting and type checking
make clear-state   # Clear the service state
make send-event    # Send a sample event to the API
```

### Rule Testing Commands

Test specific rule implementations with pre-configured events:

```bash
make trigger-rule-30    # Test Rule 30 (three consecutive withdrawals)
make trigger-rule-123   # Test Rule 123 (high volume deposits)
make trigger-rule-300   # Test Rule 300 (increasing deposits)
make trigger-rule-1100  # Test Rule 1100 (large withdrawal)
```

### Project Structure

- `app/`: Main application code
  - `models/`: Data models and validation
  - `routers/`: API route handlers
  - `services/`: Business logic and services
- `tests/`: Test suites
  - `unit/`: Unit tests
  - `integration/`: Integration tests
  - `e2e/`: End-to-end tests

## API Documentation

### Endpoints

#### POST /event
Process a transaction event and check for suspicious patterns.

Request body:
```json
{
  "type": "deposit|withdraw",
  "amount": "42.00",
  "user_id": 1,
  "t": 0
}
```

Response:
```json
{
  "alert_codes": [30, 300],
  "user_id": 1,
  "alert": true
}
```

#### GET /health
Check service health status.

Response:
```json
{
  "status": "OK"
}
```

### Rules

The service implements the following rules:

1. **Rule 30**: Alert on three consecutive withdrawals
2. **Rule 123**: Alert when total deposits exceed £200 in a 30-second window
3. **Rule 300**: Alert on pattern of increasing deposit amounts
4. **Rule 1100**: Alert on withdrawals over £100

## License

MIT License
