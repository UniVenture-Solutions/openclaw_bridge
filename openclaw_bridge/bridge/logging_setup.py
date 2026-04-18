from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from .settings import settings


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def audit_log(event: dict) -> None:
    payload = {"ts": datetime.now(UTC).isoformat(), **event}
    log_path = Path(settings.audit_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, separators=(",", ":"), ensure_ascii=True) + "\n")
