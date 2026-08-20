import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def configure_mongo_url() -> None:
    username = os.environ.pop("MONGO_APP_USERNAME", "")
    password = os.environ.pop("MONGO_APP_PASSWORD", "")
    database = os.getenv("MONGO_DB", "money_lending_production")
    host = os.getenv("MONGO_HOST", "mongodb")
    if not username or not password:
        raise RuntimeError("MONGO_APP_USERNAME and MONGO_APP_PASSWORD are required")
    os.environ["MONGO_URL"] = (
        f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{host}:27017/"
        f"{quote_plus(database)}?authSource={quote_plus(database)}&directConnection=true&replicaSet=rs0&retryWrites=true&w=majority&journal=true"
    )


if __name__ == "__main__":
    configure_mongo_url()
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips="*",
        access_log=True,
    )
