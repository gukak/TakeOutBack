"""
Gestion de configuration pour TakeOutBack.
Configuration centralisée dans Config/config.json.
"""
import json
from pathlib import Path
from typing import Any, Optional
from src.utils.path import get_config_path


DEFAULT_CONFIG = {
    "encryption": {
        "enabled": False,
        "algorithm": "AES-256",
    },
    "compression": {
        "enabled": True,
        "level": 9,
        "schedule": "nightly",
    },
    "paths": {
        "incoming": "incoming",
        "archive": "archive",
        "database": "database",
        "config": "config",
        "logs": "logs",
        "reports": "reports",
        "temp": "temp",
        "state": "state",
    },
    "logging": {
        "level": "INFO",
        "format": "text",
    },
    "archive": {
        "max_size_gb": 50,
        "strategy": "selective",
    },
    "versioning": {
        "max_versions": 10,
        "strategy": "suffix",
    },
    "hash": {
        "algorithm": "SHA256",
        "strategy": "on_demand",
    },
}


class Config:
    """Classe de gestion de configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or get_config_path() / "config.json"
        self._config = DEFAULT_CONFIG.copy()
        self._load()

    def _load(self) -> None:
        """Charge la configuration depuis le fichier."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                self._config.update(saved_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Erreur lors du chargement de la configuration: {e}")

    def save(self) -> None:
        """Sauvegarde la configuration."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de configuration."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Définit une valeur de configuration."""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()

    def get_all(self) -> dict:
        """Retourne toute la configuration."""
        return self._config.copy()


# Instance globale
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Retourne l'instance globale de configuration."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
