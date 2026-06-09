"""
Crea (si no existe) la base de datos apuntada por DB_NAME en .env y aplica
el esquema completo desde db/create/01_create_schema.sql.

Idempotente: si las tablas ya existen las omite sin error.

Uso:
  python scripts/create_schema.py
  DB_NAME=comercial_db python scripts/create_schema.py
"""
import os
import re
import sys
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "comercial_db_test")
BASE_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}

SCHEMA_FILE = Path(__file__).parent.parent / "db" / "create" / "01_create_schema.sql"


def main():
    host = BASE_CONFIG["host"]
    port = BASE_CONFIG["port"]
    print(f"Creando esquema en '{DB_NAME}'@{host}:{port}...")

    conn = mysql.connector.connect(**BASE_CONFIG)
    cur = conn.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cur.close()
    conn.close()

    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    # Quitar el CREATE DATABASE y USE hardcodeados; el destino lo controla DB_NAME
    sql = re.sub(r'CREATE\s+DATABASE[^;]+;', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'USE\s+\S+\s*;', '', sql, flags=re.IGNORECASE)
    # Hacer idempotente: si la tabla ya existe la salta
    sql = re.sub(r'\bCREATE TABLE\b', 'CREATE TABLE IF NOT EXISTS', sql, flags=re.IGNORECASE)

    conn = mysql.connector.connect(**BASE_CONFIG, database=DB_NAME)
    conn.autocommit = True
    cur = conn.cursor()
    # FK_CHECKS=0 evita colisión de nombres de constraint en MariaDB (globales entre DBs)
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    created = skipped = 0
    for stmt in sql.split(';'):
        # Quitar líneas de comentario SQL; conservar solo el DDL
        lines = [ln for ln in stmt.splitlines() if not ln.strip().startswith('--')]
        stmt = '\n'.join(lines).strip()
        if not stmt:
            continue
        try:
            cur.execute(stmt)
            created += 1
        except mysql.connector.errors.DatabaseError as exc:
            print(f"  WARN: {exc}", file=sys.stderr)
            skipped += 1
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    cur.close()
    conn.close()
    print(f"  [OK] {created} sentencias ejecutadas, {skipped} omitidas.")


if __name__ == "__main__":
    main()
