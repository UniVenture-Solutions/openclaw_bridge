from __future__ import annotations

import hashlib
import hmac
import json
import threading
import time
import uuid
from typing import Any

import frappe
from werkzeug.wrappers import Response

from openclaw_bridge.bridge.db import BridgeDbError, DatabaseClient
from openclaw_bridge.bridge.logging_setup import audit_log
from openclaw_bridge.bridge.mcp import TOOL_DEFINITIONS, mcp_result
from openclaw_bridge.bridge.rate_limit import RateLimiter
from openclaw_bridge.bridge.settings import settings
from openclaw_bridge.bridge.sql_guard import SqlValidationError

_rate_limiter = RateLimiter(settings.rate_limit_rpm)
_query_semaphore = threading.BoundedSemaphore(max(1, settings.max_concurrent_queries))
_replay_lock = threading.Lock()
_replay_cache: dict[str, float] = {}


class BridgeHttpError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _json_response(payload: dict[str, Any], status_code: int = 200) -> Response:
    return Response(
        json.dumps(payload, ensure_ascii=True, default=str),
        status=status_code,
        mimetype="application/json",
    )


def _sse_response(event_stream) -> Response:
    response = Response(event_stream, mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response


def _request_body() -> bytes:
    return frappe.request.get_data(cache=True) or b""


def _request_json() -> dict[str, Any]:
    body = _request_body()
    if not body:
        return {}
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BridgeHttpError(400, "Invalid JSON body") from exc


def _canonical_payload(method: str, path: str, timestamp: str, nonce: str, body: bytes) -> str:
    body_hash = hashlib.sha256(body).hexdigest()
    return "\n".join([method.upper(), path, timestamp, nonce, body_hash])


def _expire_replays(now: float) -> None:
    cutoff = now - settings.nonce_ttl_seconds
    stale_keys = [key for key, ts in _replay_cache.items() if ts < cutoff]
    for key in stale_keys:
        _replay_cache.pop(key, None)


def _verify_hmac_request() -> str:
    headers = frappe.request.headers
    key_id = headers.get("X-Key-Id", "")
    timestamp = headers.get("X-Timestamp", "")
    nonce = headers.get("X-Nonce", "")
    signature = headers.get("X-Signature", "")

    if not all([key_id, timestamp, nonce, signature]):
        raise BridgeHttpError(401, "Missing auth headers")

    if key_id != settings.hmac_key_id:
        raise BridgeHttpError(401, "Invalid key id")

    try:
        ts = int(timestamp)
    except ValueError as exc:
        raise BridgeHttpError(401, "Invalid timestamp") from exc

    now = int(time.time())
    if abs(now - ts) > settings.auth_max_skew_seconds:
        raise BridgeHttpError(401, "Request timestamp out of allowed skew")

    replay_key = f"{key_id}:{timestamp}:{nonce}"
    with _replay_lock:
        _expire_replays(now)
        if replay_key in _replay_cache:
            raise BridgeHttpError(401, "Replay detected")
        _replay_cache[replay_key] = now

    expected = hmac.new(
        settings.hmac_secret.encode("utf-8"),
        _canonical_payload(
            frappe.request.method,
            frappe.request.path,
            timestamp,
            nonce,
            _request_body(),
        ).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature.lower(), expected.lower()):
        raise BridgeHttpError(401, "Invalid signature")

    if not _rate_limiter.allow(key_id):
        raise BridgeHttpError(429, "Rate limit exceeded")

    return key_id


def _db_client() -> DatabaseClient:
    return DatabaseClient()


def _tool_payload(name: str, arguments: dict[str, Any], key_id: str, request_id: str) -> dict[str, Any]:
    db = _db_client()

    if name == "list_tables":
        return {"tables": db.list_tables()}

    if name == "describe_table":
        table_name = arguments.get("table_name")
        if not table_name:
            raise BridgeHttpError(400, "Missing table_name")
        return {
            "table_name": table_name,
            "columns": db.describe_table(table_name),
        }

    if name == "run_sql_readonly":
        sql = arguments.get("sql")
        if not sql:
            raise BridgeHttpError(400, "Missing sql")

        params = arguments.get("params")
        limit = arguments.get("limit")

        acquired = _query_semaphore.acquire(blocking=False)
        if not acquired:
            raise BridgeHttpError(429, "Too many concurrent queries")

        try:
            query_result = db.run_sql_readonly(sql=sql, params=params, limit=limit)
        finally:
            _query_semaphore.release()

        audit_log(
            {
                "event": "sql_query",
                "request_id": request_id,
                "caller_key_id": key_id,
                "tool": name,
                "sql_hash": query_result.sql_hash,
                "duration_ms": query_result.duration_ms,
                "row_count": query_result.row_count,
                "status": "ok",
            }
        )
        return {
            "columns": query_result.columns,
            "rows": query_result.rows,
            "row_count": query_result.row_count,
            "duration_ms": query_result.duration_ms,
            "sql_hash": query_result.sql_hash,
            "applied_limit": query_result.applied_limit,
        }

    if name == "health_check":
        return {
            "bridge_ok": True,
            "db": db.health_check(),
            "policy": {
                "max_rows": settings.max_rows,
                "query_timeout_ms": settings.query_timeout_ms,
                "rate_limit_rpm": settings.rate_limit_rpm,
                "max_concurrent_queries": settings.max_concurrent_queries,
            },
        }

    raise BridgeHttpError(404, f"Unknown tool: {name}")


def _handle_mcp_request(payload: dict[str, Any], key_id: str, request_id: str) -> dict[str, Any]:
    rpc_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "openclaw-bridge-frappe", "version": "1.0.0"},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": TOOL_DEFINITIONS}}

    if method != "tools/call":
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }

    name = params.get("name")
    arguments = params.get("arguments") or {}

    try:
        result_data = _tool_payload(name, arguments, key_id, request_id)
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": mcp_result(result_data),
        }
    except BridgeHttpError as exc:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": mcp_result({"error": exc.detail}, is_error=True),
        }
    except (SqlValidationError, BridgeDbError) as exc:
        audit_log(
            {
                "event": "tool_call",
                "request_id": request_id,
                "caller_key_id": key_id,
                "tool": name,
                "status": "error",
                "error": str(exc),
            }
        )
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": mcp_result({"error": str(exc)}, is_error=True),
        }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def mcp() -> Response:
    request_id = str(uuid.uuid4())
    try:
        key_id = _verify_hmac_request()
        payload = _request_json()
        response = _json_response(_handle_mcp_request(payload, key_id, request_id))
    except BridgeHttpError as exc:
        response = _json_response({"detail": exc.detail, "request_id": request_id}, exc.status_code)
    except Exception as exc:
        frappe.logger().exception("OpenClaw Bridge MCP failure")
        response = _json_response({"detail": str(exc), "request_id": request_id}, 500)

    response.headers["X-Request-Id"] = request_id
    return response


@frappe.whitelist(allow_guest=True, methods=["GET"])
def mcp_sse() -> Response:
    request_id = str(uuid.uuid4())
    try:
        _verify_hmac_request()
    except BridgeHttpError as exc:
        response = _json_response({"detail": exc.detail, "request_id": request_id}, exc.status_code)
        response.headers["X-Request-Id"] = request_id
        return response

    rpc_path = "/api/method/openclaw_bridge.api.mcp"

    def event_stream():
        yield "event: endpoint\n"
        yield f"data: {rpc_path}\n\n"
        while True:
            time.sleep(15)
            yield "event: ping\n"
            yield "data: keepalive\n\n"

    response = _sse_response(event_stream())
    response.headers["X-Request-Id"] = request_id
    return response


@frappe.whitelist(allow_guest=True, methods=["GET"])
def health_check() -> Response:
    request_id = str(uuid.uuid4())
    try:
        key_id = _verify_hmac_request()
        payload = {
            "ok": True,
            "db": _db_client().health_check(),
            "policy": {
                "max_rows": settings.max_rows,
                "query_timeout_ms": settings.query_timeout_ms,
                "rate_limit_rpm": settings.rate_limit_rpm,
                "max_concurrent_queries": settings.max_concurrent_queries,
            },
        }
        audit_log({"event": "tool_call", "tool": "health_check", "caller_key_id": key_id, "status": "ok"})
        response = _json_response(payload)
    except BridgeHttpError as exc:
        response = _json_response({"detail": exc.detail, "request_id": request_id}, exc.status_code)
    except Exception as exc:
        frappe.logger().exception("OpenClaw Bridge health_check failure")
        response = _json_response({"detail": str(exc), "request_id": request_id}, 500)

    response.headers["X-Request-Id"] = request_id
    return response


@frappe.whitelist()
def bridge_config_summary():
    if "System Manager" not in frappe.get_roles():
        frappe.throw("Only System Manager can access this endpoint", frappe.PermissionError)

    return {
        "db_host": settings.db_host,
        "db_port": settings.db_port,
        "db_name": settings.db_name,
        "readonly_user": settings.db_user,
        "max_rows": settings.max_rows,
        "query_timeout_ms": settings.query_timeout_ms,
        "rate_limit_rpm": settings.rate_limit_rpm,
        "max_concurrent_queries": settings.max_concurrent_queries,
        "mcp_rpc_path": "/api/method/openclaw_bridge.api.mcp",
        "mcp_sse_path": "/api/method/openclaw_bridge.api.mcp_sse",
        "health_path": "/api/method/openclaw_bridge.api.health_check",
    }
