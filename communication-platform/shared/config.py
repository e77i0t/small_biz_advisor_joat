import os
import json
import threading
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from cryptography.fernet import Fernet, InvalidToken

CONFIG_ENV_VAR = "APP_ENV"
DEFAULT_ENV = "dev"
CONFIG_PATHS = {
    "dev": "config.dev.json",
    "staging": "config.staging.json",
    "prod": "config.prod.json",
}

class FeatureFlags(BaseModel):
    enable_new_feature: bool = False
    maintenance_mode: bool = False
    # Add more feature flags as needed

class AppConfig(BaseModel):
    version: str = Field(..., description="Config version")
    db_url: str
    redis_url: str
    rabbitmq_url: str
    api_key: str
    feature_flags: FeatureFlags = FeatureFlags()
    # Add more config fields as needed

    class Config:
        env_prefix = "APP_"
        case_sensitive = False

    @staticmethod
    def decrypt_value(value: str, key: str) -> str:
        if value.startswith("enc:"):
            f = Fernet(key.encode())
            try:
                return f.decrypt(value[4:].encode()).decode()
            except InvalidToken:
                raise ValueError("Invalid encryption key or token for config value")
        return value

# --- Config Loader ---
class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.env = os.getenv(CONFIG_ENV_VAR, DEFAULT_ENV)
        self.config_path = CONFIG_PATHS.get(self.env, CONFIG_PATHS[DEFAULT_ENV])
        self._fernet_key = os.getenv("CONFIG_ENCRYPTION_KEY", "")
        self._config: Optional[AppConfig] = None
        self._version: Optional[str] = None
        self.load_config()
        # Hot-reload stub: integrate watchdog or polling here

    def load_config(self):
        with open(self.config_path) as f:
            raw = json.load(f)
        # Decrypt sensitive values
        if self._fernet_key:
            for k, v in raw.items():
                if isinstance(v, str):
                    raw[k] = AppConfig.decrypt_value(v, self._fernet_key)
        try:
            self._config = AppConfig(**raw)
            self._version = self._config.version
        except ValidationError as e:
            raise RuntimeError(f"Config validation error: {e}")

    @property
    def config(self) -> AppConfig:
        if self._config is None:
            raise RuntimeError("Config not loaded")
        return self._config

    @property
    def version(self) -> str:
        return self._version or ""

    def reload(self):
        self.load_config()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance 