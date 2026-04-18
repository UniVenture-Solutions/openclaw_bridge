from __future__ import annotations

import json
from typing import Any


TOOL_DEFINITIONS = [
    {
        "name": "list_tables",
        "description": "List all queryable tables/views in the configured database.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "describe_table",
        "description": "Describe columns for a table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_name": {"type": "string", "description": "Database table name"},
            },
            "required": ["table_name"],
        },
    },
    {
        "name": "run_sql_readonly",
        "description": "Run validated readonly SQL query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL query (SELECT/CTE only)"},
                "params": {
                    "type": ["object", "array", "null"],
                    "description": "Optional DB params for query",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Optional result row limit (capped by MAX_ROWS)",
                },
            },
            "required": ["sql"],
        },
    },
    {
        "name": "health_check",
        "description": "Bridge + DB health check with policy values.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]


def mcp_result(data: Any, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=True, default=str)}],
        "isError": is_error,
    }
