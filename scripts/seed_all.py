"""
Pobla la base de datos con los datos de prueba de todos los módulos.

Los IDs de facturas se separan por rango para evitar conflictos de PK:
  901-905  -> módulo Ventas      (F-001..F-004, F-ANU)
  911-912  -> módulo Gerencial   (FG-001, FG-002)
  921-926  -> módulo Tesorería   (F-VIG, F-030, F-060, F-090, F-MAS, F-PAG)

Lee la configuración de conexión desde .env:
  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
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


def seed_base(cur):
    cur.execute("""
        INSERT INTO empresas (id, razon_social, ruc_rif, moneda)
        VALUES (901, 'Empresa Test SA', '1790000001001', 'USD')
    """)
    cur.execute("""
        INSERT INTO sucursales (id, id_empresa, nombre, codigo, estado)
        VALUES (901, 901, 'Sucursal Principal Test', 'SUC-T01', 1)
    """)
    cur.execute("""
        INSERT INTO bodegas (id, id_sucursal, nombre, codigo, estado)
        VALUES (901, 901, 'Bodega Principal Test', 'BOD-T01', 1)
    """)
    cur.execute("""
        INSERT INTO unidades_medida (id, nombre, abreviatura)
        VALUES (901, 'Unidad Test', 'UNT')
    """)
    cur.execute("""
        INSERT INTO marcas (id, nombre)
        VALUES (901, 'Marca Test')
    """)
    cur.execute("""
        INSERT INTO categorias (id, nombre)
        VALUES (901, 'Categoria Test')
    """)
    cur.execute("""
        INSERT INTO productos (id, id_categoria, id_marca, id_unidad_medida,
                               codigo, nombre, aplica_impuesto, porcentaje_impuesto, estado)
        VALUES (901, 901, 901, 901, 'PROD-T01', 'Producto Test Uno', 1, 12.00, 1)
    """)
    cur.execute("""
        INSERT INTO productos (id, id_categoria, id_marca, id_unidad_medida,
                               codigo, nombre, aplica_impuesto, porcentaje_impuesto, estado)
        VALUES (902, 901, 901, 901, 'PROD-T02', 'Producto Test Dos', 1, 12.00, 1)
    """)
    cur.execute("""
        INSERT INTO productos_presentaciones (id, id_producto, nombre, factor_conversion, estado)
        VALUES (901, 901, 'Unidad', 1.0000, 1)
    """)
    cur.execute("""
        INSERT INTO productos_presentaciones (id, id_producto, nombre, factor_conversion, estado)
        VALUES (902, 902, 'Unidad', 1.0000, 1)
    """)


def seed_terceros(cur):
    cur.execute("""
        INSERT INTO tipos_identificacion (id, nombre, codigo)
        VALUES (901, 'RUC Test', 'RUC')
    """)
    cur.execute("""
        INSERT INTO terceros (id, id_tipo_identificacion, numero_identificacion,
                              razon_social, estado)
        VALUES (901, 901, '1790000001001', 'Cliente Test SA', 1)
    """)
    cur.execute("""
        INSERT INTO terceros_tipos (id, id_tercero, tipo)
        VALUES (901, 901, 'cliente')
    """)
    cur.execute("""
        INSERT INTO terceros (id, id_tipo_identificacion, numero_identificacion,
                              razon_social, estado)
        VALUES (902, 901, '1790000002001', 'Proveedor Test SA', 1)
    """)
    cur.execute("""
        INSERT INTO terceros_tipos (id, id_tercero, tipo)
        VALUES (902, 902, 'proveedor')
    """)


def seed_formas_pago(cur):
    cur.executemany("""
        INSERT INTO formas_pago (id, nombre, tipo, requiere_referencia, estado)
        VALUES (%s, %s, %s, %s, %s)
    """, [
        (901, 'Efectivo Test',      'efectivo',      0, 1),
        (902, 'Transferencia Test', 'transferencia', 1, 1),
    ])


def seed_inventario(cur):
    """Producto 1 = 50 und, Producto 2 = 3 und (bajo minimo de 10)."""
    cur.executemany("""
        INSERT INTO inventario (id, id_producto, id_presentacion, id_bodega,
                                cantidad, cantidad_minima, cantidad_maxima)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, [
        (901, 901, 901, 901, 50.0000, 10.0000, 200.0000),
        (902, 902, 902, 901,  3.0000, 10.0000, 100.0000),
    ])


def seed_kardex(cur):
    """3 movimientos del Producto 1 en Bodega 901: +30, +20, -15 -> saldo 35."""
    cur.executemany("""
        INSERT INTO movimientos_inventario
            (id, id_producto, id_presentacion, id_bodega,
             tipo_movimiento, cantidad, cantidad_anterior, cantidad_posterior, costo_unitario)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        (901, 901, 901, 901, 'entrada', 30,  0, 30, 5.00),
        (902, 901, 901, 901, 'entrada', 20, 30, 50, 5.00),
        (903, 901, 901, 901, 'salida',  15, 50, 35, 5.00),
    ])


def seed_facturas_ventas(cur):
    """
    Facturas IDs 901-905:
      F-001..F-003 activas enero 2025, F-004 febrero, F-ANU anulada enero.
    Detalle IDs 901-903 para las tres facturas de enero.
    """
    cur.executemany("""
        INSERT INTO facturas
            (id, id_sucursal, id_cliente, numero, fecha_emision, fecha_vencimiento,
             estado, subtotal, descuento, impuesto, total, saldo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        (901, 901, 901, 'F-001', '2025-01-10', '2025-02-10', 'activa',   89.29, 0,  10.71,  100.00,  100.00),
        (902, 901, 901, 'F-002', '2025-01-15', '2025-02-15', 'activa',  178.57, 0,  21.43,  200.00,  200.00),
        (903, 901, 901, 'F-003', '2025-01-20', '2025-02-20', 'activa',  267.86, 0,  32.14,  300.00,  300.00),
        (904, 901, 901, 'F-004', '2025-02-05', '2025-03-05', 'activa',  891.96, 0, 107.04,  999.00,  999.00),
        (905, 901, 901, 'F-ANU', '2025-01-25', '2025-02-25', 'anulada', 446.43, 0,  53.57,  500.00,  500.00),
    ])
    cur.executemany("""
        INSERT INTO facturas_detalle
            (id, id_factura, id_producto, id_presentacion, id_bodega,
             cantidad, precio_unitario, descuento, subtotal, costo_unitario)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        (901, 901, 901, 901, 901,  5.0000, 20.00, 0, 100.00, 10.00),
        (902, 902, 901, 901, 901, 10.0000, 20.00, 0, 200.00, 10.00),
        (903, 903, 902, 902, 901, 15.0000, 20.00, 0, 300.00, 10.00),
    ])


def seed_facturas_gerencial(cur):
    """
    Facturas IDs 911-912:
      FG-001 enero 2025 (2 productos), FG-002 diciembre 2024 (1 producto).
    Detalle IDs 911-913.
    """
    cur.execute("""
        INSERT INTO facturas
            (id, id_sucursal, id_cliente, numero, fecha_emision, fecha_vencimiento,
             estado, subtotal, descuento, impuesto, total, saldo)
        VALUES (911, 901, 901, 'FG-001', '2025-01-10', '2025-02-10',
                'activa', 2321.43, 0, 278.57, 2600.00, 2600.00)
    """)
    cur.executemany("""
        INSERT INTO facturas_detalle
            (id, id_factura, id_producto, id_presentacion, id_bodega,
             cantidad, precio_unitario, descuento, subtotal, costo_unitario)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        (911, 911, 901, 901, 901, 100.0000, 20.00, 0, 2000.00, 8.00),
        (912, 911, 902, 902, 901,  30.0000, 20.00, 0,  600.00, 8.00),
    ])
    cur.execute("""
        INSERT INTO facturas
            (id, id_sucursal, id_cliente, numero, fecha_emision, fecha_vencimiento,
             estado, subtotal, descuento, impuesto, total, saldo)
        VALUES (912, 901, 901, 'FG-002', '2024-12-15', '2025-01-15',
                'activa', 892.86, 0, 107.14, 1000.00, 1000.00)
    """)
    cur.execute("""
        INSERT INTO facturas_detalle
            (id, id_factura, id_producto, id_presentacion, id_bodega,
             cantidad, precio_unitario, descuento, subtotal, costo_unitario)
        VALUES (913, 912, 901, 901, 901, 50.0000, 20.00, 0, 1000.00, 8.00)
    """)


def seed_ordenes_compra(cur):
    """
    Ordenes IDs 901-905:
      OC-001..OC-003 aprobadas enero, OC-004 aprobada febrero, OC-CAN cancelada enero.
    """
    cur.executemany("""
        INSERT INTO ordenes_compra
            (id, id_sucursal, id_proveedor, id_bodega_destino, numero, fecha_emision,
             estado, subtotal, descuento, impuesto, total)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        (901, 901, 902, 901, 'OC-001', '2025-01-05', 'aprobada', 446.43, 0,  53.57,  500.00),
        (902, 901, 902, 901, 'OC-002', '2025-01-12', 'aprobada', 267.86, 0,  32.14,  300.00),
        (903, 901, 902, 901, 'OC-003', '2025-01-20', 'aprobada', 178.57, 0,  21.43,  200.00),
        (904, 901, 902, 901, 'OC-004', '2025-02-03', 'aprobada', 891.96, 0, 107.04,  999.00),
        (905, 901, 902, 901, 'OC-CAN', '2025-01-08', 'cancelada', 89.29, 0,  10.71,  100.00),
    ])


def seed_cxc(cur):
    """
    Facturas IDs 921-926 para cuentas por cobrar al corte 2025-03-01:
      F-VIG vigente, F-030/060/090/MAS en distintos rangos, F-PAG pagada (saldo=0).
    """
    cur.executemany("""
        INSERT INTO facturas
            (id, id_sucursal, id_cliente, numero, fecha_emision, fecha_vencimiento,
             estado, total, saldo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        (921, 901, 901, 'F-VIG', '2025-01-10', '2025-03-15', 'activa',  500.00, 500.00),
        (922, 901, 901, 'F-030', '2025-01-10', '2025-02-10', 'activa',  200.00, 200.00),
        (923, 901, 901, 'F-060', '2025-01-10', '2025-01-20', 'activa',  300.00, 300.00),
        (924, 901, 901, 'F-090', '2024-12-01', '2024-12-30', 'vencida', 400.00, 400.00),
        (925, 901, 901, 'F-MAS', '2024-10-01', '2024-11-01', 'vencida', 100.00, 100.00),
        (926, 901, 901, 'F-PAG', '2025-01-01', '2025-02-01', 'pagada',  999.00,   0.00),
    ])


def seed_pagos_clientes(cur):
    """3 cobros en enero 2025 sobre las facturas CxC (IDs 921-923)."""
    cur.executemany("""
        INSERT INTO pagos_clientes
            (id, id_factura, id_cliente, id_forma_pago, fecha_pago, monto)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, [
        (901, 921, 901, 901, '2025-01-15', 150.00),
        (902, 922, 901, 901, '2025-01-20', 200.00),
        (903, 923, 901, 901, '2025-01-28',  50.00),
    ])


SEEDERS = [
    ("Entidades base (empresa, sucursal, bodega, productos)", seed_base),
    ("Terceros (cliente y proveedor)",                        seed_terceros),
    ("Formas de pago",                                        seed_formas_pago),
    ("Inventario (stock inicial)",                            seed_inventario),
    ("Kardex (movimientos inventario)",                       seed_kardex),
    ("Facturas ventas (IDs 901-905) + detalle",               seed_facturas_ventas),
    ("Facturas gerenciales (IDs 911-912) + detalle",          seed_facturas_gerencial),
    ("Ordenes de compra (IDs 901-905)",                       seed_ordenes_compra),
    ("Facturas CxC tesoreria (IDs 921-926)",                  seed_cxc),
    ("Pagos clientes (cobros enero 2025)",                     seed_pagos_clientes),
]


def main():
    db = DB_CONFIG["database"]
    print(f"Conectando a '{db}'@{DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    conn = mysql.connector.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        for nombre, fn in SEEDERS:
            fn(cur)
            print(f"  [OK] {nombre}")
        conn.commit()
        print(f"\nSeed completado — {len(SEEDERS)} grupos insertados.")
    except Exception as exc:
        conn.rollback()
        print(f"\nError durante el seed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
