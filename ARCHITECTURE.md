# TakeOutBack Architecture

## Summary

TakeOutBack is a portable application for archiving the complete history of Google Takeout exports on an external drive. It preserves all Google data with versioning, fast search, and targeted restoration.

## Architecture Approach

### Approach: Flat storage + selective batch compression + SQLite index

**Decompressed files for fast access + periodic batch compression + SQLite index for search.**

### Rationale

The flat storage approach (Approach D) was chosen because:

1. **HDD Performance**: Files are decompressed for fast access. Compression is applied periodically in batches, not at each import.

2. **Instant Search**: SQLite index enables fast searches without scanning files.

3. **Natural Versioning**: Files are versioned by suffix (`name_v1.ext`, `name_v2.ext`), simple and compatible.

4. **No Massive Decompression**: Takeout exports are never fully decompressed. Only new or modified files are extracted.

5. **Scalability**: Architecture supports several million files and multiple terabytes.

## Database Structure

### Main Tables

#### `files`
Stores metadata for each unique file.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| logical_path | TEXT | Relative path within archive |
| filename | TEXT | Filename only |
| extension | TEXT | Extension without dot |
| size | INTEGER | Size in bytes |
| crc32 | INTEGER | CRC32 of ZIP archive |
| sha256 | TEXT | SHA256 hash (calculated if needed) |
| archive_path | TEXT | Path to source archive |
| archive_crc | TEXT | CRC of the archive itself |
| discovery_date | TEXT | First discovery |
| last_observed | TEXT | Last observation |
| status | TEXT | active, archived, deleted |
| takeout_id | TEXT | Link to original export |
| metadata_json | TEXT | JSON metadata (EXIF, etc.) |
| created_at | TEXT | Creation date (metadata) |
| modified_at | TEXT | Modification date |

#### `versions`
Stores each version of a file.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| file_id | INTEGER | Reference to `files.id` |
| version | INTEGER | Version number (1, 2, 3...) |
| archive_path | TEXT | Path to this version's archive |
| logical_path | TEXT | Logical path within archive |
| size | INTEGER | Size in bytes |
| crc32 | INTEGER | CRC32 |
| sha256 | TEXT | SHA256 hash |
| takeout_id | TEXT | Link to original export |
| discovered_at | TEXT | Discovery date |
| status | TEXT | active, archived, deleted |
| is_current | BOOLEAN | Current version |

#### `takeouts`
Stores information about each Takeout export.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Unique identifier (hash or date) |
| name | TEXT | Takeout file/folder name |
| import_date | TEXT | Import date |
| file_count | INTEGER | Number of files |
| total_size | INTEGER | Total size |
| status | TEXT | pending, processing, processed, error |
| notes | TEXT | Notes |

#### `operations`
Operation log.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| operation_type | TEXT | import, restore, verify, update |
| timestamp | TEXT | Operation date |
| duration_seconds | REAL | Duration in seconds |
| files_processed | INTEGER | Number of files processed |
| files_added | INTEGER | Number of files added |
| files_modified | INTEGER | Number of files modified |
| files_deleted | INTEGER | Number of files deleted |
| errors | INTEGER | Number of errors |
| details | TEXT | JSON with details |
| status | TEXT | completed, failed, interrupted |

### Indexes

- `idx_files_logical_path`: Search by path
- `idx_files_sha256`: Search by hash
- `idx_files_status`: Filter by status
- `idx_files_discovery_date`: Sort by discovery date
- `idx_files_last_observed`: Sort by last observation
- `idx_files_extension`: Filter by extension
- `idx_files_takeout_id`: Link to export
- `idx_versions_file_id`: Links to versions
- `idx_versions_is_current`: Current version
- `idx_takeouts_import_date`: Sort by import date
- `idx_operations_timestamp`: Sort by operation date
- `idx_operations_type`: Filter by type

### View `current_files`

Optimized view for fast access to the latest version of each file.

## Versioning Strategy

### Rules

1. **New file**: `name.ext` (implicit version 1)
2. **Modified file**:
   - Old version → `name_v1.ext`
   - New version → `name.ext`
3. **Deleted file**: Preserved in `Archive/deleted/` with metadata
4. **Maximum versions**: Configurable (default: 10)

### Example

```
Archive/raw/Photos/Vacation/
├── beach.jpg          # Current version (v3)
├── beach_v1.jpg       # Version 1
└── beach_v2.jpg       # Version 2
```

## Compression Strategy

### Compression Rules

| File Type | Compression | Reason |
|-----------|-------------|--------|
| Photos (JPG, PNG) | None | Already compressed |
| Videos (MP4, MOV) | None | Already compressed |
| Documents (DOCX, PDF) | 7z compression | 50-70% gain |
| Texts (TXT, CSV) | 7z compression | 80-90% gain |
| JSON/XML | 7z compression | 60-80% gain |
| Emails (MBOX) | 7z compression | 40-60% gain |

### Process

1. **Import**: Decompressed files into `Archive/raw/`
2. **Analysis**: Classification by type
3. **Nightly compression**: Group by type + date → 7z archive in `Archive/compressed/`
4. **Verification**: CRC verified before deleting source files
5. **Update**: SQLite index updated

## Security Strategy

### Level 1: Physical Security (current)
- External hard drive in a secure location
- No encryption for now

### Level 2: Data Integrity
- CRC32 for fast ZIP archive verification
- SHA256 for thorough verification (calculated on demand)
- Operation journal in SQLite
- Periodic integrity verification

### Level 3: Future Encryption (optional)
- AES-256 via `cryptography` library
- Key derived via PBKDF2
- Key stored in encrypted local file

## Update Strategy

### Embedded Tools
- **Python**: Portable version downloaded on first launch
- **7-Zip**: Portable version (`7zz.exe`/`7zz`) downloaded
- **Updates**: Detected and applied automatically

### Process
1. On startup: version check
2. Comparison with known stable versions
3. Download if update available
4. CRC verification of downloads
5. Atomic update (new version in `Tools/temp/`, replace after verification)
6. Automatic rollback on failure

## Crash Recovery Strategy

### SQLite Transactions
- All operations are transactional
- On crash: automatic rollback
- `PRAGMA journal_mode=WAL` for better tolerance

### Temporary Files
- All writes go through temporary files
- Atomic rename at the end
- Automatic cleanup on restart

### Logging
- Each operation is logged in `operations`
- On crash, resume from last complete operation
- Detailed logs in `Logs/`

### Automatic Verification
- On startup: SQLite integrity check
- On detected corruption: automatic repair attempt
- On failure: restore from last database backup

## Search Strategy

### SQLite Index
- Search by name, extension, path, date, hash
- Optimized indexes for performance
- In-memory search for frequent queries

### Performance
- Search time < 1 second for millions of files
- Memory usage < 500 MB
- Optimized SQL queries with indexes

## Restoration Strategy

### Restoration Modes
1. **Latest version**: Restore file in current state
2. **Specific version**: Restore historical version
3. **Complete folder**: Restore entire folder
4. **By filter**: Restore based on criteria (date, extension, etc.)

### Optimizations
- No massive decompression
- Targeted restoration of only requested files
- CRC verification after restoration

## Performance Strategy

### HDD Optimizations
- Sequential access prioritized
- Grouping by file type
- SQLite index in memory for frequent searches
- Batch processing (1000 files at a time)

### SQL Optimizations
- Indexes adapted to common queries
- Optimized queries
- Periodic VACUUM to keep database compact

### Memory Optimizations
- Batch reading
- No full archive loading in memory
- Automatic resource cleanup

## Testing Strategy

### Unit Tests
- Test each independent module
- Coverage > 80%

### Integration Tests
- Complete flow tests (import → search → restore)
- Resilience tests (crash, corruption)

### Performance Tests
- Load tests with millions of files
- Response time tests

## Maintenance Strategy

### Regular Updates
- Bug fixes
- Performance improvements
- New features

### Compatibility
- Support for new Windows/Linux versions
- Support for new Python/7-Zip versions
- Adaptation to Google Takeout changes

### Documentation
- Documentation updated with each version
- Update guides
- Release notes
