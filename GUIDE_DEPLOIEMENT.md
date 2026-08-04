# TakeOutBack Deployment Guide

## Prerequisites

- External hard drive (exFAT recommended)
- Disk space: 2x the size of data to archive
- Python 3.10+ (portable, provided with the project)
- 7-Zip 23.01+ (portable, provided with the project)

## Installation on External Drive

1. Connect the external drive
2. Copy the `TakeOutBack/` folder to the drive
3. Run the installation script:

```bash
# Linux
bash install.sh
```

4. Follow the on-screen instructions

## Drive Structure

```
External Drive/
├── TakeOutBack/              # Application software
│   ├── src/                  # Source code
│   ├── tools/                # Portable tools
│   ├── database/             # SQLite database
│   ├── config/               # Configuration
│   ├── logs/                 # Logs
│   └── reports/              # Generated reports
├── Incoming/                 # Google Takeout exports to process
│   └── google-takeout-*.zip  # Drop your exports here
└── Archive/                  # Compressed archives
    ├── raw/                  # Decompressed files (fast access)
    ├── compressed/           # Batch-compressed archives
    └── deleted/              # Deleted files (preserved)
```

## Running TakeOutBack

### Interactive Mode

```bash
bash TakeOutBack.sh
```

### Non-Interactive Mode

```bash
# Import Takeout exports
bash TakeOutBack.sh import

# Search for a file
bash TakeOutBack.sh search "photo.jpg"

# Verify integrity
bash TakeOutBack.sh verify

# Show statistics
bash TakeOutBack.sh stats
```

**Note on FAT32/exFAT drives:** If the filesystem doesn't support executable permissions, you must use `bash` before the script name. The installation script will detect this and display the correct commands.

## Tool Updates

```bash
bash TakeOutBack.sh update-tools
```

The system automatically checks for the latest stable versions
and downloads only the necessary tools.

## Backup

### Recommended Backup

- Regularly backup `Database/catalogue.db`
- Backup `Config/` (but not local `config.json`)
- Verify integrity periodically

### Backup Method

```bash
# Manual database backup
cp database/catalogue.db database/catalogue.db.backup

# Integrity verification
bash TakeOutBack.sh verify
```

## Emergency Restoration

### In Case of Database Corruption

1. Immediately stop all write operations
2. Copy the current database (even if corrupted)
3. Run verification:
   ```bash
   bash TakeOutBack.sh verify
   ```
4. If automatic repair fails, restore from last backup

### In Case of File Loss

1. Deleted files are preserved in `Archive/deleted/`
2. Use restore by filter to recover them
3. Or search through Takeout export history

## Troubleshooting

### Problem: Missing portable tools

```bash
bash TakeOutBack.sh update-tools
```

### Problem: Corrupted database

```bash
bash TakeOutBack.sh verify
```

### Problem: Path conflicts

The system uses relative paths. No issues with mount point changes.

### Problem: Incompatible version

```bash
bash TakeOutBack.sh update-tools
```

## Periodic Maintenance

### Weekly

- Verify integrity: `bash TakeOutBack.sh verify`
- Clean temporary files

### Monthly

- Export inventory: `bash TakeOutBack.sh stats`
- Check disk space
- Archive old logs

### Quarterly

- Update tools: `bash TakeOutBack.sh update-tools`
- Periodic compression: `bash TakeOutBack.sh import`
- Full database backup

## Version Notes

Consult the [CHANGELOG.md](CHANGELOG.md) for the complete version history
and changes.
