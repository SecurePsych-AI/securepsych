import sys
import os

# Add backend/jargon/ to sys.path so service-relative imports work
# (e.g. `from routes.simplify import ...`, `from main import app`)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# jargon/services/simplifier.py reads OLLAMA_BASE_URL at import time;
# set a default so unit tests that mock the chain can import without Ollama running.
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("OLLAMA_MODEL", "llama3.2")
