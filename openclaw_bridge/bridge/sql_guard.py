from __future__ import annotations

import re


class SqlValidationError(ValueError):
    pass


_BLOCKED_PATTERNS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bREPLACE\b",
    r"\bALTER\b",
    r"\bDROP\b",
    r"\bCREATE\b",
    r"\bTRUNCATE\b",
    r"\bRENAME\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bCOMMIT\b",
    r"\bROLLBACK\b",
    r"\bCALL\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bINTO\s+OUTFILE\b",
    r"\bLOAD_FILE\b",
    r"\bFOR\s+UPDATE\b",
    r"\bLOCK\s+TABLES\b",
]


def _strip_string_literals(sql: str) -> str:
    out = []
    in_single = False
    in_double = False
    for ch in sql:
        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(" ")
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            out.append(" ")
            continue
        if in_single or in_double:
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def validate_readonly_sql(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise SqlValidationError("SQL must be a non-empty string")

    stripped = sql.strip()
    if "--" in stripped or "/*" in stripped or "*/" in stripped or "#" in stripped:
        raise SqlValidationError("SQL comments are not allowed")

    semicolon_count = stripped.count(";")
    if semicolon_count > 1:
        raise SqlValidationError("Only one SQL statement is allowed")
    if semicolon_count == 1 and not stripped.endswith(";"):
        raise SqlValidationError("Only one SQL statement is allowed")

    if stripped.endswith(";"):
        stripped = stripped[:-1].rstrip()

    upper = stripped.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise SqlValidationError("Only SELECT/CTE queries are allowed")

    scrubbed = _strip_string_literals(upper)
    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, scrubbed):
            raise SqlValidationError(f"Blocked SQL pattern detected: {pattern}")

    return stripped
