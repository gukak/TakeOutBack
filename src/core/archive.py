"""
Gestion des archives ZIP et 7Z pour TakeOutBack.
Analyse sans décompression, extraction sélective.
"""
import zipfile
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from src.utils.path import get_7zip_binary
from src.utils.hash import calculate_crc32, calculate_sha256, verify_file_integrity
from src.utils.logger import get_logger


class ArchiveError(Exception):
    """Erreur liée aux archives."""
    pass


class ArchiveAnalyzer:
    """Analyse les archives ZIP et 7Z sans les décompresser."""

    def __init__(self):
        self.logger = get_logger()

    def is_zip(self, file_path: Path) -> bool:
        """Vérifie si un fichier est une archive ZIP."""
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                zf.testzip()
            return True
        except Exception:
            return False

    def is_7z(self, file_path: Path) -> bool:
        """Vérifie si un fichier est une archive 7Z."""
        try:
            result = subprocess.run(
                [str(get_7zip_binary()), "l", str(file_path)],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False

    def analyze_zip(self, archive_path: Path) -> Dict[str, Any]:
        """Analyse une archive ZIP et retourne ses métadonnées."""
        files_info = []
        total_size = 0
        file_count = 0

        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                for info in zf.infolist():
                    file_info = {
                        "filename": info.filename,
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "crc32": info.CRC,
                        "date_time": info.date_time,
                        "is_dir": info.is_dir(),
                        "comment": info.comment.decode("utf-8") if info.comment else "",
                    }
                    files_info.append(file_info)
                    total_size += info.file_size
                    file_count += 1

                archive_crc = self._calculate_zip_crc(zf)

        except zipfile.BadZipFile as e:
            raise ArchiveError(f"Archive ZIP corrompue: {archive_path} - {e}")
        except Exception as e:
            raise ArchiveError(f"Erreur lors de l'analyse de {archive_path}: {e}")

        return {
            "path": str(archive_path),
            "type": "zip",
            "file_count": file_count,
            "total_size": total_size,
            "archive_crc": archive_crc,
            "files": files_info,
        }

    def analyze_7z(self, archive_path: Path) -> Dict[str, Any]:
        """Analyse une archive 7Z et retourne ses métadonnées."""
        files_info = []
        total_size = 0
        file_count = 0

        try:
            result = subprocess.run(
                [str(get_7zip_binary()), "l", "-slt", str(archive_path)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise ArchiveError(
                    f"Erreur 7z pour {archive_path}: {result.stderr}"
                )

            # Parser la sortie 7z
            current_file = {}
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("Path = "):
                    if current_file:
                        files_info.append(current_file)
                    current_file = {"filename": line[7:]}
                elif line.startswith("Size = "):
                    current_file["size"] = int(line[7:])
                    total_size += int(line[7:])
                elif line.startswith("CRC = "):
                    current_file["crc32"] = int(line[6:], 16)
                elif line.startswith("Method = "):
                    current_file["method"] = line[9:]
                elif line.startswith("Attributes = "):
                    attrs = int(line[13:])
                    current_file["is_dir"] = bool(attrs & 0x10)

            if current_file:
                files_info.append(current_file)

            file_count = len(files_info)

        except subprocess.TimeoutExpired:
            raise ArchiveError(f"Timeout lors de l'analyse de {archive_path}")
        except Exception as e:
            raise ArchiveError(f"Erreur lors de l'analyse de {archive_path}: {e}")

        return {
            "path": str(archive_path),
            "type": "7z",
            "file_count": file_count,
            "total_size": total_size,
            "archive_crc": None,
            "files": files_info,
        }

    def _calculate_zip_crc(self, zf: zipfile.ZipFile) -> Optional[str]:
        """Calcule le CRC32 de l'ensemble de l'archive ZIP."""
        import zlib
        crc = 0
        for info in zf.infolist():
            if not info.is_dir():
                try:
                    data = zf.read(info.filename)
                    crc = zlib.crc32(data, crc)
                except Exception:
                    pass
        return f"{crc & 0xFFFFFFFF:08x}"

    def extract_file(
        self,
        archive_path: Path,
        target_path: Path,
        filename: str,
        algorithm: str = "crc32",
    ) -> bool:
        """Extrait un fichier spécifique d'une archive."""
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if self.is_zip(archive_path):
            return self._extract_from_zip(archive_path, target_path, filename)
        elif self.is_7z(archive_path):
            return self._extract_from_7z(archive_path, target_path, filename)
        else:
            raise ArchiveError(f"Type d'archive non supporté: {archive_path}")

    def _extract_from_zip(
        self, archive_path: Path, target_path: Path, filename: str
    ) -> bool:
        """Extrait un fichier d'une archive ZIP."""
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                if filename not in zf.namelist():
                    raise ArchiveError(f"Fichier non trouvé dans l'archive: {filename}")

                # Extraire le fichier
                with zf.open(filename) as source, open(target_path, "wb") as dest:
                    dest.write(source.read())

                # Vérifier le CRC si demandé
                file_info = zf.getinfo(filename)
                if file_info.CRC:
                    actual_crc = calculate_crc32(target_path)
                    if actual_crc != file_info.CRC:
                        self.logger.warning(
                            f"CRC mismatch pour {filename}: "
                            f"attendu={file_info.CRC:08x}, "
                            f"actuel={actual_crc:08x}"
                        )
                        return False

                return True

        except zipfile.BadZipFile as e:
            raise ArchiveError(f"Archive ZIP corrompue: {e}")

    def _extract_from_7z(
        self, archive_path: Path, target_path: Path, filename: str
    ) -> bool:
        """Extrait un fichier d'une archive 7Z."""
        try:
            result = subprocess.run(
                [
                    str(get_7zip_binary()),
                    "x",
                    f"-o{target_path.parent}",
                    f"-y",
                    str(archive_path),
                    filename,
                ],
                capture_output=True,
                timeout=120
            )

            if result.returncode != 0:
                raise ArchiveError(
                    f"Erreur 7z lors de l'extraction de {filename}: "
                    f"{result.stderr.decode('utf-8', errors='ignore')}"
                )

            return True

        except subprocess.TimeoutExpired:
            raise ArchiveError(f"Timeout lors de l'extraction de {filename}")

    def list_archive_contents(
        self, archive_path: Path, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Liste le contenu d'une archive."""
        if self.is_zip(archive_path):
            return self._list_zip_contents(archive_path, limit)
        elif self.is_7z(archive_path):
            return self._list_7z_contents(archive_path, limit)
        else:
            return []

    def _list_zip_contents(self, archive_path: Path, limit: int) -> List[Dict[str, Any]]:
        """Liste le contenu d'une archive ZIP."""
        contents = []
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                for i, info in enumerate(zf.infolist()):
                    if i >= limit:
                        break
                    contents.append({
                        "filename": info.filename,
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "is_dir": info.is_dir(),
                    })
        except Exception:
            pass
        return contents

    def _list_7z_contents(self, archive_path: Path, limit: int) -> List[Dict[str, Any]]:
        """Liste le contenu d'une archive 7Z."""
        contents = []
        try:
            result = subprocess.run(
                [str(get_7zip_binary()), "l", str(archive_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n")[5:]:  # Skip header
                    line = line.strip()
                    if line and not line.startswith("---"):
                        parts = line.split()
                        if len(parts) >= 4:
                            contents.append({
                                "filename": parts[-1],
                                "size": int(parts[-2]) if parts[-2].isdigit() else 0,
                                "is_dir": parts[0] == "D",
                            })
        except Exception:
            pass
        return contents


class ArchiveManager:
    """Gère les opérations sur les archives (création, vérification, etc.)."""

    def __init__(self):
        self.analyzer = ArchiveAnalyzer()
        self.logger = get_logger()

    def create_archive(
        self,
        source_paths: List[Path],
        archive_path: Path,
        compression_level: int = 9,
    ) -> bool:
        """Crée une archive 7Z à partir de fichiers sources."""
        try:
            archive_path.parent.mkdir(parents=True, exist_ok=True)

            args = [
                str(get_7zip_binary()),
                "a",
                f"-mx={compression_level}",
                str(archive_path),
            ]
            args.extend([str(p) for p in source_paths])

            result = subprocess.run(
                args,
                capture_output=True,
                timeout=3600  # 1 heure max
            )

            if result.returncode != 0:
                self.logger.error(
                    f"Erreur lors de la création de l'archive: {result.stderr.decode()}"
                )
                return False

            return True

        except subprocess.TimeoutExpired:
            self.logger.error("Timeout lors de la création de l'archive")
            return False
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'archive: {e}")
            return False

    def verify_archive(self, archive_path: Path) -> bool:
        """Vérifie l'intégrité d'une archive."""
        if self.analyzer.is_zip(archive_path):
            return self._verify_zip(archive_path)
        elif self.analyzer.is_7z(archive_path):
            return self._verify_7z(archive_path)
        return False

    def _verify_zip(self, archive_path: Path) -> bool:
        """Vérifie l'intégrité d'une archive ZIP."""
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                bad_files = zf.testzip()
                return bad_files is None
        except zipfile.BadZipFile:
            return False

    def _verify_7z(self, archive_path: Path) -> bool:
        """Vérifie l'intégrité d'une archive 7Z."""
        try:
            result = subprocess.run(
                [str(get_7zip_binary()), "t", str(archive_path)],
                capture_output=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_archive_info(self, archive_path: Path) -> Optional[Dict[str, Any]]:
        """Retourne les informations d'une archive."""
        if self.analyzer.is_zip(archive_path):
            return self.analyzer.analyze_zip(archive_path)
        elif self.analyzer.is_7z(archive_path):
            return self.analyzer.analyze_7z(archive_path)
        return None
