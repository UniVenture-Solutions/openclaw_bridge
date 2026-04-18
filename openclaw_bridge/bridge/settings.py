from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    host: str = "0.0.0.0"
    port: int = 8800

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""

    hmac_key_id: str = ""
    hmac_secret: str = ""

    auth_max_skew_seconds: int = 300
    nonce_ttl_seconds: int = 600

    max_rows: int = 1000
    query_timeout_ms: int = 10000
    max_concurrent_queries: int = 5
    rate_limit_rpm: int = 60

    audit_log_path: str = "/home/frappe/dev-bench/logs/openclaw_bridge_audit.log"
    log_level: str = "INFO"


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _site_fallback() -> dict:
    """Best-effort fallback from Frappe site config when running inside bench."""
    try:
        import frappe  # type: ignore

        conf = frappe.get_site_config() or {}
        common = {
            "db_host": conf.get("db_host"),
            "db_name": conf.get("db_name"),
            "db_user": conf.get("db_user"),
            "db_password": conf.get("db_password"),
            "readonly_user": conf.get("openclaw_bridge_readonly_user"),
            "readonly_password": conf.get("openclaw_bridge_readonly_password"),
            "hmac_key_id": conf.get("openclaw_bridge_hmac_key_id"),
            "hmac_secret": conf.get("openclaw_bridge_hmac_secret"),
        }
        return {k: v for k, v in common.items() if v}
    except Exception:
        return {}


def load_settings() -> Settings:
    cfg = Settings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=_int_env("PORT", 8800),
        db_host=os.getenv("DB_HOST", "127.0.0.1"),
        db_port=_int_env("DB_PORT", 3306),
        db_name=os.getenv("DB_NAME", ""),
        db_user=os.getenv("DB_USER", ""),
        db_password=os.getenv("DB_PASSWORD", ""),
        hmac_key_id=os.getenv("HMAC_KEY_ID", ""),
        hmac_secret=os.getenv("HMAC_SECRET", ""),
        auth_max_skew_seconds=_int_env("AUTH_MAX_SKEW_SECONDS", 300),
        nonce_ttl_seconds=_int_env("NONCE_TTL_SECONDS", 600),
        max_rows=_int_env("MAX_ROWS", 1000),
        query_timeout_ms=_int_env("QUERY_TIMEOUT_MS", 10000),
        max_concurrent_queries=_int_env("MAX_CONCURRENT_QUERIES", 5),
        rate_limit_rpm=_int_env("RATE_LIMIT_RPM", 60),
        audit_log_path=os.getenv(
            "AUDIT_LOG_PATH", "/home/frappe/dev-bench/logs/openclaw_bridge_audit.log"
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

    fallback = _site_fallback()
    if not cfg.hmac_key_id:
        cfg.hmac_key_id = fallback.get("hmac_key_id", "")
    if not cfg.hmac_secret:
        cfg.hmac_secret = fallback.get("hmac_secret", "")
    if not cfg.db_name:
        cfg.db_name = fallback.get("db_name", "")
    if not cfg.db_user:
        cfg.db_user = fallback.get("readonly_user", "")
    if not cfg.db_password:
        cfg.db_password = fallback.get("readonly_password", "")
    if not cfg.db_user:
        cfg.db_user = fallback.get("db_user", "")
    if not cfg.db_password:
        cfg.db_password = fallback.get("db_password", "")
    if cfg.db_host == "127.0.0.1" and fallback.get("db_host"):
        cfg.db_host = fallback["db_host"]

    return cfg


settings = load_settings()
