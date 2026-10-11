"""Decrypt and validate an application backup without modifying MongoDB."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import os
from pathlib import Path

from bson import json_util
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify an encrypted .stfbak file")
    parser.add_argument("backup", type=Path)
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / "server" / ".env")
    key = os.getenv("BACKUP_ENCRYPTION_KEY", "").encode()
    if len(key) != 32:
        raise SystemExit("BACKUP_ENCRYPTION_KEY must be exactly 32 UTF-8 bytes")
    raw = args.backup.read_bytes()
    if len(raw) < 51 or raw[:7] != b"STFBKP1":
        raise SystemExit("Invalid or truncated STF backup header")
    nonce = raw[7:19]
    backup_id = raw[19:35].rstrip(b" ").decode("ascii")
    compressed = AESGCM(key).decrypt(nonce, raw[35:], backup_id.encode())
    snapshot = json_util.loads(gzip.decompress(compressed).decode("utf-8"))
    if snapshot.get("backup_id") != backup_id or not isinstance(snapshot.get("collections"), dict):
        raise SystemExit("Backup contents failed structural validation")
    counts = {name: len(rows) for name, rows in snapshot["collections"].items()}
    print(f"VERIFIED {backup_id}")
    print(f"sha256={hashlib.sha256(raw).hexdigest()}")
    print(f"database={snapshot.get('database')} created_at={snapshot.get('created_at')}")
    print("collections=" + ", ".join(f"{name}:{count}" for name, count in sorted(counts.items())))


if __name__ == "__main__":
    main()
