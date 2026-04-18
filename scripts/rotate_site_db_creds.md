# Rotate Site DB Credentials (After Bridge Cutover)

1. Update app DB user password in MariaDB.
2. Update `sites/localhost/site_config.json` with new password.
3. Restart bench services.
4. Verify ERP works and bridge still reads through `openclaw_ro`.

```bash
bench --site localhost mariadb -e "ALTER USER '_5adb37e1a356424b'@'192.168.18.107' IDENTIFIED BY 'NEW_STRONG_PASSWORD'; FLUSH PRIVILEGES;"
```
