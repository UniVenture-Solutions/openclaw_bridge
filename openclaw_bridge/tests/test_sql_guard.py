from openclaw_bridge.bridge.sql_guard import SqlValidationError, validate_readonly_sql


def test_accepts_basic_select():
    assert validate_readonly_sql("SELECT 1") == "SELECT 1"


def test_accepts_cte_with_trailing_semicolon():
    assert validate_readonly_sql("WITH x AS (SELECT 1) SELECT * FROM x;") == "WITH x AS (SELECT 1) SELECT * FROM x"


def test_rejects_non_select_sql():
    try:
        validate_readonly_sql("DELETE FROM tabUser")
        assert False
    except SqlValidationError as exc:
        assert "SELECT/CTE" in str(exc)


def test_rejects_multi_statement():
    try:
        validate_readonly_sql("SELECT 1; SELECT 2")
        assert False
    except SqlValidationError as exc:
        assert "one SQL statement" in str(exc)


def test_rejects_comment_bypass():
    try:
        validate_readonly_sql("SELECT 1 -- sneaky")
        assert False
    except SqlValidationError as exc:
        assert "comments" in str(exc)
