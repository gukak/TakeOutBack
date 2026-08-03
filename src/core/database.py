"""
Gestion de la base de données SQLite pour TakeOutBack.
Schéma optimisé pour plusieurs millions de fichiers.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.utils.path import get_database_path
from src.utils.logger import get_logger


SCHEMA_VERSION = 1

CREATE_TABLES_SQL = """
-- Table des fichiers (une entrée par fichier unique dans l'archive)
CREATE TABLE IF NOT EXISTS files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    logical_path    TEXT NOT NULL,
    filename        TEXT NOT NULL,
    extension       TEXT,
    size            INTEGER NOT NULL,
    crc32           INTEGER,
    sha256          TEXT,
    archive_path    TEXT NOT NULL,
    archive_crc     TEXT,
    discovery_date  TEXT NOT NULL,
    last_observed   TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    takeout_id      TEXT,
    metadata_json   TEXT,
    created_at      TEXT NOT NULL,
    modified_at     TEXT
);

-- Table des versions (un fichier peut avoir plusieurs versions)
CREATE TABLE IF NOT EXISTS versions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id         INTEGER NOT NULL REFERENCES files(id),
    version         INTEGER NOT NULL,
    archive_path    TEXT NOT NULL,
    logical_path    TEXT NOT NULL,
    size            INTEGER NOT NULL,
    crc32           INTEGER,
    sha256          TEXT,
    takeout_id      TEXT,
    discovered_at   TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    is_current      BOOLEAN NOT NULL DEFAULT 0,
    UNIQUE(file_id, version)
);

-- Table des exports Takeout
CREATE TABLE IF NOT EXISTS takeouts (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    import_date     TEXT NOT NULL,
    file_count      INTEGER DEFAULT 0,
    total_size      INTEGER DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'processed',
    notes           TEXT
);

-- Table des opérations (journal)
CREATE TABLE IF NOT EXISTS operations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type  TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    duration_seconds REAL,
    files_processed INTEGER DEFAULT 0,
    files_added     INTEGER DEFAULT 0,
    files_modified  INTEGER DEFAULT 0,
    files_deleted   INTEGER DEFAULT 0,
    errors          INTEGER DEFAULT 0,
    details         TEXT,
    status          TEXT NOT NULL DEFAULT 'completed'
);
"""

CREATE_INDEXES_SQL = """
-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_files_logical_path ON files(logical_path);
CREATE INDEX IF NOT EXISTS idx_files_sha256 ON files(sha256);
CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
CREATE INDEX IF NOT EXISTS idx_files_discovery_date ON files(discovery_date);
CREATE INDEX IF NOT EXISTS idx_files_last_observed ON files(last_observed);
CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension);
CREATE INDEX IF NOT EXISTS idx_files_takeout_id ON files(takeout_id);
CREATE INDEX IF NOT EXISTS idx_versions_file_id ON versions(file_id);
CREATE INDEX IF NOT EXISTS idx_versions_is_current ON versions(is_current);
CREATE INDEX IF NOT EXISTS idx_takeouts_import_date ON takeouts(import_date);
CREATE INDEX IF NOT EXISTS idx_operations_timestamp ON operations(timestamp);
CREATE INDEX IF NOT EXISTS idx_operations_type ON operations(operation_type);
"""

CREATE_VIEW_SQL = """
-- Vue pour la recherche rapide (dernière version de chaque fichier)
CREATE VIEW IF NOT EXISTS current_files AS
SELECT f.*, v.archive_path as current_archive, v.logical_path as current_logical_path
FROM files f
JOIN versions v ON f.id = v.file_id AND v.is_current = 1;
"""


class Database:
    """Classe de gestion de la base de données SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_database_path() / "catalogue.db"
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Établit la connexion à la base de données."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False
        )
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute("PRAGMA cache_size=-64000")
        self._connection.execute("PRAGMA temp_store=MEMORY")
        self._connection.execute("PRAGMA mmap_size=268435456")

    def close(self) -> None:
        """Ferme la connexion."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def initialize(self) -> None:
        """Initialise la base de données avec le schéma."""
        if not self._connection:
            self.connect()

        with self._connection:
            self._connection.executescript(CREATE_TABLES_SQL)
            self._connection.executescript(CREATE_INDEXES_SQL)
            self._connection.executescript(CREATE_VIEW_SQL)

            # Mettre à jour la version du schéma
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_info (schema_version INTEGER)"
            )
            self._connection.execute(
                "INSERT OR REPLACE INTO schema_info (schema_version) VALUES (?)",
                (SCHEMA_VERSION,)
            )

        logger = get_logger()
        logger.info(f"Base de données initialisée: {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """Retourne la connexion actuelle."""
        if not self._connection:
            self.connect()
        return self._connection

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Exécute une requête SQL."""
        conn = self.get_connection()
        return conn.execute(query, params)

    def executemany(self, query: str, params_list: List[tuple]) -> None:
        """Exécute une requête avec plusieurs jeux de paramètres."""
        conn = self.get_connection()
        with conn:
            conn.executemany(query, params_list)

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Exécute une requête et retourne tous les résultats."""
        cursor = self.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Exécute une requête et retourne un seul résultat."""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    def add_file(
        self,
        logical_path: str,
        filename: str,
        extension: str,
        size: int,
        crc32: Optional[int] = None,
        sha256: Optional[str] = None,
        archive_path: str = "",
        archive_crc: Optional[str] = None,
        discovery_date: str = "",
        last_observed: str = "",
        status: str = "active",
        takeout_id: Optional[str] = None,
        metadata_json: Optional[str] = None,
        created_at: str = "",
        modified_at: Optional[str] = None,
    ) -> int:
        """Ajoute un fichier à la base de données."""
        conn = self.get_connection()
        with conn:
            cursor = conn.execute(
                """INSERT INTO files 
                   (logical_path, filename, extension, size, crc32, sha256,
                    archive_path, archive_crc, discovery_date, last_observed,
                    status, takeout_id, metadata_json, created_at, modified_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    logical_path, filename, extension, size, crc32, sha256,
                    archive_path, archive_crc, discovery_date, last_observed,
                    status, takeout_id, metadata_json, created_at, modified_at
                )
            )
            return cursor.lastrowid

    def add_version(
        self,
        file_id: int,
        version: int,
        archive_path: str,
        logical_path: str,
        size: int,
        crc32: Optional[int] = None,
        sha256: Optional[str] = None,
        takeout_id: Optional[str] = None,
        discovered_at: str = "",
        status: str = "active",
        is_current: bool = False,
    ) -> int:
        """Ajoute une version d'un fichier."""
        conn = self.get_connection()
        with conn:
            # Désactiver l'ancienne version actuelle
            conn.execute(
                "UPDATE versions SET is_current = 0 WHERE file_id = ? AND is_current = 1",
                (file_id,)
            )

            cursor = conn.execute(
                """INSERT INTO versions
                   (file_id, version, archive_path, logical_path, size, crc32, sha256,
                    takeout_id, discovered_at, status, is_current)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    file_id, version, archive_path, logical_path, size, crc32, sha256,
                    takeout_id, discovered_at, status, is_current
                )
            )
            return cursor.lastrowid

    def get_file_by_path(self, logical_path: str) -> Optional[Dict[str, Any]]:
        """Récupère un fichier par son chemin logique."""
        return self.fetch_one(
            "SELECT * FROM files WHERE logical_path = ?",
            (logical_path,)
        )

    def get_current_version(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Récupère la version actuelle d'un fichier."""
        return self.fetch_one(
            "SELECT * FROM versions WHERE file_id = ? AND is_current = 1",
            (file_id,)
        )

    def get_all_versions(self, file_id: int) -> List[Dict[str, Any]]:
        """Récupère toutes les versions d'un fichier."""
        return self.fetch_all(
            "SELECT * FROM versions WHERE file_id = ? ORDER BY version ASC",
            (file_id,)
        )

    def search_files(
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
        """Recherche de fichiers avec filtres."""
        conditions = []
        params = []

        if filename:
            conditions.append("f.filename LIKE ?")
            params.append(f"%{filename}%")

        if extension:
            conditions.append("f.extension = ?")
            params.append(extension.lstrip("."))

        if path:
            conditions.append("f.logical_path LIKE ?")
            params.append(f"%{path}%")

        if date_from:
            conditions.append("f.discovery_date >= ?")
            params.append(date_from)

        if date_to:
            conditions.append("f.discovery_date <= ?")
            params.append(date_to)

        if sha256:
            conditions.append("f.sha256 = ?")
            params.append(sha256)

        if status:
            conditions.append("f.status = ?")
            params.append(status)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT f.*, v.archive_path as current_archive, v.logical_path as current_logical_path
            FROM files f
            LEFT JOIN versions v ON f.id = v.file_id AND v.is_current = 1
            WHERE {where_clause}
            ORDER BY f.discovery_date DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        return self.fetch_all(query, tuple(params))

    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques de la base de données."""
        stats = {}

        # Nombre total de fichiers
        stats["total_files"] = self.fetch_one(
            "SELECT COUNT(*) as count FROM files"
        )["count"]

        # Nombre total de versions
        stats["total_versions"] = self.fetch_one(
            "SELECT COUNT(*) as count FROM versions"
        )["count"]

        # Nombre de fichiers actifs
        stats["active_files"] = self.fetch_one(
            "SELECT COUNT(*) as count FROM files WHERE status = 'active'"
        )["count"]

        # Taille totale (estimation)
        stats["total_size"] = self.fetch_one(
            "SELECT COALESCE(SUM(size), 0) as total FROM files"
        )["total"]

        # Nombre d'exports
        stats["total_takeouts"] = self.fetch_one(
            "SELECT COUNT(*) as count FROM takeouts"
        )["count"]

        # Dernier import
        stats["last_import"] = self.fetch_one(
            "SELECT import_date FROM takeouts ORDER BY import_date DESC LIMIT 1"
        )

        return stats

    def add_operation(
        self,
        operation_type: str,
        timestamp: str,
        duration_seconds: Optional[float] = None,
        files_processed: int = 0,
        files_added: int = 0,
        files_modified: int = 0,
        files_deleted: int = 0,
        errors: int = 0,
        details: Optional[str] = None,
        status: str = "completed",
    ) -> int:
        """Ajoute une opération au journal."""
        conn = self.get_connection()
        with conn:
            cursor = conn.execute(
                """INSERT INTO operations
                   (operation_type, timestamp, duration_seconds, files_processed,
                    files_added, files_modified, files_deleted, errors, details, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    operation_type, timestamp, duration_seconds, files_processed,
                    files_added, files_modified, files_deleted, errors, details, status
                )
            )
            return cursor.lastrowid

    def verify_integrity(self) -> Dict[str, Any]:
        """Vérifie l'intégrité de la base de données."""
        result = {
            "database_ok": True,
            "errors": [],
            "warnings": [],
        }

        try:
            # Vérifier la structure de la base
            self.execute("PRAGMA integrity_check")
            self.execute("PRAGMA foreign_key_check")

            # Vérifier les index
            indexes = self.fetch_all("PRAGMA index_list(files)")
            if not indexes:
                result["warnings"].append("Aucun index sur la table files")

            indexes = self.fetch_all("PRAGMA index_list(versions)")
            if not indexes:
                result["warnings"].append("Aucun index sur la table versions")

        except sqlite3.DatabaseError as e:
            result["database_ok"] = False
            result["errors"].append(f"Erreur SQLite: {str(e)}")

        return result

    def repair(self) -> bool:
        """Tente de réparer la base de données."""
        try:
            # Créer une nouvelle base
            backup_path = self.db_path.with_suffix(".db.backup")
            backup_path.rename(self.db_path.with_suffix(".db.corrupted"))

            self.initialize()

            logger = get_logger()
            logger.info("Base de données réparée avec succès")
            return True

        except Exception as e:
            logger = get_logger()
            logger.error(f"Échec de la réparation: {e}")
            return False

    def export_integrity_report(
        self,
        report_dir: Optional[Path] = None,
        formats: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Vérifie l'intégrité et exporte un rapport JSON/CSV."""
        import json
        import csv
        from datetime import datetime

        if formats is None:
            formats = ["json", "csv"]
        if report_dir is None:
            from src.utils.path import get_reports_path
            report_dir = get_reports_path()

        report_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"integrity_report_{timestamp}"

        # Exécuter la vérification
        result = self.verify_integrity()

        # Ajouter les statistiques
        stats = self.get_statistics()
        result["statistics"] = stats

        # Ajouter les opérations récentes
        recent_ops = self.fetch_all(
            "SELECT * FROM operations ORDER BY timestamp DESC LIMIT 50"
        )
        result["recent_operations"] = recent_ops

        # Ajouter les fichiers avec erreurs (CRC invalide, etc.)
        file_errors = self.fetch_all(
            """
            SELECT f.logical_path, f.filename, f.extension, f.size,
                   f.crc32, f.sha256, f.archive_path, f.status,
                   f.last_observed
            FROM files f
            WHERE f.status = 'deleted' OR f.crc32 IS NULL
            ORDER BY f.last_observed DESC
            LIMIT 100
            """
        )
        result["file_issues"] = file_errors

        # Exporter en JSON
        json_path = None
        if "json" in formats:
            json_path = report_dir / f"{filename_base}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        # Exporter en CSV
        csv_path = None
        if "csv" in formats:
            csv_path = report_dir / f"{filename_base}.csv"
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "type", "status", "message", "timestamp"
                ])
                # Ligne de statut global
                status = "OK" if result["database_ok"] else "ERREUR"
                writer.writerow(["global", status,
                    "Base de données intacte" if result["database_ok"] else "Erreurs détectées",
                    datetime.now().isoformat()])
                # Erreurs
                for error in result["errors"]:
                    writer.writerow(["error", "ERROR", error,
                        datetime.now().isoformat()])
                # Avertissements
                for warning in result["warnings"]:
                    writer.writerow(["warning", "WARNING", warning,
                        datetime.now().isoformat()])
                # Statistiques
                for key, value in stats.items():
                    if isinstance(value, (int, float, str)):
                        writer.writerow(["stat", key, str(value),
                            datetime.now().isoformat()])

        # Retourner les chemins des rapports
        result["reports"] = {
            "json": str(json_path) if json_path else None,
            "csv": str(csv_path) if csv_path else None,
        }

        return result

    def check_and_recover(self) -> Dict[str, Any]:
        """Vérifie et récupère automatiquement après un crash."""
        result = {
            "recovered": False,
            "recovery_steps": [],
            "errors": [],
        }

        # Vérifier si un journal de transaction existe
        journal_path = self.db_path.with_suffix(".db-journal")
        wal_path = self.db_path.with_suffix(".db-wal")
        shm_path = self.db_path.with_suffix(".db-shm")

        if journal_path.exists() or wal_path.exists():
            result["recovery_steps"].append("Journal de transaction détecté")

            try:
                # Fermer et rouvrir pour forcer la récupération WAL
                self.close()
                self.connect()

                # Vérifier l'intégrité
                integrity = self.fetch_one("PRAGMA integrity_check")
                if integrity and integrity.get("integrity_check") == "ok":
                    result["recovered"] = True
                    result["recovery_steps"].append("Récupération WAL réussie")
                else:
                    result["errors"].append("Intégrité compromise après récupération WAL")

            except Exception as e:
                result["errors"].append(f"Erreur lors de la récupération: {str(e)}")

        # Vérifier les opérations incomplètes
        incomplete_ops = self.fetch_all(
            "SELECT * FROM operations WHERE status = 'in_progress'"
        )
        if incomplete_ops:
            result["recovery_steps"].append(
                f"{len(incomplete_ops)} opération(s) incomplète(s) détectée(s)"
            )
            for op in incomplete_ops:
                self.execute(
                    "UPDATE operations SET status = 'interrupted' WHERE id = ?",
                    (op["id"],)
                )
            result["recovered"] = True

        return result


# Instance globale
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """Retourne l'instance globale de la base de données."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
