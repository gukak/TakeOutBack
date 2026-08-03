# Architecture TakeOutBack

## Résumé

TakeOutBack est une application portable d'archivage de l'historique Google Takeout. Elle permet de conserver l'intégralité des données Google sur un disque externe, avec versionnement, recherche rapide et restauration ciblée.

## Architecture retenue

### Approche : Dépôt plat + compression sélective par lot

**Stockage décompressé en accès rapide + compression périodique par lot + index SQLite pour la recherche.**

### Justification

L'approche D (dépôt plat avec compression sélective) a été retenue car :

1. **Performance HDD** : Les fichiers sont décompressés pour un accès rapide. La compression est appliquée périodiquement par lot, pas à chaque import.

2. **Recherche instantanée** : L'index SQLite permet des recherches rapides sans parcourir les fichiers.

3. **Versionnement naturel** : Les fichiers sont versionnés par suffixe (`nom_v1.ext`, `nom_v2.ext`), simple et compatible.

4. **Pas de décompression massive** : Les exports Takeout ne sont jamais entièrement décompressés. Seuls les fichiers nouveaux ou modifiés sont extraits.

5. **Évolutivité** : L'architecture supporte plusieurs millions de fichiers et plusieurs téraoctets.

## Structure de base de données

### Tables principales

#### `files`
Stocke les métadonnées de chaque fichier unique.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Clé primaire |
| logical_path | TEXT | Chemin relatif dans l'archive |
| filename | TEXT | Nom de fichier seul |
| extension | TEXT | Extension sans le point |
| size | INTEGER | Taille en octets |
| crc32 | INTEGER | CRC32 de l'archive ZIP |
| sha256 | TEXT | Hash SHA256 (calculé si nécessaire) |
| archive_path | TEXT | Chemin vers l'archive source |
| archive_crc | TEXT | CRC de l'archive elle-même |
| discovery_date | TEXT | Première découverte |
| last_observed | TEXT | Dernière observation |
| status | TEXT | active, archived, deleted |
| takeout_id | TEXT | Lien vers l'export d'origine |
| metadata_json | TEXT | Métadonnées JSON (EXIF, etc.) |
| created_at | TEXT | Date de création (métadonnée) |
| modified_at | TEXT | Date de modification |

#### `versions`
Stocke chaque version d'un fichier.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Clé primaire |
| file_id | INTEGER | Référence vers `files.id` |
| version | INTEGER | Numéro de version (1, 2, 3...) |
| archive_path | TEXT | Chemin vers l'archive de cette version |
| logical_path | TEXT | Chemin logique dans l'archive |
| size | INTEGER | Taille en octets |
| crc32 | INTEGER | CRC32 |
| sha256 | TEXT | Hash SHA256 |
| takeout_id | TEXT | Lien vers l'export d'origine |
| discovered_at | TEXT | Date de découverte |
| status | TEXT | active, archived, deleted |
| is_current | BOOLEAN | Version actuelle |

#### `takeouts`
Stocke les informations sur chaque export Takeout.

| Colonne | Type | Description |
|---------|------|-------------|
| id | TEXT | Identifiant unique (hash ou date) |
| name | TEXT | Nom du fichier/dossier Takeout |
| import_date | TEXT | Date d'import |
| file_count | INTEGER | Nombre de fichiers |
| total_size | INTEGER | Taille totale |
| status | TEXT | pending, processing, processed, error |
| notes | TEXT | Notes |

#### `operations`
Journal des opérations effectuées.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Clé primaire |
| operation_type | TEXT | import, restore, verify, update |
| timestamp | TEXT | Date de l'opération |
| duration_seconds | REAL | Durée en secondes |
| files_processed | INTEGER | Nombre de fichiers traités |
| files_added | INTEGER | Nombre de fichiers ajoutés |
| files_modified | INTEGER | Nombre de fichiers modifiés |
| files_deleted | INTEGER | Nombre de fichiers supprimés |
| errors | INTEGER | Nombre d'erreurs |
| details | TEXT | JSON avec détails |
| status | TEXT | completed, failed, interrupted |

### Index

- `idx_files_logical_path` : Recherche par chemin
- `idx_files_sha256` : Recherche par hash
- `idx_files_status` : Filtrage par statut
- `idx_files_discovery_date` : Tri par date de découverte
- `idx_files_last_observed` : Tri par dernière observation
- `idx_files_extension` : Filtrage par extension
- `idx_files_takeout_id` : Lien vers l'export
- `idx_versions_file_id` : Liens vers les versions
- `idx_versions_is_current` : Version actuelle
- `idx_takeouts_import_date` : Tri par date d'import
- `idx_operations_timestamp` : Tri par date d'opération
- `idx_operations_type` : Filtrage par type

### Vue `current_files`

Vue optimisée pour accéder rapidement à la dernière version de chaque fichier.

## Stratégie de versionnement

### Règles

1. **Nouveau fichier** : `nom.ext` (version 1 implicite)
2. **Fichier modifié** :
   - Ancienne version → `nom_v1.ext`
   - Nouvelle version → `nom.ext`
3. **Fichier supprimé** : Conservé dans `Archive/deleted/` avec métadonnées
4. **Maximum de versions** : Configurable (par défaut : 10)

### Exemple

```
Archive/raw/Photos/Vacation/
├── beach.jpg          # Version actuelle (v3)
├── beach_v1.jpg       # Version 1
└── beach_v2.jpg       # Version 2
```

## Stratégie de compression

### Règles de compression

| Type de fichier | Compression | Raison |
|----------------|-------------|--------|
| Photos (JPG, PNG) | Non compressé | Déjà compressés |
| Vidéos (MP4, MOV) | Non compressé | Déjà compressés |
| Documents (DOCX, PDF) | Compression 7z | Gain 50-70% |
| Textes (TXT, CSV) | Compression 7z | Gain 80-90% |
| JSON/XML | Compression 7z | Gain 60-80% |
| Emails (MBOX) | Compression 7z | Gain 40-60% |

### Processus

1. **Import** : Fichiers décompressés dans `Archive/raw/`
2. **Analyse** : Classification par type
3. **Compression nocturne** : Groupes par type + date → archive 7z dans `Archive/compressed/`
4. **Vérification** : CRC vérifié avant suppression des fichiers source
5. **Mise à jour** : Index SQLite mis à jour

## Stratégie de sécurité

### Niveau 1 : Sécurité physique (actuel)
- Disque dur externe dans un endroit sécurisé
- Pas de chiffrement pour l'instant

### Niveau 2 : Intégrité des données
- CRC32 pour vérification rapide des archives ZIP
- SHA256 pour vérification approfondie (calculé à la demande)
- Journal des opérations dans SQLite
- Vérification d'intégrité périodique

### Niveau 3 : Chiffrement futur (optionnel)
- AES-256 via `cryptography` library
- Clé dérivée via PBKDF2
- Stockage de la clé dans un fichier local chiffré

## Stratégie de mise à jour

### Outils embarqués
- **Python** : version portable téléchargée au premier lancement
- **7-Zip** : version portable (`7zz.exe`/`7zz`) téléchargée
- **Mises à jour** : détectées et appliquées automatiquement

### Processus
1. Au démarrage : vérification des versions
2. Comparaison avec versions stables connues
3. Téléchargement si mise à jour disponible
4. Vérification CRC des téléchargements
5. Mise à jour atomique (nouvelle version dans `Tools/temp/`, remplacement après vérification)
6. Rollback automatique en cas d'échec

## Stratégie de reprise après incident

### Transactions SQLite
- Toutes les opérations sont transactionnelles
- En cas de crash : rollback automatique
- `PRAGMA journal_mode=WAL` pour meilleure tolérance

### Fichiers temporaires
- Toutes les écritures passent par des fichiers temporaires
- Renommage atomique à la fin
- Nettoyage automatique au redémarrage

### Journalisation
- Chaque opération est journalisée dans `operations`
- En cas de crash, reprise depuis la dernière opération complète
- Logs détaillés dans `Logs/`

### Vérification automatique
- Au démarrage : vérification de l'intégrité de SQLite
- En cas de corruption détectée : tentative de réparation automatique
- Si échec : restauration depuis la dernière sauvegarde de la base

## Stratégie de recherche

### Index SQLite
- Recherche par nom, extension, chemin, date, hash
- Index optimisés pour performance
- Recherche en mémoire pour les requêtes fréquentes

### Performance
- Temps de recherche < 1 seconde pour des millions de fichiers
- Consommation mémoire < 500 MB
- Requêtes SQL optimisées avec index

## Stratégie de restauration

### Modes de restauration
1. **Dernière version** : Restauration du fichier dans son état actuel
2. **Version spécifique** : Restauration d'une version historique
3. **Dossier complet** : Restauration d'un dossier entier
4. **Par filtre** : Restauration basée sur des critères (date, extension, etc.)

### Optimisations
- Pas de décompression massive
- Restauration ciblée uniquement des fichiers demandés
- Vérification CRC après restauration

## Stratégie de performance

### Optimisations HDD
- Accès séquentiels privilégiés
- Regroupement par type de fichier
- Index SQLite en mémoire pour les recherches fréquentes
- Batch processing (lots de 1000 fichiers)

### Optimisations SQL
- Index adaptés aux requêtes courantes
- Requêtes optimisées
- VACUUM périodique pour maintenir la base compacte

### Optimisations mémoire
- Lecture par lots
- Pas de chargement complet des archives en mémoire
- Nettoyage automatique des ressources

## Stratégie de test

### Tests unitaires
- Tests de chaque module indépendant
- Couverture > 80%

### Tests d'intégration
- Tests de flux complets (import → recherche → restauration)
- Tests de résilience (crash, corruption)

### Tests de performance
- Tests de charge avec millions de fichiers
- Tests de temps de réponse

## Stratégie de maintenance

### Mises à jour régulières
- Corrections de bugs
- Améliorations de performance
- Nouvelles fonctionnalités

### Compatibilité
- Support de nouvelles versions de Windows/Linux
- Support de nouvelles versions de Python/7-Zip
- Adaptation aux évolutions de Google Takeout

### Documentation
- Mise à jour de la documentation à chaque version
- Guides de mise à jour
- Notes de version
