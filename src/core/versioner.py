"""
Gestion des versions pour TakeOutBack.
Versionnement des fichiers avec conservation de l'historique.
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.core.database import Database, get_database
from src.utils.path import get_archive_path
from src.utils.logger import get_logger


class Versioner:
    """Gère le versionnement des fichiers."""

    def __init__(self, database: Optional[Database] = None):
        self.db = database or get_database()
        self.logger = get_logger()
        self.archive_path = get_archive_path()

    def get_version_filename(self, filename: str, version: int) -> str:
        """Génère le nom de fichier avec le numéro de version."""
        if version <= 1:
            return filename
        else:
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            return f"{stem}_v{version}{suffix}"

    def get_versioned_path(self, logical_path: str, version: int) -> str:
        """Génère le chemin versionné d'un fichier."""
        path_obj = Path(logical_path)
        versioned_name = self.get_version_filename(path_obj.name, version)
        return str(path_obj.parent / versioned_name)

    def create_versioned_file(
        self,
        source_path: Path,
        logical_path: str,
        version: int,
        destination_dir: Optional[Path] = None,
    ) -> Path:
        """Crée une copie versionnée d'un fichier."""
        if destination_dir is None:
            destination_dir = self.archive_path / "raw"

        versioned_name = self.get_version_filename(Path(logical_path).name, version)
        target_path = destination_dir / Path(logical_path).parent / versioned_name

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if source_path.exists():
            shutil.copy2(source_path, target_path)
            self.logger.debug(f"Version {version} créée: {target_path}")
        else:
            self.logger.warning(f"Fichier source introuvable: {source_path}")

        return target_path

    def get_file_versions(
        self, logical_path: str
    ) -> List[Dict[str, Any]]:
        """Récupère toutes les versions d'un fichier."""
        file_info = self.db.get_file_by_path(logical_path)
        if not file_info:
            return []

        return self.db.get_all_versions(file_info["id"])

    def get_current_version(self, logical_path: str) -> Optional[Dict[str, Any]]:
        """Récupère la version actuelle d'un fichier."""
        file_info = self.db.get_file_by_path(logical_path)
        if not file_info:
            return None

        return self.db.get_current_version(file_info["id"])

    def get_version_by_number(
        self, logical_path: str, version: int
    ) -> Optional[Dict[str, Any]]:
        """Récupère une version spécifique d'un fichier."""
        file_info = self.db.get_file_by_path(logical_path)
        if not file_info:
            return None

        versions = self.db.get_all_versions(file_info["id"])
        for v in versions:
            if v["version"] == version:
                return v

        return None

    def delete_old_versions(
        self, logical_path: str, max_versions: int = 10
    ) -> int:
        """Supprime les anciennes versions au-delà du maximum."""
        versions = self.get_file_versions(logical_path)
        if len(versions) <= max_versions:
            return 0

        # Supprimer les versions les plus anciennes (sauf la version actuelle)
        deleted_count = 0
        for v in versions[:-1]:  # Exclure la dernière (courante)
            if v["version"] <= len(versions) - max_versions:
                # Marquer comme supprimée
                self.db.execute(
                    "UPDATE versions SET status = 'deleted' WHERE id = ?",
                    (v["id"],)
                )
                deleted_count += 1

        return deleted_count

    def restore_version(
        self,
        logical_path: str,
        version: int,
        destination_path: Path,
    ) -> bool:
        """Restaure une version spécifique d'un fichier."""
        version_info = self.get_version_by_number(logical_path, version)
        if not version_info:
            self.logger.error(f"Version {version} non trouvée pour {logical_path}")
            return False

        # Créer le dossier de destination
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        # Copier le fichier depuis l'archive
        source_path = Path(version_info["archive_path"])
        if source_path.exists():
            shutil.copy2(source_path, destination_path)
            self.logger.info(f"Version {version} restaurée: {destination_path}")
            return True
        else:
            self.logger.error(f"Fichier source introuvable: {source_path}")
            return False

    def get_version_history(
        self, logical_path: str
    ) -> List[Dict[str, Any]]:
        """Retourne l'historique complet d'un fichier."""
        versions = self.get_file_versions(logical_path)
        history = []

        for v in versions:
            history.append({
                "version": v["version"],
                "size": v["size"],
                "discovered_at": v["discovered_at"],
                "status": v["status"],
                "is_current": v["is_current"],
            })

        return history

    def get_all_versioned_files(self) -> List[Dict[str, Any]]:
        """Retourne tous les fichiers avec leur version actuelle."""
        return self.db.fetch_all(
            """
            SELECT f.*, v.version, v.archive_path as version_archive,
                   v.logical_path as version_path
            FROM files f
            JOIN versions v ON f.id = v.file_id AND v.is_current = 1
            ORDER BY f.discovery_date DESC
            """
        )

    def compact_versions(self, max_versions: int = 10) -> int:
        """Compacte les versions en gardant seulement les plus récentes."""
        total_deleted = 0

        # Récupérer tous les fichiers
        all_files = self.db.fetch_all(
            "SELECT id, logical_path FROM files"
        )

        for file_info in all_files:
            deleted = self.delete_old_versions(
                file_info["logical_path"], max_versions
            )
            total_deleted += deleted

        self.logger.info(f"Compactage terminé: {total_deleted} anciennes versions supprimées")
        return total_deleted
