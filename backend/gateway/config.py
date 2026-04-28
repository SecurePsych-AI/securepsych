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
    
    # FERPA Assertion: ensure all URLs point strictly to localhost.
    for service_name, url in settings.services.model_dump().items():
        if not url.startswith("http://localhost"):
            raise RuntimeError(f"FERPA Violation: Service URL {service_name} must point to 'http://localhost'. Found: {url}")

    return settings

settings = load_settings()
