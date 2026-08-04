# TakeOutBack

Portable application for archiving the complete history of Google Takeout exports on an external drive.

## Features

- Incremental archiving of Google Takeout exports
- File versioning (preserves all historical versions)
- Fast search across millions of files
- Targeted file or version restoration
- Integrity verification with JSON/CSV reports
- Periodic batch compression
- 100% portable (external drive)
- Linux compatible

## Structure

```
Drive root/
├── TakeOutBack/              # Application software
│   ├── src/                  # Source code
│   ├── tools/                # Portable tools (Python, 7-Zip)
│   ├── database/             # SQLite database
│   ├── config/               # Configuration
│   ├── logs/                 # Logs
│   ├── reports/              # Generated reports
│   └── ...
├── Incoming/                 # Google Takeout exports to process
│   └── google-takeout-*.zip  # Drop your exports here
└── Archive/                  # Compressed archives
    ├── raw/                  # Decompressed files (fast access)
    ├── compressed/           # Batch-compressed archives
    └── deleted/              # Deleted files (preserved)
```

## Quick Install

### Linux

```bash
cd /media/your_drive
curl -fsSL https://raw.githubusercontent.com/gukak/TakeOutBack/main/install.sh | bash
```

### Manual Install

1. Download the ZIP from [GitHub](https://github.com/gukak/TakeOutBack/archive/refs/heads/main.zip)
2. Extract and rename the folder to `TakeOutBack`
3. Place it at the root of your external drive
4. Create `Incoming/` and `Archive/` folders next to `TakeOutBack/`

## Usage

```bash
# Interactive menu
bash TakeOutBack.sh

# Non-interactive mode
bash TakeOutBack.sh import
bash TakeOutBack.sh search "photo.jpg"
bash TakeOutBack.sh verify
bash TakeOutBack.sh stats
```

### Workflow

1. Drop your Google Takeout exports into `Incoming/`
2. Run `bash TakeOutBack.sh import` to process them
3. Search files with `bash TakeOutBack.sh search "name"`
4. Restore via interactive menu or command line
5. Verify integrity with `bash TakeOutBack.sh verify`

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed technical documentation
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [GUIDE_DEPLOIEMENT.md](GUIDE_DEPLOIEMENT.md) - Operational guide

## License

TBD.
