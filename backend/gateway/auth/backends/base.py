from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAuthBackend(ABC):
    @abstractmethod
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifies the given token and returns the decoded payload.
        Should raise an exception (e.g., ValueError) if invalid.
        Expected payload dict should at least contain a 'sub' (user_id) key.
        """
        pass
