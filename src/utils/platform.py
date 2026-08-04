"""
Gestion plateforme pour TakeOutBack (Linux uniquement).

Ce module fournit les utilitaires spécifiques à la plateforme Linux.
Une abstraction future permettra d'étendre le support à d'autres OS.
"""
import os
import sys
from pathlib import Path
from typing import Optional


def check_case_sensitivity(base_path: Path) -> bool:
    """Vérifie si le système de fichiers est sensible à la casse."""
    test_file = base_path / "TestFile_Case_Sensitivity_Check"
    try:
        test_file.touch()
        return not (base_path / "testfile_case_sensitivity_check").exists()
    except Exception:
        return True
    finally:
        if test_file.exists():
            test_file.unlink()


def get_disk_usage(path: Path) -> dict:
    """Retourne l'utilisation disque d'un dossier."""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        return {
            "total": total,
            "used": used,
            "free": free,
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round((used / total) * 100, 2),
        }
    except Exception as e:
        return {"error": str(e)}
