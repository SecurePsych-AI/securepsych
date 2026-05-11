ROOT   := $(shell pwd)
PYTEST := $(ROOT)/backend/.venv/bin/pytest

.PHONY: test-all test-fast test-rag test-gateway test-ferpa \
        test-jargon test-summarizer test-ai test-frontend \
        docker-build docker-up docker-down docker-logs docker-clean \
        dev-start dev-stop lint format help

# Central targets run from backend/ so pytest finds pytest.ini and uses testpaths.
# testpaths only covers shared/tests, gateway/tests, rag/tests — services with
# service-relative imports (jargon, summarizer) get isolated sessions below.

test-all: ## Run all tests (backend + frontend), except live Ollama
	cd backend && $(PYTEST) -m "not ai" -q --tb=short
	cd backend/jargon && $(PYTEST) tests/ -m "not ai" -q --tb=short
	cd backend/summarizer && $(PYTEST) tests/ -m "not ai" -q --tb=short
	cd frontend && npm test -- --run

test-fast: ## Unit tests only — no Ollama, no spaCy model (~fastest)
	cd backend && $(PYTEST) -m "not ai and not requires_spacy" -q --tb=short
	cd backend/jargon && $(PYTEST) tests/ -m "not ai" -q --tb=short
	cd backend/summarizer && $(PYTEST) tests/ -m "not ai" -q --tb=short

test-rag: ## RAG service tests only
	cd backend && $(PYTEST) -m rag -v --tb=short

test-gateway: ## Gateway proxy and auth tests only
	cd backend && $(PYTEST) -m gateway -v --tb=short

test-ferpa: ## FERPA compliance checks — run before every PR
	cd backend && $(PYTEST) -m ferpa -v --tb=short

test-jargon: ## Jargon service tests only (isolated session)
	cd backend/jargon && $(PYTEST) tests/ -v --tb=short

test-summarizer: ## Summarizer service tests only (isolated session)
	cd backend/summarizer && $(PYTEST) tests/ -v --tb=short

test-ai: ## Smoke tests requiring a live Ollama model
	cd backend && $(PYTEST) -m ai -v --tb=short
	cd backend/jargon && $(PYTEST) tests/ -m ai -v --tb=short
	cd backend/summarizer && $(PYTEST) tests/ -m ai -v --tb=short

test-frontend: ## Frontend vitest suite only
	cd frontend && npm test -- --run

# ─── Docker ──────────────────────────────────────────────────────────────────

docker-build: ## Build all Docker images
	docker compose build

docker-up: ## Start all services in Docker (detached)
	docker compose up -d

docker-down: ## Stop and remove Docker containers
	docker compose down

docker-logs: ## Tail logs from all Docker containers
	docker compose logs -f

docker-clean: ## Remove containers, local images, and named volumes
	docker compose down --rmi local --volumes

# ─── Local dev (shell scripts, no Docker) ────────────────────────────────────

dev-start: ## Start all services locally via shell (requires venv + Ollama)
	bash scripts/start.sh

dev-stop: ## Stop all locally running services
	bash scripts/stop.sh

# ─── Code quality ─────────────────────────────────────────────────────────────

lint: ## Check Python formatting and style (black + flake8)
	cd backend && $(ROOT)/backend/.venv/bin/black --check . && $(ROOT)/backend/.venv/bin/flake8 .

format: ## Auto-format Python code with black
	cd backend && $(ROOT)/backend/.venv/bin/black .

# ─── Help ─────────────────────────────────────────────────────────────────────

help: ## List all available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  %-20s %s\n", $$1, $$2}'
