"""
Import de exports Google Takeout pour TakeOutBack.
Analyse incrémentale, détection des nouveaux/modifiés/inchangés.
"""
import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from src.core.database import Database, get_database
from src.core.archive import ArchiveAnalyzer, ArchiveError
from src.utils.path import get_incoming_path, get_archive_path
from src.utils.hash import calculate_crc32, calculate_sha256
from src.utils.logger import get_logger, log_operation


class ImportResult:
    """Résultat d'un import."""

    def __init__(self):
        self.new_files: List[str] = []
        self.modified_files: List[str] = []
        self.unchanged_files: List[str] = []
        self.deleted_files: List[str] = []
        self.errors: List[str] = []
        self.total_files: int = 0
        self.total_size: int = 0
        self.duration_seconds: float = 0


class TakeoutImporter:
    """Importe et analyse les exports Google Takeout."""

    def __init__(self, database: Optional[Database] = None):
        self.db = database or get_database()
        self.analyzer = ArchiveAnalyzer()
        self.logger = get_logger()

    def detect_exports(self) -> List[Path]:
        """Détecte les exports Takeout dans le dossier Incoming/."""
        incoming_path = get_incoming_path()
        exports = []

        if not incoming_path.exists():
            self.logger.warning(f"Dossier Incoming/ non trouvé: {incoming_path}")
            return exports

        for item in incoming_path.iterdir():
            if item.is_file():
                if item.suffix.lower() in (".zip", ".7z"):
                    exports.append(item)
                elif item.is_dir():
                    # Vérifier si c'est un dossier Takeout
                    for sub_item in item.iterdir():
                        if sub_item.suffix.lower() in (".zip", ".7z"):
                            exports.append(sub_item)

        return exports

    def analyze_takeout(
        self, takeout_path: Path
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Analyse un export Takeout et retourne les métadonnées."""
        files_info = []
        takeout_id = self._generate_takeout_id(takeout_path)

        try:
            if takeout_path.suffix.lower() == ".zip":
                archive_info = self.analyzer.analyze_zip(takeout_path)
            elif takeout_path.suffix.lower() == ".7z":
                archive_info = self.analyzer.analyze_7z(takeout_path)
            else:
                self.logger.warning(f"Type de fichier non supporté: {takeout_path}")
                return [], takeout_id

            for file_info in archive_info["files"]:
                if not file_info.get("is_dir", False):
                    files_info.append({
                        "logical_path": file_info["filename"],
                        "filename": Path(file_info["filename"]).name,
                        "extension": Path(file_info["filename"]).suffix.lstrip("."),
                        "size": file_info["size"],
                        "crc32": file_info.get("crc32"),
                        "archive_path": str(takeout_path),
                        "takeout_id": takeout_id,
                    })

        except ArchiveError as e:
            self.logger.error(f"Erreur lors de l'analyse de {takeout_path}: {e}")
            raise

        return files_info, takeout_id

    def _generate_takeout_id(self, takeout_path: Path) -> str:
        """Génère un identifiant unique pour un export Takeout."""
        # Utiliser le hash du nom + taille + date de modification
        content = f"{takeout_path.name}:{takeout_path.stat().st_size}:{takeout_path.stat().st_mtime}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def import_takeout(self, takeout_path: Path) -> ImportResult:
        """Importe un export Takeout complet."""
        start_time = datetime.now()
        result = ImportResult()

        self.logger.info(f"Import en cours: {takeout_path}")

        try:
            # Analyser l'export
            files_info, takeout_id = self.analyze_takeout(takeout_path)
            result.total_files = len(files_info)
            result.total_size = sum(f["size"] for f in files_info)

            # Enregistrer l'export
            self.db.execute(
                """INSERT OR REPLACE INTO takeouts
                   (id, name, import_date, file_count, total_size, status)
                   VALUES (?, ?, ?, ?, ?, 'processed')""",
                (
                    takeout_id,
                    takeout_path.name,
                    datetime.now().isoformat(),
                    len(files_info),
                    result.total_size,
                )
            )

            # Traiter chaque fichier
            for file_info in files_info:
                try:
                    self._process_file(file_info, takeout_id)
                except Exception as e:
                    result.errors.append(
                        f"Erreur pour {file_info['logical_path']}: {str(e)}"
                    )

            # Calculer la durée
            end_time = datetime.now()
            result.duration_seconds = (end_time - start_time).total_seconds()

            # Journaliser l'opération
            log_operation(
                operation_type="import",
                details={
                    "takeout_id": takeout_id,
                    "takeout_name": takeout_path.name,
                    "new_files": len(result.new_files),
                    "modified_files": len(result.modified_files),
                    "unchanged_files": len(result.unchanged_files),
                    "errors": len(result.errors),
                    "duration_seconds": result.duration_seconds,
                },
                status="completed" if not result.errors else "completed_with_errors"
            )

        except Exception as e:
            self.logger.error(f"Erreur lors de l'import de {takeout_path}: {e}")
            result.errors.append(f"Erreur d'import: {str(e)}")

        return result

    def _process_file(
        self, file_info: Dict[str, Any], takeout_id: str
    ) -> None:
        """Traite un fichier individuel."""
        logical_path = file_info["logical_path"]
        existing_file = self.db.get_file_by_path(logical_path)

        if existing_file:
            # Fichier existant - vérifier si modifié
            if self._is_file_modified(existing_file, file_info):
                # Fichier modifié - créer une nouvelle version
                self._create_new_version(existing_file, file_info)
                self.logger.debug(f"Fichier modifié: {logical_path}")
            else:
                # Fichier inchangé
                self.logger.debug(f"Fichier inchangé: {logical_path}")
        else:
            # Nouveau fichier
            self._add_new_file(file_info, takeout_id)
            self.logger.debug(f"Nouveau fichier: {logical_path}")

    def _is_file_modified(
        self, existing: Dict[str, Any], new_info: Dict[str, Any]
    ) -> bool:
        """Vérifie si un fichier a été modifié."""
        # Comparaison par ordre de priorité:
        # 1. Taille
        if existing["size"] != new_info["size"]:
            return True

        # 2. CRC32
        if existing.get("crc32") and new_info.get("crc32"):
            if existing["crc32"] != new_info["crc32"]:
                return True

        # 3. SHA256 (dernier recours, calculé si nécessaire)
        if existing.get("sha256") and new_info.get("sha256"):
            if existing["sha256"] != new_info["sha256"]:
                return True

        return False

    def _add_new_file(
        self, file_info: Dict[str, Any], takeout_id: str
    ) -> None:
        """Ajoute un nouveau fichier à la base de données."""
        file_id = self.db.add_file(
            logical_path=file_info["logical_path"],
            filename=file_info["filename"],
            extension=file_info["extension"],
            size=file_info["size"],
            crc32=file_info.get("crc32"),
            archive_path=file_info["archive_path"],
            discovery_date=datetime.now().isoformat(),
            last_observed=datetime.now().isoformat(),
            takeout_id=takeout_id,
            created_at=datetime.now().isoformat(),
        )

        # Ajouter la première version
        self.db.add_version(
            file_id=file_id,
            version=1,
            archive_path=file_info["archive_path"],
            logical_path=file_info["logical_path"],
            size=file_info["size"],
            crc32=file_info.get("crc32"),
            takeout_id=takeout_id,
            discovered_at=datetime.now().isoformat(),
            is_current=True,
        )

    def _create_new_version(
        self, existing_file: Dict[str, Any], new_info: Dict[str, Any]
    ) -> None:
        """Crée une nouvelle version d'un fichier existant."""
        # Récupérer la version actuelle
        current_version = self.db.get_current_version(existing_file["id"])
        next_version = (current_version["version"] if current_version else 0) + 1

        # Mettre à jour le fichier
        self.db.execute(
            """UPDATE files
               SET last_observed = ?, size = ?, crc32 = ?,
                   archive_path = ?, modified_at = ?
               WHERE id = ?""",
            (
                datetime.now().isoformat(),
                new_info["size"],
                new_info.get("crc32"),
                new_info["archive_path"],
                datetime.now().isoformat(),
                existing_file["id"],
            )
        )

        # Ajouter la nouvelle version
        self.db.add_version(
            file_id=existing_file["id"],
            version=next_version,
            archive_path=new_info["archive_path"],
            logical_path=new_info["logical_path"],
            size=new_info["size"],
            crc32=new_info.get("crc32"),
            takeout_id=new_info.get("takeout_id"),
            discovered_at=datetime.now().isoformat(),
            is_current=True,
        )

    def scan_incoming(self) -> ImportResult:
        """Scan le dossier Incoming/ et importe tous les exports trouvés."""
        exports = self.detect_exports()
        combined_result = ImportResult()

        if not exports:
            self.logger.info("Aucun export Takeout trouvé dans Incoming/")
            return combined_result

        self.logger.info(f"{len(exports)} export(s) Takeout détecté(s)")

        for export_path in exports:
            try:
                result = self.import_takeout(export_path)
                combined_result.new_files.extend(result.new_files)
                combined_result.modified_files.extend(result.modified_files)
                combined_result.unchanged_files.extend(result.unchanged_files)
                combined_result.errors.extend(result.errors)
                combined_result.total_files += result.total_files
                combined_result.total_size += result.total_size
                combined_result.duration_seconds += result.duration_seconds
            except Exception as e:
                self.logger.error(f"Erreur lors de l'import de {export_path}: {e}")
                combined_result.errors.append(f"{export_path}: {str(e)}")

        return combined_result
