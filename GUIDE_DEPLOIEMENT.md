# Guide de déploiement TakeOutBack

## Prérequis

- Disque dur externe (exFAT recommandé)
- Espace disque : 2x la taille des données à archiver
- Python 3.10+ (portable, fourni avec le projet)
- 7-Zip 23.01+ (portable, fourni avec le projet)

## Installation sur disque externe

1. Brancher le disque externe
2. Copier le dossier `TakeOutBack/` sur le disque
3. Lancer l'installation :
   ```bash
   # Windows
   run.bat --setup

   # Linux
   ./run.sh --setup
   ```
4. Suivre les instructions à l'écran

## Structure du disque

```
Disque externe/
└── TakeOutBack/
    ├── setup.py          # Installation initiale
    ├── main.py           # Point d'entrée principal
    ├── run.bat / run.sh  # Scripts de lancement
    ├── src/              # Code source
    ├── tools/            # Outils portables
    ├── incoming/         # Exports Takeout à analyser
    ├── archive/          # Données archivées
    ├── database/         # Base SQLite
    ├── config/           # Configuration
    ├── logs/             # Journalisation
    └── reports/          # Rapports générés
```

## Mise à jour des outils

```bash
python src/main.py --update-tools
```

Le système vérifie automatiquement les dernières versions stables
et télécharge uniquement les outils nécessaires.

## Sauvegarde

### Sauvegarde recommandée

- Sauvegarder régulièrement `Database/catalogue.db`
- Sauvegarder `Config/` (mais pas `config.json` local)
- Vérifier l'intégrité périodiquement

### Méthode de sauvegarde

```bash
# Sauvegarde manuelle de la base
cp Database/catalogue.db Database/catalogue.db.backup

# Vérification d'intégrité
python src/main.py --verify
```

## Restauration d'urgence

### En cas de corruption de la base

1. Arrêter immédiatement toute opération d'écriture
2. Copier la base actuelle (même corrompue)
3. Lancer la vérification :
   ```bash
   python src/main.py --verify --repair
   ```
4. Si réparation automatique échoue, restaurer depuis la dernière sauvegarde

### En cas de perte de fichiers

1. Les fichiers supprimés sont conservés dans `Archive/deleted/`
2. Utiliser la restauration par filtre pour les récupérer
3. Ou rechercher dans l'historique des exports Takeout

## Dépannage

### Problème : outils portables manquants

```bash
python src/main.py --setup --repair-tools
```

### Problème : base de données corrompue

```bash
python src/main.py --verify --repair
```

### Problème : conflit de chemins

Le système utilise des chemins relatifs. Aucun problème de changement
de lettre de lecteur (Windows) ou de point de montage (Linux).

### Problème : version incompatible

```bash
python src/main.py --update-tools
```

## Maintenance périodique

### Chaque semaine

- Vérifier l'intégrité : `python src/main.py --verify`
- Nettoyer les fichiers temporaires

### Chaque mois

- Exporter un inventaire : `python src/main.py --export-inventory`
- Vérifier l'espace disque
- Archiver les logs anciens

### Chaque trimestre

- Mise à jour des outils : `python src/main.py --update-tools`
- Compression périodique : `python src/main.py --compress`
- Sauvegarde complète de la base

## Notes de version

Consultez le [CHANGELOG.md](CHANGELOG.md) pour l'historique complet
des versions et leurs changements.
