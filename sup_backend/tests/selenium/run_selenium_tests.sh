#!/bin/bash
set -e

# Run from any directory — always resolves to sup_backend/
cd "$(dirname "$0")/../.."

echo "==> Installing test dependencies..."
pip install -r tests/selenium/requirements-test.txt -q

echo "==> Running database migrations..."
python manage.py migrate --run-syncdb -q

echo "==> Running Selenium tests..."
pytest tests/selenium/ --tb=short --junitxml=tests/selenium/results.xml "$@"
