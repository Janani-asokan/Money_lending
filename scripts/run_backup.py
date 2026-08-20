"""Run the same encrypted backup job used by the owner API."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from starlette.requests import Request

SERVER_DIR = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))
import main  # noqa: E402


async def run() -> None:
    await main.startup()
    try:
        request = Request({
            "type": "http", "method": "POST", "path": "/api/backups/manual",
            "headers": [], "client": ("127.0.0.1", 0),
        })
        result = await main.manual_backup(request, {
            "id": "SYSTEM", "username": "backup-job", "name": "Automated backup job", "role": "owner",
        })
        print(result)
    finally:
        await main.shutdown()


if __name__ == "__main__":
    asyncio.run(run())
