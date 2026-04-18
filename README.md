### OpenClaw Bridge (Frappe App)

Reusable Frappe app that exposes readonly MCP endpoints using standard Frappe API routes.

### What this app provides

- MCP tools:
  - `list_tables()`
  - `describe_table(table_name)`
  - `run_sql_readonly(sql, params?, limit?)`
  - `health_check()`
- HMAC auth using request headers
- Replay protection
- Rate limiting + concurrent query cap
- SQL validation for readonly analytics
- Audit logging

### Dependencies

Defined in `pyproject.toml` and `requirements.txt`:

- `pymysql`
- dev/test: `pytest`

### Installation

```bash
cd /home/frappe/dev-bench
bench get-app <repo-url> --branch version-16
bench --site <site> install-app openclaw_bridge
```

### Portable route pattern

No custom nginx or supervisor config is required.

Public MCP endpoints use standard Frappe method routes:

- `POST /api/method/openclaw_bridge.api.mcp`
- `GET /api/method/openclaw_bridge.api.mcp_sse`
- `GET /api/method/openclaw_bridge.api.health_check`

### Install-time setup

On install, the app automatically tries to:

- ensure `openclaw_bridge_hmac_key_id`
- ensure `openclaw_bridge_hmac_secret`
- create/update a readonly DB user when DB privileges allow it

If your DB account cannot create users, the app will still install cleanly and you can provision the readonly DB user separately.

### DB user setup (optional/manual fallback)

Use:

- `apps/openclaw_bridge/scripts/create_readonly_user.sql`
- `apps/openclaw_bridge/scripts/rotate_site_db_creds.md`

### Admin helper

System Manager only:

- `/api/method/openclaw_bridge.api.bridge_config_summary`
