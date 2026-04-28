ROOT   := $(shell pwd)
PYTEST := $(ROOT)/backend/.venv/bin/pytest

.PHONY: test-all test-fast test-rag test-gateway test-ferpa \
        test-jargon test-summarizer test-ai

# Central targets run from backend/ so pytest finds pytest.ini and uses testpaths.
# testpaths only covers shared/tests, gateway/tests, rag/tests — services with
# service-relative imports (jargon, summarizer) get isolated sessions below.

test-all: ## Run all tests except those requiring a live Ollama model
	cd backend && $(PYTEST) -m "not ai" -q --tb=short
	cd backend/jargon && $(PYTEST) tests/ -m "not ai" -q --tb=short
	cd backend/summarizer && $(PYTEST) tests/ -m "not ai" -q --tb=short

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
