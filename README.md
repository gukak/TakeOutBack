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
D:/ (racine du disque)
├── TakeOutBack/              # Logiciel
│   ├── src/                  # Code source
│   ├── tools/                # Outils portables (Python, 7-Zip)
│   ├── database/             # Base SQLite
│   ├── config/               # Configuration
│   ├── logs/                 # Journalisation
│   ├── reports/              # Rapports générés
│   └── ...
├── Incoming/                 # Exports Takeout à traiter
│   └── google-takeout-*.zip  # Déposez vos exports ici
└── Archive/                  # Archives compressées
    ├── raw/                  # Fichiers décompressés (accès rapide)
    ├── compressed/           # Archives compressées par lot
    └── deleted/              # Fichiers supprimés conservés
```

## Installation rapide

### Linux

```bash
# Sur le disque externe, installez TakeOutBack
cd /media/votre_disque
curl -fsSL https://raw.githubusercontent.com/gukak/TakeOutBack/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
# Sur le disque externe, installez TakeOutBack
cd D:\
iwr -useb https://raw.githubusercontent.com/gukak/TakeOutBack/main/install.ps1 | iex
```

### Installation manuelle

1. Téléchargez le ZIP depuis [GitHub](https://github.com/gukak/TakeOutBack/archive/refs/heads/main.zip)
2. Décompressez et renommez le dossier en `TakeOutBack`
3. Placez-le à la racine de votre disque externe
4. Créez les dossiers `Incoming/` et `Archive/` à côté de `TakeOutBack/`

## Utilisation

### Lancement

```bash
# Menu interactif
./TakeOutBack.sh

# Mode non interactif
./TakeOutBack.sh import
./TakeOutBack.sh search "photo.jpg"
./TakeOutBack.sh verify
./TakeOutBack.sh stats
```

### Workflow typique

1. Déposez vos exports Google Takeout dans `Incoming/`
2. Lancez `./TakeOutBack.sh import` pour les analyser
3. Recherchez vos fichiers avec `./TakeOutBack.sh search "nom"`
4. Restaurez via le menu interactif ou la ligne de commande
5. Vérifiez l'intégrité avec `./TakeOutBack.sh verify`

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Documentation technique détaillée
- [CHANGELOG.md](CHANGELOG.md) - Historique des versions
