from typing import Dict, Any
from .base import BaseAuthBackend
from .local_jwt import LocalJWTBackend

class SchoolDirectoryBackend(BaseAuthBackend):
    """
    Option B - Future Placeholder
    Placeholder for Active Directory/SSO environments.
    Authenticates users via the school system but delegates token 
    verification locally to maintain the X-User-ID downstream contract.
    """
    def __init__(self):
        # Wraps the local JWT backend for token verification post-login
        self._local_validator = LocalJWTBackend()

    def verify_token(self, token: str) -> Dict[str, Any]:
        return self._local_validator.verify_token(token)
