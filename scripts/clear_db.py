"""
Elimina TODOS los registros de todas las tablas de la base de datos.

Desactiva la verificacion de FKs durante el proceso para evitar errores
de restriccion de integridad referencial, luego la reactiva.

Lee la configuracion de conexion desde .env:
  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

Uso:
  python scripts/clear_db.py           (pide confirmacion interactiva)
  python scripts/clear_db.py --yes     (omite confirmacion, util en CI)
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "comercial_db_test"),
}

# Orden seguro: tablas hijas antes que tablas padre
TABLES = [
    "caja",
    "pagos_proveedores",
    "pagos_clientes",
    "notas_credito_detalle",
    "notas_credito",
    "facturas_detalle",
    "facturas",
    "pedidos_detalle",
    "pedidos",
    "listas_precios_detalle",
    "listas_precios",
    "recepciones_detalle",
    "recepciones",
    "ordenes_compra_detalle",
    "ordenes_compra",
    "movimientos_inventario",
    "inventario",
    "usuarios_roles",
    "roles_permisos",
    "permisos",
    "roles",
    "usuarios",
    "parametros",
    "cuentas_bancarias",
    "formas_pago",
    "contactos",
    "direcciones",
    "terceros_tipos",
    "terceros",
    "tipos_identificacion",
    "productos_presentaciones",
    "productos",
    "unidades_medida",
    "marcas",
    "categorias",
    "empleados",
    "bodegas",
    "sucursales",
    "areas",
    "cargos",
    "empresas",
]


def main():
    skip_confirm = "--yes" in sys.argv
    db = DB_CONFIG["database"]

    if not skip_confirm:
        print(f"ADVERTENCIA: se eliminaran TODOS los registros de '{db}'@{DB_CONFIG['host']}.")
        confirmacion = input(f"Confirme escribiendo el nombre de la base de datos: ").strip()
        if confirmacion != db:
            print("Nombre incorrecto. Operacion cancelada.")
            sys.exit(0)

    print(f"\nConectando a '{db}'@{DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    conn = mysql.connector.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")

        total_eliminados = 0
        for tabla in TABLES:
            cur.execute(f"DELETE FROM `{tabla}`")
            n = cur.rowcount
            total_eliminados += n
            if n:
                print(f"  {tabla}: {n} fila(s)")

        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
        print(f"\nLimpieza completada — {total_eliminados} registros eliminados en total.")
    except Exception as exc:
        conn.rollback()
        print(f"\nError durante la limpieza: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
