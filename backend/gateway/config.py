import yaml
from pathlib import Path
from pydantic import BaseModel

CONFIG_PATH = Path(__file__).parent / "config.yaml"

class FeatureFlags(BaseModel):
    rag_enabled: bool = True
    summarizer_enabled: bool = True
    jargon_enabled: bool = False

class AuthSettings(BaseModel):
    backend: str = "local_jwt"

class ServiceUrls(BaseModel):
    rag_url: str
    summarizer_url: str
    jargon_url: str

class StorageSettings(BaseModel):
    log_dir: str = "/mnt/securepsych/data/gateway"

class Settings(BaseModel):
    features: FeatureFlags
    auth: AuthSettings
    services: ServiceUrls
    storage: StorageSettings

def load_settings() -> Settings:
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Configuration file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r") as f:
        config_data = yaml.safe_load(f) or {}
        
    settings = Settings(**config_data)
    
    from urllib.parse import urlparse
    for service_name, url in settings.services.model_dump().items():
        parsed = urlparse(url)
        if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1"):
            raise RuntimeError(
                f"FERPA Violation: {service_name} must be http://localhost:<port>. Got: {url}"
            )

    return settings

settings = load_settings()
