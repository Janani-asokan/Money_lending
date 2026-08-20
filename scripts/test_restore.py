"""Restore an encrypted backup into temporary collections, verify, then remove them."""
from __future__ import annotations

import argparse
import gzip
import os
from pathlib import Path

from bson import json_util
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv
from pymongo import MongoClient


def read_backup(path: Path, key: bytes) -> tuple[str, dict]:
    raw = path.read_bytes()
    if len(raw) < 51 or raw[:7] != b"STFBKP1":
        raise SystemExit("Invalid or truncated STF backup")
    backup_id = raw[19:35].rstrip(b" ").decode("ascii")
    clear = AESGCM(key).decrypt(raw[7:19], raw[35:], backup_id.encode())
    return backup_id, json_util.loads(gzip.decompress(clear).decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    parser.add_argument("--confirm-temporary-write", action="store_true")
    args = parser.parse_args()
    if not args.confirm_temporary_write:
        raise SystemExit("Pass --confirm-temporary-write to run the isolated recovery test")
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / "server" / ".env")
    key = os.getenv("BACKUP_ENCRYPTION_KEY", "").encode()
    if len(key) != 32:
        raise SystemExit("BACKUP_ENCRYPTION_KEY must be exactly 32 UTF-8 bytes")
    backup_id, snapshot = read_backup(args.backup, key)
    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=5000)
    database = client[os.environ["MONGO_DB"]]
    prefix = f"__restore_test_{backup_id.lower().replace('-', '_')}_"
    created: list[str] = []
    try:
        for source_name, documents in snapshot["collections"].items():
            target_name = prefix + source_name
            if target_name in database.list_collection_names():
                raise SystemExit(f"Refusing to overwrite existing collection: {target_name}")
            if documents:
                database[target_name].insert_many(documents, ordered=True)
            else:
                database.create_collection(target_name)
            created.append(target_name)
            restored = database[target_name].count_documents({})
            if restored != len(documents):
                raise RuntimeError(f"Count mismatch for {source_name}: {restored} != {len(documents)}")
        print(f"RESTORE TEST PASSED {backup_id}: {len(created)} collections verified")
    finally:
        for name in created:
            if name.startswith(prefix):
                database.drop_collection(name)
        client.close()


if __name__ == "__main__":
    main()
