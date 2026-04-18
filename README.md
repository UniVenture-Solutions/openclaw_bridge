## OpenClaw Bridge

`openclaw_bridge` is a reusable Frappe app that exposes a readonly MCP-compatible analytics interface for external AI clients such as OpenClaw.

Instead of adding custom nginx routes or standalone sidecar services, this app uses standard Frappe API method routes. That makes it portable across benches and easier to install, update, and maintain.

### Purpose

This app lets an external MCP client query analytics data from a Frappe / ERPNext MariaDB database while adding guardrails around how that data is accessed.

It is designed for:

- readonly analytics access
- remote MCP clients that speak JSON-RPC over HTTP
- deployment on ordinary Frappe benches without custom reverse-proxy edits

It is not intended for:

- write operations
- unrestricted SQL execution
- bypassing Frappe or database security controls

### Features

- MCP-compatible endpoints exposed through `/api/method/...`
- HMAC-based request authentication
- nonce replay protection
- rate limiting
- concurrent query limiting
- SQL validation that allows `SELECT` / `WITH` only
- readonly transaction execution
- table discovery and schema inspection tools
- audit logging for MCP requests and SQL activity
- install-time secret generation
- install-time readonly DB user provisioning when DB privileges allow it

### MCP Tools

The server exposes these tools:

- `list_tables`
  Lists queryable tables and views in the configured site database.
- `describe_table`
  Returns column metadata for a requested table.
- `run_sql_readonly`
  Executes validated readonly SQL with optional parameters and row limit.
- `health_check`
  Returns bridge and policy health information.

### Public API Routes

No custom nginx or supervisor wiring is required. Once the app is installed on a site, the public endpoints are:

- `POST /api/method/openclaw_bridge.api.mcp`
- `GET /api/method/openclaw_bridge.api.mcp_sse`
- `GET /api/method/openclaw_bridge.api.health_check`

There is also an admin-only helper:

- `GET /api/method/openclaw_bridge.api.bridge_config_summary`

### Authentication

Every MCP request must include these headers:

- `X-Key-Id`
- `X-Timestamp`
- `X-Nonce`
- `X-Signature`

The signature is lowercase hex `HMAC-SHA256` over:

```text
<METHOD>\n<PATH>\n<TIMESTAMP>\n<NONCE>\n<SHA256_HEX_OF_BODY>
```

The HMAC values are stored in site config:

- `openclaw_bridge_hmac_key_id`
- `openclaw_bridge_hmac_secret`
- `openclaw_bridge_audit_log_path` (optional override)

If these values do not exist during install, the app generates them automatically.

### Readonly Database Access

The bridge reads from the site MariaDB database using:

- `openclaw_bridge_readonly_user`
- `openclaw_bridge_readonly_password`
- `openclaw_bridge_readonly_host`

During install, the app attempts to create and grant this readonly DB user automatically.

If the current DB account does not have `CREATE USER` / `GRANT` privileges, install still succeeds and you can provision the readonly user separately using:

- [scripts/create_readonly_user.sql](scripts/create_readonly_user.sql)
- [scripts/rotate_site_db_creds.md](scripts/rotate_site_db_creds.md)

You can also provide elevated DB credentials in site config if you want install-time auto-provisioning to succeed on restricted benches:

- `openclaw_bridge_admin_db_user`
- `openclaw_bridge_admin_db_password`

### Installation

```bash
cd /path/to/bench
bench get-app <repo-url> --branch <branch>
bench --site <site> install-app openclaw_bridge
```

### How It Works

Requests arrive through Frappe's normal `/api/method/...` routing.

The app then:

1. verifies HMAC headers
2. blocks replayed nonces
3. applies request rate limits
4. validates MCP JSON-RPC payloads
5. validates SQL as readonly-only
6. executes queries inside readonly transaction settings
7. returns MCP-compatible JSON responses

### Security Model

This app reduces risk, but it does not remove it entirely. Broad analytics access still needs careful operational judgment.

Main protections:

- HMAC auth on every request
- readonly query validation
- no DDL / write SQL
- row and concurrency caps
- audit logging
- optional least-privilege readonly DB user

Recommended production setup:

- use a dedicated readonly DB user
- rotate the HMAC secret periodically
- keep `MAX_ROWS` conservative
- expose the endpoints only over HTTPS
- monitor audit logs

By default, audit logs are written to the current bench's `logs/openclaw_bridge_audit.log`. You can override that path with `openclaw_bridge_audit_log_path` in `site_config.json`.

### Development Notes

Runtime dependency:

- `pymysql`

Dev/test dependency:

- `pytest`

### Example OpenClaw Configuration

Example route layout for a site hosted at `https://example.com`:

- RPC: `https://example.com/api/method/openclaw_bridge.api.mcp`
- SSE: `https://example.com/api/method/openclaw_bridge.api.mcp_sse`
- Health: `https://example.com/api/method/openclaw_bridge.api.health_check`

### Repository Structure

- [openclaw_bridge/api.py](openclaw_bridge/api.py): Frappe-exposed MCP endpoints
- [openclaw_bridge/install.py](openclaw_bridge/install.py): install-time config and DB user provisioning
- [openclaw_bridge/bridge/db.py](openclaw_bridge/bridge/db.py): readonly database access
- [openclaw_bridge/bridge/sql_guard.py](openclaw_bridge/bridge/sql_guard.py): SQL validation
- [openclaw_bridge/bridge/settings.py](openclaw_bridge/bridge/settings.py): bridge config loading
- [openclaw_bridge/bridge/mcp.py](openclaw_bridge/bridge/mcp.py): MCP tool definitions

### License

`mit`
