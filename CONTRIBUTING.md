# Contributing Guidelines

Thank you for your interest in contributing to the Arabic OCR & Translation project!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd OCR-POC
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Download ML models** (first time only)
   ```bash
   docker-compose exec backend python scripts/download_models.py
   ```

## Code Style

### Python
- Follow PEP 8 style guide
- Use type hints for all functions
- Maximum line length: 100 characters
- Use `black` for formatting: `black backend/`
- Use `flake8` for linting: `flake8 backend/`

### TypeScript/React
- Use TypeScript for all new code
- Follow ESLint rules
- Use functional components with hooks
- Maximum line length: 100 characters

## Testing

- Write tests for all new features
- Run tests before submitting PR: `pytest backend/tests`
- Aim for >70% code coverage

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add tests
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request with a clear description

## Reporting Issues

When reporting issues, please include:
- Description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

## Questions?

Feel free to open an issue for questions or discussions.




