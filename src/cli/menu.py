"""
Interface CLI interactive pour TakeOutBack.
Menu principal avec toutes les options.
"""
import sys
from typing import Optional
from src.core.database import get_database
from src.core.importer import TakeoutImporter
from src.core.indexer import SearchEngine
from src.core.versioner import Versioner
from src.core.compressor import Compressor
from src.utils.logger import get_logger


class CLI:
    """Interface CLI interactive."""

    def __init__(self):
        self.logger = get_logger()
        self.running = True

    def run(self) -> None:
        """Lance l'interface CLI interactive."""
        self._print_banner()

        while self.running:
            try:
                self._show_menu()
                choice = input("\nChoix [1-10]: ").strip()
                self._handle_choice(choice)
            except KeyboardInterrupt:
                print("\n\nArrêt demandé par l'utilisateur.")
                self.running = False
            except EOFError:
                print("\n\nFin du flux d'entrée.")
                self.running = False
            except Exception as e:
                self.logger.error(f"Erreur: {e}")
                print(f"\nErreur: {e}")
                input("Appuyez sur Entrée pour continuer...")

    def _print_banner(self) -> None:
        """Affiche la bannière du programme."""
        print("=" * 60)
        print("  TakeOutBack - Archivage Google Takeout")
        print("  Application portable d'archivage de l'historique Google")
        print("=" * 60)
        print()

    def _show_menu(self) -> None:
        """Affiche le menu principal."""
        print("\nMenu principal:")
        print("-" * 40)
        print("  1. Initialiser le dépôt")
        print("  2. Analyser de nouveaux Google Takeout")
        print("  3. Rechercher")
        print("  4. Restaurer")
        print("  5. Vérifier l'intégrité")
        print("  6. Afficher les statistiques")
        print("  7. Exporter un inventaire")
        print("  8. Mettre à jour les outils portables")
        print("  9. Paramètres")
        print("  10. Quitter")
        print("-" * 40)

    def _handle_choice(self, choice: str) -> None:
        """Gère le choix de l'utilisateur."""
        if choice == "1":
            self._initialize()
        elif choice == "2":
            self._analyze_takeout()
        elif choice == "3":
            self._search()
        elif choice == "4":
            self._restore()
        elif choice == "5":
            self._verify()
        elif choice == "6":
            self._stats()
        elif choice == "7":
            self._export_inventory()
        elif choice == "8":
            self._update_tools()
        elif choice == "9":
            self._settings()
        elif choice == "10":
            self.running = False
            print("\nAu revoir!")
        else:
            print("\nChoix invalide. Veuillez entrer un nombre de 1 à 10.")

    def _initialize(self) -> None:
        """Initialise le dépôt."""
        print("\nInitialisation du dépôt...")
        db = get_database()
        db.initialize()
        print("Dépôt initialisé avec succès!")

    def _analyze_takeout(self) -> None:
        """Analyse les exports Takeout."""
        print("\nAnalyse des exports Takeout...")
        importer = TakeoutImporter()
        result = importer.scan_incoming()

        print(f"\nRésultats:")
        print(f"  Fichiers traités: {result.total_files}")
        print(f"  Taille totale: {result.total_size:,} octets")
        print(f"  Durée: {result.duration_seconds:.2f} secondes")
        if result.errors:
            print(f"  Erreurs: {len(result.errors)}")

    def _search(self) -> None:
        """Recherche de fichiers."""
        print("\nRecherche de fichiers:")
        print("  1. Par nom")
        print("  2. Par extension")
        print("  3. Par chemin")
        print("  4. Par date")
        print("  5. Par hash")
        print("  6. Recherche avancée")
        print("  7. Retour")

        choice = input("\nChoix [1-7]: ").strip()

        if choice == "1":
            filename = input("Nom du fichier: ").strip()
            self._search_by_name(filename)
        elif choice == "2":
            extension = input("Extension (sans le point): ").strip()
            self._search_by_extension(extension)
        elif choice == "3":
            path = input("Chemin: ").strip()
            self._search_by_path(path)
        elif choice == "4":
            date_from = input("Date début (YYYY-MM-DD): ").strip() or None
            date_to = input("Date fin (YYYY-MM-DD): ").strip() or None
            self._search_by_date(date_from, date_to)
        elif choice == "5":
            sha256 = input("Hash SHA256: ").strip()
            self._search_by_hash(sha256)
        elif choice == "6":
            self._advanced_search()
        elif choice == "7":
            return
        else:
            print("Choix invalide.")

    def _search_by_name(self, filename: str) -> None:
        """Recherche par nom."""
        search_engine = SearchEngine()
        results = search_engine.search_by_name(filename)

        print(f"\nRésultats ({len(results)} fichiers):")
        for i, result in enumerate(results[:10], 1):
            print(f"  {i}. {result['logical_path']} ({result['size']:,} octets)")

    def _search_by_extension(self, extension: str) -> None:
        """Recherche par extension."""
        search_engine = SearchEngine()
        results = search_engine.search_by_extension(extension)

        print(f"\nRésultats ({len(results)} fichiers):")
        for i, result in enumerate(results[:10], 1):
            print(f"  {i}. {result['logical_path']} ({result['size']:,} octets)")

    def _search_by_path(self, path: str) -> None:
        """Recherche par chemin."""
        search_engine = SearchEngine()
        results = search_engine.search_by_path(path)

        print(f"\nRésultats ({len(results)} fichiers):")
        for i, result in enumerate(results[:10], 1):
            print(f"  {i}. {result['logical_path']} ({result['size']:,} octets)")

    def _search_by_date(self, date_from: Optional[str], date_to: Optional[str]) -> None:
        """Recherche par date."""
        search_engine = SearchEngine()
        results = search_engine.search_by_date(date_from, date_to)

        print(f"\nRésultats ({len(results)} fichiers):")
        for i, result in enumerate(results[:10], 1):
            print(f"  {i}. {result['logical_path']} ({result['size']:,} octets)")

    def _search_by_hash(self, sha256: str) -> None:
        """Recherche par hash."""
        search_engine = SearchEngine()
        results = search_engine.search_by_hash(sha256)

        print(f"\nRésultats ({len(results)} fichiers):")
        for i, result in enumerate(results[:10], 1):
            print(f"  {i}. {result['logical_path']} ({result['size']:,} octets)")

    def _advanced_search(self) -> None:
        """Recherche avancée."""
        search_engine = SearchEngine()

        filename = input("Nom (vide pour ignorer): ").strip() or None
        extension = input("Extension (vide pour ignorer): ").strip() or None
        path = input("Chemin (vide pour ignorer): ").strip() or None

        results = search_engine.advanced_search(
            filename=filename,
            extension=extension,
            path=path,
        )

        print(f"\nRésultats ({len(results)} fichiers):")
        for i, result in enumerate(results[:10], 1):
            print(f"  {i}. {result['logical_path']} ({result['size']:,} octets)")

    def _restore(self) -> None:
        """Restauration de fichiers."""
        print("\nRestauration de fichiers:")
        print("  1. Restaurer la dernière version")
        print("  2. Restaurer une version spécifique")
        print("  3. Restaurer un dossier")
        print("  4. Restaurer par filtre (date, extension)")
        print("  5. Retour")

        choice = input("\nChoix [1-5]: ").strip()

        if choice == "1":
            logical_path = input("Chemin du fichier: ").strip()
            destination = input("Destination: ").strip()
            versioner = Versioner()
            success = versioner.restore_version(logical_path, 1, destination)
            if success:
                print(f"Restauration réussie: {destination}")
            else:
                print("Échec de la restauration.")
        elif choice == "2":
            logical_path = input("Chemin du fichier: ").strip()
            version = int(input("Numéro de version: ").strip())
            destination = input("Destination: ").strip()
            versioner = Versioner()
            success = versioner.restore_version(logical_path, version, destination)
            if success:
                print(f"Restauration réussie: {destination}")
            else:
                print("Échec de la restauration.")
        elif choice == "3":
            folder_path = input("Chemin du dossier: ").strip()
            destination = input("Destination: ").strip()
            versioner = Versioner()
            result = versioner.restore_folder(folder_path, destination)
            if result["restored"] > 0:
                print(f"Dossier restauré: {result['restored']} fichiers")
                if result["errors"]:
                    print(f"Erreurs: {len(result['errors'])}")
            else:
                print("Aucun fichier trouvé.")
        elif choice == "4":
            print("\nFiltres de restauration:")
            extension = input("Extension (vide pour ignorer): ").strip() or None
            date_from = input("Date début (YYYY-MM-DD, vide pour ignorer): ").strip() or None
            date_to = input("Date fin (YYYY-MM-DD, vide pour ignorer): ").strip() or None
            destination = input("Destination: ").strip()

            filter_criteria = {
                "extension": extension,
                "date_from": date_from,
                "date_to": date_to,
            }

            versioner = Versioner()
            result = versioner.restore_by_filter(filter_criteria, destination)
            if result["restored"] > 0:
                print(f"Filtre appliqué: {result['restored']} fichiers restaurés")
                if result["errors"]:
                    print(f"Erreurs: {len(result['errors'])}")
            else:
                print("Aucun fichier ne correspond aux filtres.")
        elif choice == "5":
            return
        else:
            print("Choix invalide.")

    def _verify(self) -> None:
        """Vérification d'intégrité avec export de rapport."""
        print("\nVérification de l'intégrité...")
        db = get_database()

        # Vérification complète avec export de rapport
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

        # Vérifier les CRC des archives
        compressor = Compressor()
        archive_result = compressor.verify_compressed_archives()

        print(f"\n✓ Archives vérifiées: {archive_result['verified']}")
        if archive_result["failed"] > 0:
            print(f"✗ Archives corrompues: {archive_result['failed']}")
            for error in archive_result["errors"]:
                print(f"  - {error}")

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

    def _stats(self) -> None:
        """Affichage des statistiques."""
        print("\nStatistiques:")
        db = get_database()
        stats = db.get_statistics()

        print(f"  Fichiers totaux: {stats['total_files']:,}")
        print(f"  Versions totales: {stats['total_versions']:,}")
        print(f"  Fichiers actifs: {stats['active_files']:,}")
        print(f"  Taille totale: {stats['total_size']:,} octets")
        print(f"  Exports: {stats['total_takeouts']}")
        if stats['last_import']:
            print(f"  Dernier import: {stats['last_import']['import_date']}")

    def _export_inventory(self) -> None:
        """Export de l'inventaire."""
        print("\nExport de l'inventaire...")
        # Fonctionnalité en cours de développement
        print("Fonctionnalité en cours de développement.")

    def _update_tools(self) -> None:
        """Mise à jour des outils portables."""
        print("\nVérification des mises à jour des outils...")
        # Fonctionnalité en cours de développement
        print("Fonctionnalité en cours de développement.")

    def _settings(self) -> None:
        """Paramètres."""
        print("\nParamètres:")
        print("  1. Configurer le chiffrement")
        print("  2. Configurer la compression")
        print("  3. Configurer les chemins")
        print("  4. Configurer les logs")
        print("  5. Retour")

        choice = input("\nChoix [1-5]: ").strip()

        if choice in ["1", "2", "3", "4"]:
            print(f"Paramètre {choice} en cours de développement.")
        elif choice == "5":
            return
        else:
            print("Choix invalide.")
