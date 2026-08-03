"""
Point d'entrée principal de TakeOutBack.
Gère le démarrage, l'initialisation et les commandes CLI.
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.path import (
    get_root_path,
    get_data_path,
    get_python_binary,
    get_7zip_binary,
    detect_os,
    ensure_directory,
)
from src.utils.config import get_config, Config
from src.utils.logger import setup_logger, get_logger
from src.utils.platform import is_windows, is_linux
from src.core.database import Database, get_database
from src.core.importer import TakeoutImporter
from src.core.indexer import SearchEngine
from src.core.versioner import Versioner
from src.core.compressor import Compressor
from src.cli.menu import CLI


def check_portable_tools() -> bool:
    """Vérifie que les outils portables sont présents."""
    python_binary = get_python_binary()
    sevenzip_binary = get_7zip_binary()

    if not python_binary.exists():
        print(f"ERREUR: Python portable introuvable dans {python_binary}")
        print("Exécutez setup.py pour installer les outils portables.")
        return False

    if not sevenzip_binary.exists():
        print(f"ERREUR: 7-Zip portable introuvable dans {sevenzip_binary}")
        print("Exécutez setup.py pour installer les outils portables.")
        return False

    return True


def check_crash_recovery() -> None:
    """Vérifie et récupère après un éventuel crash."""
    try:
        db = get_database()
        recovery_result = db.check_and_recover()
        if recovery_result["recovered"]:
            print("⚠️ Récupération après crash détectée:")
            for step in recovery_result["recovery_steps"]:
                print(f"  - {step}")
            if recovery_result["errors"]:
                for error in recovery_result["errors"]:
                    print(f"  ✗ {error}")
        elif recovery_result["recovery_steps"]:
            print("ℹ️ Vérification post-crash terminée.")
    except Exception as e:
        print(f"ℹ️ Vérification post-crash: {e}")


def run_setup() -> None:
    """Exécute l'installation initiale."""
    logger = setup_logger("setup", json_format=False)
    logger.info("Démarrage de l'installation...")

    # Créer toute l'arborescence
    directories = [
        get_data_path() / "Incoming",
        get_data_path() / "Archive",
        get_data_path() / "Archive" / "raw",
        get_data_path() / "Archive" / "compressed",
        get_data_path() / "Archive" / "deleted",
        get_root_path() / "database",
        get_root_path() / "config",
        get_root_path() / "logs",
        get_root_path() / "reports",
        get_root_path() / "temp",
        get_root_path() / "state",
        get_root_path() / "scripts",
        get_root_path() / "tools" / detect_os() / "python",
        get_root_path() / "tools" / detect_os() / "7zip",
    ]

    for directory in directories:
        ensure_directory(directory)
        logger.info(f"Dossier créé: {directory}")

    # Initialiser la base de données
    db = get_database()
    db.initialize()
    logger.info("Base de données initialisée")

    # Créer le fichier de configuration par défaut
    config = get_config()
    config.save()
    logger.info("Configuration créée")

    # Créer le fichier de version
    version_info = {
        "software_version": "1.0.0",
        "sqlite_schema_version": 1,
        "python_version": "3.11.5",
        "sevenzip_version": "23.01",
        "build_date": datetime.now().isoformat(),
        "last_update": datetime.now().isoformat(),
    }
    version_path = get_root_path() / "config" / "version.json"
    import json
    with open(version_path, "w", encoding="utf-8") as f:
        json.dump(version_info, f, indent=2)
    logger.info("Fichier de version créé")

    logger.info("Installation terminée avec succès!")
    print("\nInstallation terminée!")
    print("Vous pouvez maintenant lancer TakeOutBack avec:")
    print("  python src/main.py")


def run_import() -> None:
    """Exécute l'import de Takeout."""
    logger = get_logger()
    logger.info("Démarrage de l'import...")

    importer = TakeoutImporter()
    result = importer.scan_incoming()

    print(f"\nImport terminé:")
    print(f"  Fichiers traités: {result.total_files}")
    print(f"  Taille totale: {result.total_size:,} octets")
    print(f"  Durée: {result.duration_seconds:.2f} secondes")
    if result.errors:
        print(f"  Erreurs: {len(result.errors)}")


def run_search(query: str) -> None:
    """Exécute une recherche."""
    search_engine = SearchEngine()
    results = search_engine.advanced_search(filename=query)

    print(f"\nRésultats pour '{query}' ({len(results)} fichiers):")
    for i, result in enumerate(results[:20], 1):
        print(f"  {i}. {result['logical_path']} ({result['size']:,} octets)")


def run_verify() -> None:
    """Exécute la vérification d'intégrité avec export de rapport."""
    db = get_database()
    result = db.export_integrity_report()

    if result["database_ok"]:
        print("✓ Base de données intacte")
    else:
        print("✗ Erreurs détectées:")
        for error in result["errors"]:
            print(f"  - {error}")

    if result["warnings"]:
        print("\nAvertissements:")
        for warning in result["warnings"]:
            print(f"  - {warning}")

    # Afficher les statistiques
    stats = result.get("statistics", {})
    print(f"\nStatistiques:")
    print(f"  Fichiers totaux: {stats.get('total_files', 0):,}")
    print(f"  Versions totales: {stats.get('total_versions', 0):,}")
    print(f"  Fichiers actifs: {stats.get('active_files', 0):,}")
    print(f"  Taille totale: {stats.get('total_size', 0):,} octets")

    # Afficher les chemins des rapports générés
    reports = result.get("reports", {})
    if reports.get("json"):
        print(f"\n✓ Rapport JSON: {reports['json']}")
    if reports.get("csv"):
        print(f"✓ Rapport CSV: {reports['csv']}")


def run_stats() -> None:
    """Affiche les statistiques."""
    db = get_database()
    stats = db.get_statistics()

    print(f"\nStatistiques:")
    print(f"  Fichiers totaux: {stats['total_files']:,}")
    print(f"  Versions totales: {stats['total_versions']:,}")
    print(f"  Fichiers actifs: {stats['active_files']:,}")
    print(f"  Taille totale: {stats['total_size']:,} octets")
    print(f"  Exports: {stats['total_takeouts']}")


def run_update_tools() -> None:
    """Met à jour les outils portables."""
    print("\nVérification des mises à jour des outils...")
    from src.core.tools import ToolManager
    manager = ToolManager()

    updates = manager.check_updates()
    for tool_name, info in updates.items():
        status = "⚠️ Mise à jour disponible" if info["update_available"] else "✓ À jour"
        print(f"  {tool_name}: {info['current_version']} → {info['latest_version']} [{status}]")

    # Lancer les mises à jour si disponibles
    for tool_name, info in updates.items():
        if info["update_available"]:
            print(f"\nTéléchargement de {tool_name}...")
            success = manager.download_tool(tool_name)
            if success:
                print(f"✓ {tool_name} mis à jour avec succès")
            else:
                print(f"✗ Échec du téléchargement de {tool_name}")

    results = manager.verify_tools()
    if results["all_installed"]:
        print("\n✓ Tous les outils sont installés et valides.")
    else:
        print("\n✗ Certains outils manquent ou sont invalides.")
        for tool_name, info in results["tools"].items():
            if not info["valid"]:
                print(f"  - {tool_name}: non installé ou version invalide")


def main() -> None:
    """Fonction principale."""
    # Parser les arguments CLI
    parser = argparse.ArgumentParser(
        description="TakeOutBack - Archivage Google Takeout"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Exécuter l'installation initiale",
    )
    parser.add_argument(
        "--import",
        action="store_true",
        dest="do_import",
        help="Importer les exports Takeout",
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Rechercher un fichier",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Vérifier l'intégrité",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Afficher les statistiques",
    )
    parser.add_argument(
        "--update-tools",
        action="store_true",
        help="Mettre à jour les outils portables",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Niveau de log",
    )

    args = parser.parse_args()

    # Configurer le logger
    import logging
    log_level = getattr(logging, args.log_level)
    setup_logger("takeoutback", log_level=log_level)
    logger = get_logger()

    # Vérifier les outils portables
    if not check_portable_tools():
        sys.exit(1)

    # Vérifier la récupération après crash
    check_crash_recovery()

    # Exécuter la commande demandée
    if args.setup:
        run_setup()
    elif args.do_import:
        run_import()
    elif args.search:
        run_search(args.search)
    elif args.verify:
        run_verify()
    elif args.stats:
        run_stats()
    elif args.update_tools:
        run_update_tools()
    else:
        # Lancer l'interface interactive
        cli = CLI()
        cli.run()


if __name__ == "__main__":
    main()
