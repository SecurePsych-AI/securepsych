import os
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

    # Allow env var overrides for service URLs — required for Docker deployment
    # where services communicate via container names instead of localhost.
    services = config_data.get("services", {})
    for env_var, key in (
        ("RAG_SERVICE_URL", "rag_url"),
        ("SUMMARIZER_SERVICE_URL", "summarizer_url"),
        ("JARGON_SERVICE_URL", "jargon_url"),
    ):
        val = os.environ.get(env_var)
        if val:
            services[key] = val
    config_data["services"] = services

    settings = Settings(**config_data)

    from urllib.parse import urlparse
    _env = os.environ.get("SECUREPSYCH_ENV", "")
    for service_name, url in settings.services.model_dump().items():
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        is_local = hostname in ("localhost", "127.0.0.1")
        # Docker bridge network: single-label hostnames (no dots) are container names
        # on an isolated internal network — not external internet addresses.
        is_docker_container = _env == "docker" and "." not in hostname
        if parsed.scheme != "http" or not (is_local or is_docker_container):
            raise RuntimeError(
                f"FERPA Violation: {service_name} must route to a local or Docker-internal "
                f"service via http://. Got: {url}"
            )

    return settings

settings = load_settings()
