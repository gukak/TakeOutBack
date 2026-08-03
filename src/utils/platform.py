"""
Abstraction multi-plateforme pour TakeOutBack.
Gère les différences entre Windows et Linux.
"""
import os
import sys
from pathlib import Path
from typing import Optional


def is_windows() -> bool:
    """Retourne True si le système est Windows."""
    return sys.platform == "win32"


def is_linux() -> bool:
    """Retourne True si le système est Linux."""
    return sys.platform == "linux"


def get_path_separator() -> str:
    """Retourne le séparateur de chemins."""
    return "\\" if is_windows() else "/"


def normalize_path(path: Path) -> Path:
    """Normalise un chemin pour la plateforme actuelle."""
    return Path(str(path).replace("/", get_path_separator()))


def sanitize_filename(filename: str) -> str:
    """Nettoie un nom de fichier pour la compatibilité multi-plateforme."""
    # Caractères interdits sous Windows
    forbidden_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in forbidden_chars:
        filename = filename.replace(char, "_")
    # Remplacer les espaces en début/fin
    filename = filename.strip()
    return filename


def check_case_sensitivity(base_path: Path) -> bool:
    """Vérifie si le système de fichiers est sensible à la casse."""
    test_file = base_path / "TestFile_Case_Sensitivity_Check"
    try:
        test_file.touch()
        # Vérifier si le fichier existe avec une casse différente
        return not (base_path / "testfile_case_sensitivity_check").exists()
    except Exception:
        return True
    finally:
        if test_file.exists():
            test_file.unlink()


def get_file_permissions(file_path: Path) -> Optional[str]:
    """Retourne les permissions d'un fichier."""
    try:
        if is_windows():
            return "N/A (Windows)"
        else:
            import stat
            mode = os.stat(file_path).st_mode
            return stat.filemode(mode)
    except Exception:
        return None


def set_file_permissions(file_path: Path, permissions: str) -> None:
    """Définit les permissions d'un fichier."""
    try:
        if not is_windows():
            import stat
            perm_map = {
                "r": stat.S_IRUSR,
                "w": stat.S_IWUSR,
                "x": stat.S_IXUSR,
            }
            mode = 0
            for char, perm in perm_map.items():
                if char in permissions:
                    mode |= perm
            os.chmod(file_path, mode)
    except Exception as e:
        print(f"Erreur lors du changement des permissions: {e}")


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


def is_removable_drive(path: Path) -> bool:
    """Vérifie si un chemin est sur un disque amovible."""
    try:
        if is_windows():
            # Sous Windows, vérifier si c'est un lecteur amovible
            drive = str(path).split(":")[0] + ":"
            import ctypes
            return ctypes.windll.kernel32.GetDriveTypeW(drive) == 2  # REMOVABLE
        else:
            # Sous Linux, vérifier si c'est un périphérique amovible
            device = os.statvfs(str(path))
            return bool(device.f_flag & 0x80000000)  # ST_RDONLY
    except Exception:
        return False
