import sys
import os
from pathlib import Path

# Add backend/jargon/ to sys.path so service-relative imports work
# (e.g. `from routes.simplify import ...`, `from main import app`)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

# Jargon service reads OLLAMA_BASE_URL / OLLAMA_MODEL at module import time
# and has no load_dotenv() of its own. Load from the service's .env so tests use
# the real configured values (gemma3:4b). If a required var is missing, the import
# fails clearly.
load_dotenv(Path(__file__).parent.parent / ".env", override=True)
