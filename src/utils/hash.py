"""
Calculs de hash pour TakeOutBack.
Supporte CRC32 et SHA256.
"""
import hashlib
import zlib
from pathlib import Path
from typing import Optional


def calculate_crc32(file_path: Path) -> int:
    """Calcule le CRC32 d'un fichier."""
    crc = 0
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            crc = zlib.crc32(chunk, crc)
    return crc & 0xFFFFFFFF


def calculate_sha256(file_path: Path) -> str:
    """Calcule le SHA256 d'un fichier."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def calculate_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calcule le hash d'un fichier selon l'algorithme spécifié."""
    if algorithm.lower() == "crc32":
        return f"{calculate_crc32(file_path):08x}"
    elif algorithm.lower() == "sha256":
        return calculate_sha256(file_path)
    else:
        raise ValueError(f"Algorithme non supporté: {algorithm}")


def calculate_hash_from_bytes(data: bytes, algorithm: str = "sha256") -> str:
    """Calcule le hash de données en mémoire."""
    if algorithm.lower() == "crc32":
        return f"{zlib.crc32(data):08x}"
    elif algorithm.lower() == "sha256":
        return hashlib.sha256(data).hexdigest()
    else:
        raise ValueError(f"Algorithme non supporté: {algorithm}")


def verify_file_integrity(
    file_path: Path,
    expected_crc: Optional[int] = None,
    expected_sha256: Optional[str] = None,
) -> bool:
    """Vérifie l'intégrité d'un fichier."""
    if expected_crc is not None:
        actual_crc = calculate_crc32(file_path)
        if actual_crc != expected_crc:
            return False

    if expected_sha256 is not None:
        actual_sha256 = calculate_sha256(file_path)
        if actual_sha256 != expected_sha256:
            return False

    return True
