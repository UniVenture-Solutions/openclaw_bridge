from __future__ import annotations

import re
import secrets

import frappe
import pymysql
from frappe.installer import update_site_config


_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_\-.%]+$")


def _safe_or_default(value: str, default: str) -> str:
    if value and _SAFE_IDENTIFIER.fullmatch(value):
        return value
    return default


def _detect_db_client_host() -> str:
    row = frappe.db.sql(
        "SELECT SUBSTRING_INDEX(CURRENT_USER(), '@', -1) AS host",
        as_dict=True,
    )
    host = (row[0].get("host") if row else "") or ""
    return _safe_or_default(host, "%")


def _quote_ident(value: str) -> str:
    return value.replace("`", "``")


def _quote_sql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def provision_readonly_db_user() -> dict[str, str]:
    conf = frappe.get_site_config() or {}

    db_name = conf.get("db_name") or frappe.conf.db_name
    if not db_name:
        raise frappe.ValidationError("Missing db_name in site configuration")

    default_user = "openclaw_ro"
    user = _safe_or_default(str(conf.get("openclaw_bridge_readonly_user") or default_user), default_user)

    detected_host = _detect_db_client_host()
    configured_host = str(conf.get("openclaw_bridge_readonly_host") or detected_host)
    host = _safe_or_default(configured_host, detected_host)

    password = conf.get("openclaw_bridge_readonly_password") or secrets.token_urlsafe(24)

    create_user_sql = (
        f"CREATE USER IF NOT EXISTS '{_quote_sql_string(user)}'@'{_quote_sql_string(host)}' "
        f"IDENTIFIED BY '{_quote_sql_string(password)}'"
    )
    alter_user_sql = (
        f"ALTER USER '{_quote_sql_string(user)}'@'{_quote_sql_string(host)}' "
        f"IDENTIFIED BY '{_quote_sql_string(password)}'"
    )
    grant_sql = (
        f"GRANT SELECT ON `{_quote_ident(db_name)}`.* "
        f"TO '{_quote_sql_string(user)}'@'{_quote_sql_string(host)}'"
    )

    try:
        frappe.db.sql(create_user_sql)
        frappe.db.sql(alter_user_sql)
        frappe.db.sql(grant_sql)
        frappe.db.sql("FLUSH PRIVILEGES")
    except Exception as exc:
        admin_user = conf.get("openclaw_bridge_admin_db_user")
        admin_password = conf.get("openclaw_bridge_admin_db_password")
        if not admin_user or not admin_password:
            raise exc
        _provision_with_admin_credentials(
            admin_user=str(admin_user),
            admin_password=str(admin_password),
            db_name=str(db_name),
            readonly_user=str(user),
            readonly_host=str(host),
            readonly_password=str(password),
            db_host=str(conf.get("db_host") or frappe.conf.db_host or "127.0.0.1"),
            db_port=int(conf.get("db_port") or frappe.conf.db_port or 3306),
        )

    update_site_config(
        {
            "openclaw_bridge_readonly_user": user,
            "openclaw_bridge_readonly_host": host,
            "openclaw_bridge_readonly_password": password,
        },
        validate=False,
    )

    return {
        "db_name": db_name,
        "readonly_user": user,
        "readonly_host": host,
    }


def ensure_bridge_secrets() -> dict[str, str | int]:
    conf = frappe.get_site_config() or {}

    key_id = str(conf.get("openclaw_bridge_hmac_key_id") or "openclaw-ut-prod")
    secret = str(conf.get("openclaw_bridge_hmac_secret") or secrets.token_urlsafe(48))

    update_site_config(
        {
            "openclaw_bridge_hmac_key_id": key_id,
            "openclaw_bridge_hmac_secret": secret,
        },
        validate=False,
    )

    return {
        "hmac_key_id": key_id,
    }


def after_install() -> None:
    try:
        ensure_bridge_secrets()
    except Exception:
        frappe.logger().exception("OpenClaw Bridge: failed to ensure HMAC secrets during install")

    try:
        info = provision_readonly_db_user()
        frappe.logger().info(
            "OpenClaw Bridge readonly DB user ensured: %(readonly_user)s@%(readonly_host)s on %(db_name)s",
            info,
        )
    except Exception:
        # Do not fail entire app installation if host-level DB user provisioning is restricted.
        frappe.logger().exception("OpenClaw Bridge: failed to auto-provision readonly DB user during install")


def _provision_with_admin_credentials(
    admin_user: str,
    admin_password: str,
    db_name: str,
    readonly_user: str,
    readonly_host: str,
    readonly_password: str,
    db_host: str,
    db_port: int,
) -> None:
    conn = pymysql.connect(
        host=db_host,
        port=db_port,
        user=admin_user,
        password=admin_password,
        database="mysql",
        autocommit=True,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                (
                    f"CREATE USER IF NOT EXISTS '{_quote_sql_string(readonly_user)}'@"
                    f"'{_quote_sql_string(readonly_host)}' IDENTIFIED BY '{_quote_sql_string(readonly_password)}'"
                )
            )
            cur.execute(
                (
                    f"ALTER USER '{_quote_sql_string(readonly_user)}'@"
                    f"'{_quote_sql_string(readonly_host)}' IDENTIFIED BY '{_quote_sql_string(readonly_password)}'"
                )
            )
            cur.execute(
                (
                    f"GRANT SELECT ON `{_quote_ident(db_name)}`.* TO "
                    f"'{_quote_sql_string(readonly_user)}'@'{_quote_sql_string(readonly_host)}'"
                )
            )
            cur.execute("FLUSH PRIVILEGES")
    finally:
        conn.close()
