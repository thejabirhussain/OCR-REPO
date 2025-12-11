#!/bin/bash
# Run test suite

set -e

echo "Running backend tests..."

cd backend
pytest -v --cov=app --cov-report=html

echo "Tests completed!"




