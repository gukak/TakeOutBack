"""
Gestion des outils portables (Python, 7-Zip).
Téléchargement, vérification, mise à jour, rollback.
"""
import hashlib
import json
import platform
import shutil
import subprocess
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from src.utils.path import (
    get_root_path,
    get_tools_path,
    get_temp_path,
    get_config_path,
)
from src.utils.logger import get_logger


class ToolVersion:
    """Représente la version d'un outil portable."""

    def __init__(
        self,
        name: str,
        version: str,
        url: str,
        checksum: str = "",
        checksum_algorithm: str = "sha256",
    ):
        self.name = name
        self.version = version
        self.url = url
        self.checksum = checksum
        self.checksum_algorithm = checksum_algorithm

    def get_url(self) -> str:
        return self.url

    def get_checksum(self) -> str:
        return self.checksum


class ToolManager:
    """Gère les outils portables : détection, téléchargement, mise à jour."""

    KNOWN_TOOLS: Dict[str, ToolVersion] = {
        "python": ToolVersion(
            name="python",
            version="3.13.14",
            url="https://github.com/gukak/TakeOutBack/raw/main/binaries/linux/python/Python-3.13.14.tgz",
            checksum="",
        ),
        "7zip": ToolVersion(
            name="7zip",
            version="23.01",
            url="https://github.com/gukak/TakeOutBack/raw/main/binaries/linux/7zip/7z2301-linux-x64.tar.xz",
            checksum="",
        ),
    }

    def __init__(self):
        self.logger = get_logger()
        self.tools_dir = get_tools_path("linux")
        self.temp_dir = get_temp_path()
        self.version_file = get_config_path() / "version.json"

    def _get_local_archive(self, tool_name: str) -> Optional[Path]:
        """Retourne le chemin de l'archive locale si elle existe."""
        local_dir = get_root_path() / "binaries" / "linux" / tool_name
        if not local_dir.exists():
            return None

        tool_dir = self.LOCAL_BINARIES_DIR / tool_name
        if not tool_dir.exists():
            return None

        # Chercher l'archive correspondante
        for archive in tool_dir.iterdir():
            if archive.suffix in [".zip", ".tgz", ".tar.gz", ".tar.xz", ".7z"]:
                return archive

        return None

    def detect_installed_tools(self) -> Dict[str, Dict[str, Any]]:
        """Détecte les outils portables installés et leurs versions."""
        installed = {}
        tools_base = Path(__file__).parent.parent.parent / "tools"

        for tool_name in ["python", "7zip"]:
            tool_dir = tools_base / "linux" / tool_name
            binary = self._get_tool_binary(tool_dir, tool_name)

            if binary and binary.exists():
                version = self._detect_tool_version(binary, tool_name)
                installed[tool_name] = {
                    "path": str(binary),
                    "version": version,
                    "installed": True,
                }
            else:
                installed[tool_name] = {
                    "path": None,
                    "version": None,
                    "installed": False,
                }

        return installed

    def _get_tool_binary(self, tool_dir: Path, tool_name: str) -> Optional[Path]:
        """Retourne le chemin du binaire d'un outil."""
        if tool_name == "python":
            return tool_dir / "python3"
        elif tool_name == "7zip":
            return tool_dir / "7z"
        return None

    def _detect_tool_version(self, binary: Path, tool_name: str) -> Optional[str]:
        """Détecte la version d'un outil portable."""
        try:
            if tool_name == "python":
                result = subprocess.run(
                    [str(binary), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return result.stdout.strip().replace("Python ", "")
            elif tool_name == "7zip":
                result = subprocess.run(
                    [str(binary), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "7-Zip" in line:
                            parts = line.split()
                            for part in parts:
                                if part[0].isdigit():
                                    return part
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def check_updates(self) -> Dict[str, Dict[str, Any]]:
        """Vérifie les mises à jour disponibles pour chaque outil."""
        installed = self.detect_installed_tools()
        updates = {}

        for tool_name, info in installed.items():
            if tool_name in self.KNOWN_TOOLS:
                known = self.KNOWN_TOOLS[tool_name]
                current_version = info.get("version")
                updates[tool_name] = {
                    "current_version": current_version,
                    "latest_version": known.version,
                    "update_available": current_version != known.version and info["installed"],
                    "url": known.get_url(),
                }

        return updates

    def download_tool(self, tool_name: str) -> bool:
        """Télécharge un outil portable."""
        if tool_name not in self.KNOWN_TOOLS:
            self.logger.error(f"Outil inconnu: {tool_name}")
            return False

        tool = self.KNOWN_TOOLS[tool_name]
        url = tool.get_url()
        expected_checksum = tool.get_checksum()

        self.logger.info(f"Téléchargement de {tool_name} {tool.version}...")

        try:
            temp_file = self.temp_dir / f"{tool_name}_download.tmp"
            urllib.request.urlretrieve(url, temp_file)

            if expected_checksum:
                actual_checksum = self._calculate_checksum(temp_file, tool.checksum_algorithm)
                if actual_checksum != expected_checksum:
                    self.logger.error(
                        f"Checksum invalide pour {tool_name}: "
                        f"attendu={expected_checksum}, obtenu={actual_checksum}"
                    )
                    temp_file.unlink()
                    return False

            self._extract_tool(tool_name, temp_file, tool.version)
            temp_file.unlink()

            self.logger.info(f"{tool_name} {tool.version} installé avec succès")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors du téléchargement de {tool_name}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return False

    def _extract_tool(self, tool_name: str, archive_path: Path, version: str) -> None:
        """Extrait un outil portable."""
        tool_dir = self.tools_dir / tool_name
        tool_dir.mkdir(parents=True, exist_ok=True)

        if tool_name == "python":
            self._extract_python(archive_path, tool_dir)
        elif tool_name == "7zip":
            self._extract_7zip(archive_path, tool_dir)

    def _extract_python(self, archive_path: Path, tool_dir: Path) -> None:
        """Extrait Python portable."""
        import zipfile

        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(tool_dir)
        else:
            subprocess.run(
                ["tar", "xzf", str(archive_path), "-C", str(tool_dir)],
                check=True,
            )

    def _extract_7zip(self, archive_path: Path, tool_dir: Path) -> None:
        """Extrait 7-Zip portable."""
        if archive_path.suffix == ".7z":
            subprocess.run(
                [str(get_tools_path("linux") / "7zip" / "7z"),
                 "x", str(archive_path), f"-o{tool_dir}", "-y"],
                check=True,
            )
        elif archive_path.suffix == ".tar.xz":
            subprocess.run(
                ["tar", "xJf", str(archive_path), "-C", str(tool_dir)],
                check=True,
            )
        else:
            subprocess.run(
                ["tar", "xzf", str(archive_path), "-C", str(tool_dir)],
                check=True,
            )

    def _calculate_checksum(self, file_path: Path, algorithm: str) -> str:
        """Calcule le hash d'un fichier."""
        if algorithm == "sha256":
            sha256 = hashlib.sha256()
        elif algorithm == "sha1":
            sha256 = hashlib.sha1()
        else:
            sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def update_tools(self) -> Dict[str, bool]:
        """Met à jour tous les outils nécessaires."""
        updates = self.check_updates()
        results = {}

        for tool_name, info in updates.items():
            if info["update_available"]:
                self.logger.info(
                    f"Mise à jour disponible pour {tool_name}: "
                    f"{info['current_version']} -> {info['latest_version']}"
                )
                results[tool_name] = self.download_tool(tool_name)
            else:
                results[tool_name] = True

        return results

    def rollback_tool(self, tool_name: str) -> bool:
        """Annule une mise à jour d'outil."""
        backup_dir = self.tools_dir / f"{tool_name}.backup"
        tool_dir = self.tools_dir / tool_name

        if backup_dir.exists():
            if tool_dir.exists():
                shutil.rmtree(tool_dir)
            shutil.move(str(backup_dir), str(tool_dir))
            self.logger.info(f"Rollback réussi pour {tool_name}")
            return True
        else:
            self.logger.error(f"Pas de backup pour {tool_name}")
            return False

    def save_version_info(self, tools_info: Dict[str, Dict[str, Any]]) -> None:
        """Sauvegarde les informations de version dans version.json."""
        version_data = {
            "software_version": "1.0.0",
            "build_date": datetime.now().isoformat(),
            "tools": tools_info,
        }
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.version_file, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=2)

    def verify_tools(self) -> Dict[str, Any]:
        """Vérifie l'état de tous les outils."""
        installed = self.detect_installed_tools()
        results = {
            "all_installed": True,
            "tools": {},
        }

        for tool_name, info in installed.items():
            tool_result = {
                "installed": info["installed"],
                "version": info["version"],
                "path": info["path"],
                "valid": False,
            }

            if info["installed"] and info["version"]:
                tool_result["valid"] = True
            else:
                results["all_installed"] = False

            results["tools"][tool_name] = tool_result

        return results
