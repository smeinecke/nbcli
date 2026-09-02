# Makefile

.PHONY: all format reformat-ruff check fix-ruff fix test integration-test validate \
	complexity xenon bandit vulture pyright \
	docker-build docker-build-no-cache docker-run docker-compose-up docker-compose-down docker-test

# Default target: runs validation
all: validate

# Format the code using ruff
format:
	ruff format --check --diff .

reformat-ruff:
	ruff format .

# Check the code using ruff
check:
	ruff check .

fix-ruff:
	ruff check . --fix

fix: reformat-ruff fix-ruff
	@echo "Updated code."

# Cyclomatic complexity
complexity:
	radon cc nbcli/ -a -nc -i "build,venv,.venv,dist"

# Maintainability / complexity gate
xenon:
	xenon -b D -m B -a B nbcli/ -i "build,venv,.venv,dist,tests"

# Security linter
bandit:
	bandit -c pyproject.toml -r nbcli/

# Dead code detection
vulture:
	vulture nbcli/ .vulture-whitelist.py \
		--ignore-names "banner1,dont_write_bytecode,kw_string,res_string" \
		--min-confidence 70

# Type checking
pyright:
	pyright

# Unit tests with coverage
test:
	pytest tests/unit -v --cov --cov-report=xml --cov-report=term-missing

# Integration tests
integration-test:
	pytest tests/integration -v --tb=short

# Validate the code (format + check + complexity/security/type tools)
validate: format check complexity bandit vulture pyright
	@echo "Validation passed. Your code is ready to push."

# Docker build targets
docker-build:
	docker build -t nbcli:local .

docker-build-no-cache:
	docker build --no-cache -t nbcli:local .

docker-run:
	docker run -it nbcli:local

docker-compose-up:
	docker compose up --build

docker-compose-down:
	docker compose down

docker-test: docker-build
	@echo "Testing Docker image..."
	@docker run --rm nbcli:local python -m nbcli --help
	@echo "Docker image test passed!"
