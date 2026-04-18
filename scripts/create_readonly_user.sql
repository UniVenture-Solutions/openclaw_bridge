-- Run with: bench --site localhost mariadb < apps/openclaw_bridge/scripts/create_readonly_user.sql

CREATE USER IF NOT EXISTS 'openclaw_ro'@'192.168.18.107' IDENTIFIED BY 'REPLACE_WITH_STRONG_PASSWORD';
GRANT SELECT ON `_5adb37e1a356424b`.* TO 'openclaw_ro'@'192.168.18.107';
FLUSH PRIVILEGES;

SHOW GRANTS FOR 'openclaw_ro'@'192.168.18.107';
