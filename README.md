# TakeOutBack

Application portable d'archivage de l'historique Google Takeout.

## Fonctionnalités

- Archivage incrémental des exports Google Takeout
- Versionnement des fichiers (conservation de toutes les versions)
- Recherche rapide dans des millions de fichiers
- Restauration ciblée de fichiers ou versions spécifiques
- Vérification d'intégrité
- Compression périodique par lot
- Fonctionnement 100% portable (disque externe)
- Compatible Windows et Linux

## Structure

```
TakeOutBack/
├── src/              # Code source
├── tools/            # Outils portables (Python, 7-Zip)
├── incoming/         # Exports Takeout à analyser
├── archive/          # Données archivées
│   ├── raw/          # Fichiers décompressés (accès rapide)
│   ├── compressed/   # Archives compressées par lot
│   └── deleted/      # Fichiers supprimés conservés
├── database/         # Base SQLite
├── config/           # Configuration
├── logs/             # Journalisation
├── reports/          # Rapports générés
├── temp/             # Fichiers temporaires
├── state/            # État de l'application
└── tests/            # Tests unitaires
```

## Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/gukak/TakeOutBack.git
   ```

2. Copier le dossier sur le disque externe

3. Lancer l'installation :
   ```bash
   # Windows
   run.bat --setup

   # Linux
   ./run.sh --setup
   ```

4. Suivre les instructions

## Utilisation

```bash
# Menu interactif
python src/main.py

# Mode non interactif
python src/main.py --import
python src/main.py --verify
python src/main.py --stats
python src/main.py --search "photo.jpg"
```

## Menu interactif

1. Initialiser le dépôt
2. Analyser de nouveaux Google Takeout
3. Rechercher
4. Restaurer
5. Vérifier l'intégrité
6. Afficher les statistiques
7. Exporter un inventaire
8. Mettre à jour les outils portables
9. Paramètres
10. Quitter

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Documentation technique détaillée
- [CHANGELOG.md](CHANGELOG.md) - Historique des versions
- [GUIDE_DEPLOIEMENT.md](GUIDE_DEPLOIEMENT.md) - Guide opérationnel

## Configuration

Tous les paramètres sont dans `Config/config.json` (créé automatiquement lors du premier lancement).

## Outils portables

Le projet utilise des outils portables stockés dans `Tools/` :

- **Python** : 3.11+ (téléchargé automatiquement)
- **7-Zip** : 23.01+ (téléchargé automatiquement)

Aucun outil système n'est utilisé. Le programme fonctionne même sans Python installé sur la machine hôte.

## Licence

À définir.
