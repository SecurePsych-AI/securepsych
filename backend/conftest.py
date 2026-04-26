import sys
import os

# Add the project root directory (one level up from backend) to the Python path
# This allows pytest to resolve `from backend.module import ...` imports when
# running pytest directly from inside the `backend/` directory.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
