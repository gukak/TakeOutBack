"""
Compression périodique pour TakeOutBack.
Compresse les fichiers anciens par lot pour économiser de l'espace disque.
"""
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from src.core.database import Database, get_database
from src.core.archive import ArchiveManager
from src.utils.path import get_archive_path
from src.utils.logger import get_logger


class CompressionConfig:
    """Configuration de compression."""

    def __init__(
        self,
        enabled: bool = True,
        max_size_gb: float = 50.0,
        schedule: str = "nightly",
        compression_level: int = 9,
    ):
        self.enabled = enabled
        self.max_size_gb = max_size_gb
        self.schedule = schedule
        self.compression_level = compression_level


class Compressor:
    """Compresse les fichiers par lot pour économiser de l'espace disque."""

    def __init__(
        self,
        database: Optional[Database] = None,
        config: Optional[CompressionConfig] = None,
    ):
        self.db = database or get_database()
        self.config = config or CompressionConfig()
        self.archive_manager = ArchiveManager()
        self.logger = get_logger()
        self.archive_path = get_archive_path()

    def should_compress(self) -> bool:
        """Vérifie si la compression doit être effectuée."""
        if not self.config.enabled:
            return False

        # Vérifier l'utilisation disque
        disk_usage = self._get_disk_usage()
        if disk_usage["usage_percent"] > 80:
            return True

        return False

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Retourne l'utilisation disque."""
        import shutil
        try:
            total, used, free = shutil.disk_usage(self.archive_path)
            return {
                "total": total,
                "used": used,
                "free": free,
                "usage_percent": round((used / total) * 100, 2),
            }
        except Exception:
            return {"usage_percent": 0}

    def get_compressible_files(
        self, date_threshold: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Récupère les fichiers éligibles à la compression."""
        if date_threshold is None:
            # Compression des fichiers de plus de 30 jours
            date_threshold = datetime.now() - timedelta(days=30)

        threshold_str = date_threshold.isoformat()

        files = self.db.fetch_all(
            """
            SELECT f.*, v.archive_path as version_archive, v.logical_path as version_path
            FROM files f
            JOIN versions v ON f.id = v.file_id AND v.is_current = 1
            WHERE f.last_observed < ?
            AND f.status = 'active'
            ORDER BY f.last_observed ASC
            """,
            (threshold_str,)
        )

        return files

    def compress_files_by_type(
        self, file_type: str, max_files: int = 1000
    ) -> bool:
        """Compresse les fichiers d'un type spécifique par lot."""
        files = self.db.fetch_all(
            """
            SELECT f.*, v.archive_path as version_archive, v.logical_path as version_path
            FROM files f
            JOIN versions v ON f.id = v.file_id AND v.is_current = 1
            WHERE f.extension = ?
            AND f.status = 'active'
            ORDER BY f.last_observed ASC
            LIMIT ?
            """,
            (file_type, max_files)
        )

        if not files:
            self.logger.info(f"Aucun fichier à compresser pour le type: {file_type}")
            return True

        # Créer un groupe de compression
        group_name = f"{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        archive_path = self.archive_path / "compressed" / f"{group_name}.7z"

        # Collecter les fichiers source
        source_files = []
        for file_info in files:
            source_path = Path(file_info["version_archive"])
            if source_path.exists():
                source_files.append(source_path)

        if not source_files:
            self.logger.warning(f"Aucun fichier source trouvé pour {group_name}")
            return False

        # Créer l'archive
        success = self.archive_manager.create_archive(
            source_paths=source_files,
            archive_path=archive_path,
            compression_level=self.config.compression_level,
        )

        if success:
            # Mettre à jour la base de données
            self._update_archive_paths(files, str(archive_path))
            self.logger.info(f"Compression réussie: {group_name} ({len(files)} fichiers)")
        else:
            self.logger.error(f"Échec de la compression: {group_name}")

        return success

    def _update_archive_paths(
        self, files: List[Dict[str, Any]], new_archive_path: str
    ) -> None:
        """Met à jour les chemins d'archive dans la base de données."""
        for file_info in files:
            self.db.execute(
                """UPDATE files
                   SET archive_path = ?
                   WHERE id = ?""",
                (new_archive_path, file_info["id"])
            )

            self.db.execute(
                """UPDATE versions
                   SET archive_path = ?
                   WHERE id = ?""",
                (new_archive_path, file_info["id"])
            )

    def compress_all_pending(self) -> Dict[str, Any]:
        """Compresse tous les fichiers en attente."""
        result = {
            "compressed_groups": 0,
            "total_files": 0,
            "total_size_saved": 0,
            "errors": [],
        }

        if not self.should_compress():
            self.logger.info("Compression non nécessaire actuellement")
            return result

        # Compresser par type de fichier
        file_types = self._get_file_types()
        for file_type in file_types:
            try:
                success = self.compress_files_by_type(file_type)
                if success:
                    result["compressed_groups"] += 1
            except Exception as e:
                result["errors"].append(f"Erreur pour {file_type}: {str(e)}")

        return result

    def _get_file_types(self) -> List[str]:
        """Récupère les types de fichiers à compresser."""
        results = self.db.fetch_all(
            "SELECT DISTINCT extension FROM files WHERE extension IS NOT NULL"
        )
        return [r["extension"] for r in results]

    def verify_compressed_archives(self) -> Dict[str, Any]:
        """Vérifie l'intégrité des archives compressées."""
        result = {
            "verified": 0,
            "failed": 0,
            "errors": [],
        }

        compressed_dir = self.archive_path / "compressed"
        if not compressed_dir.exists():
            return result

        for archive_file in compressed_dir.glob("*.7z"):
            try:
                if self.archive_manager.verify_archive(archive_file):
                    result["verified"] += 1
                else:
                    result["failed"] += 1
                    result["errors"].append(f"Archive corrompue: {archive_file}")
            except Exception as e:
                result["failed"] += 1
                result["errors"].append(f"Erreur vérification {archive_file}: {str(e)}")

        return result
