"""
Indexation et recherche pour TakeOutBack.
Moteur de recherche rapide pour des millions de fichiers.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.core.database import Database, get_database
from src.utils.logger import get_logger


class SearchEngine:
    """Moteur de recherche pour TakeOutBack."""

    def __init__(self, database: Optional[Database] = None):
        self.db = database or get_database()
        self.logger = get_logger()

    def search_by_name(
        self,
        filename: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Recherche par nom de fichier."""
        return self.db.search_files(
            filename=filename,
            limit=limit,
            offset=offset,
        )

    def search_by_extension(
        self,
        extension: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Recherche par extension."""
        return self.db.search_files(
            extension=extension.lstrip("."),
            limit=limit,
            offset=offset,
        )

    def search_by_path(
        self,
        path: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Recherche par chemin."""
        return self.db.search_files(
            path=path,
            limit=limit,
            offset=offset,
        )

    def search_by_date(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Recherche par date."""
        return self.db.search_files(
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )

    def search_by_hash(
        self,
        sha256: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Recherche par hash SHA256."""
        return self.db.search_files(
            sha256=sha256,
            limit=limit,
            offset=offset,
        )

    def search_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Recherche par statut."""
        return self.db.search_files(
            status=status,
            limit=limit,
            offset=offset,
        )

    def advanced_search(
        self,
        filename: Optional[str] = None,
        extension: Optional[str] = None,
        path: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sha256: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Recherche avancée avec plusieurs filtres."""
        return self.db.search_files(
            filename=filename,
            extension=extension,
            path=path,
            date_from=date_from,
            date_to=date_to,
            sha256=sha256,
            status=status,
            limit=limit,
            offset=offset,
        )

    def get_file_details(self, logical_path: str) -> Optional[Dict[str, Any]]:
        """Récupère les détails complets d'un fichier."""
        file_info = self.db.get_file_by_path(logical_path)
        if not file_info:
            return None

        # Récupérer les versions
        versions = self.db.get_all_versions(file_info["id"])

        return {
            **file_info,
            "versions": versions,
            "version_count": len(versions),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de recherche."""
        return self.db.get_statistics()

    def rebuild_index(self) -> bool:
        """Reconstruit l'index de recherche."""
        try:
            self.db.execute("VACUUM")
            self.logger.info("Index reconstruit avec succès")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la reconstruction de l'index: {e}")
            return False

    def optimize_performance(self) -> bool:
        """Optimise les performances de la base de données."""
        try:
            # Vider les fichiers temporaires
            self.db.execute("PRAGMA temp_store = MEMORY")
            self.db.execute("PRAGMA cache_size = -64000")  # 64 MB cache

            # Rebuild les index
            self.db.execute("REINDEX")

            self.logger.info("Optimisation de la base de données terminée")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation: {e}")
            return False
