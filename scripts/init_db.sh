#!/bin/bash
# Initialize database with migrations

set -e

echo "Running database migrations..."

cd backend
alembic upgrade head

echo "Database initialized successfully!"

