import sys
import os

# Add backend/summarizer/ to sys.path so service-relative imports work
# (e.g. `from main import app`)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# summarizer services read OLLAMA_BASE_URL / OLLAMA_MODEL at import time;
# set defaults so unit tests that mock the chain can import without Ollama running.
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("OLLAMA_MODEL", "llama3.2")
