"""
Gestion des chemins portables pour TakeOutBack.
Tous les chemins sont relatifs au dossier racine du projet.
"""
import os
import sys
from pathlib import Path
from typing import Optional


def get_root_path() -> Path:
    """Retourne le chemin racine du projet TakeOutBack (dossier parent de src/)."""
    return Path(__file__).parent.parent.parent.resolve()


def get_data_path() -> Path:
    """Retourne le chemin racine des données (dossier parent de TakeOutBack/)."""
    return get_root_path().parent.resolve()


def get_tools_path(os_name: Optional[str] = None) -> Path:
    """Retourne le chemin vers le dossier Tools/."""
    if os_name is None:
        os_name = detect_os()
    return get_root_path() / "tools" / os_name


def get_incoming_path() -> Path:
    """Retourne le chemin vers le dossier Incoming/ (à côté de TakeOutBack/)."""
    return get_data_path() / "Incoming"


def get_archive_path() -> Path:
    """Retourne le chemin vers le dossier Archive/ (à côté de TakeOutBack/)."""
    return get_data_path() / "Archive"


def get_database_path() -> Path:
    """Retourne le chemin vers le dossier Database/."""
    return get_root_path() / "database"


def get_config_path() -> Path:
    """Retourne le chemin vers le dossier Config/."""
    return get_root_path() / "config"


def get_logs_path() -> Path:
    """Retourne le chemin vers le dossier Logs/."""
    return get_root_path() / "logs"


def get_reports_path() -> Path:
    """Retourne le chemin vers le dossier Reports/."""
    return get_root_path() / "reports"


def get_temp_path() -> Path:
    """Retourne le chemin vers le dossier Temp/."""
    return get_root_path() / "temp"


def get_state_path() -> Path:
    """Retourne le chemin vers le dossier State/."""
    return get_root_path() / "state"


def detect_os() -> str:
    """Détecte le système d'exploitation (windows ou linux)."""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "linux":
        return "linux"
    else:
        raise OSError(f"Système d'exploitation non supporté: {sys.platform}")


def get_python_binary() -> Path:
    """Retourne le chemin vers le Python portable."""
    os_name = detect_os()
    python_dir = get_tools_path(os_name) / "python"
    if os_name == "windows":
        return python_dir / "python.exe"
    else:
        return python_dir / "python3"


def get_7zip_binary() -> Path:
    """Retourne le chemin vers le 7-Zip portable."""
    os_name = detect_os()
    sevenzip_dir = get_tools_path(os_name) / "7zip"
    if os_name == "windows":
        return sevenzip_dir / "7zz.exe"
    else:
        return sevenzip_dir / "7zz"


def ensure_directory(path: Path) -> None:
    """Crée un dossier s'il n'existe pas."""
    path.mkdir(parents=True, exist_ok=True)
