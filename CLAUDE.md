# comercial-DB — Referencia de comandos

Proyecto: base de datos MySQL de empresa comercial con sucursales, inventario, ventas, compras y tesorería.
Conexión configurada en `.env` (ver `.env.example`).

**`.env` por defecto apunta a `comercial_db_test`** (DB de tests). Para trabajar con la DB de desarrollo
(`comercial_db`) hay que sobreescribir `$env:DB_NAME="comercial_db"` en la sesión.

---

## Base de datos

### Crear el esquema completo

```powershell
# Crea la DB apuntada por .env (comercial_db_test) si no existe y aplica el esquema.
# Idempotente: re-ejecutar no falla si las tablas ya existen.
py scripts/create_schema.py
```

Para crear el esquema en la DB de desarrollo:

```powershell
$env:DB_NAME="comercial_db"; py scripts/create_schema.py
```

También se puede usar el cliente MySQL directamente (si está disponible en PATH):

```sql
-- En cliente MySQL (mysql CLI, DBeaver, etc.)
SOURCE db/create/01_create_schema.sql;
```

---

## Scripts Python

### Limpiar toda la base de datos

```powershell
# Con confirmación interactiva (escribe el nombre de la DB para confirmar)
py scripts/clear_db.py

# Sin confirmación — útil en CI o flujos automatizados
py scripts/clear_db.py --yes
```

Elimina **todos los registros** de todas las tablas en orden seguro (hijos antes que padres), desactivando FK checks. **Destructivo e irreversible** en la DB apuntada por `.env`.

---

### Poblar con datos de prueba mínimos (seed_all)

```powershell
py scripts/seed_all.py
```

Inserta un conjunto pequeño y fijo de datos de prueba (IDs en rango 901-926) para todos los módulos: empresa, sucursal, bodega, productos, clientes, proveedor, formas de pago, inventario, kardex, facturas de ventas, facturas gerenciales, órdenes de compra, cuentas por cobrar y pagos de clientes.

Usa la base de datos definida en `.env` (`DB_NAME`, por defecto `comercial_db_test`).

> **Nota:** `seed_all` es para inspección manual de datos. **No ejecutar antes de `pytest`** — los tests
> crean sus propios datos mediante fixtures y usan los mismos IDs (901-926); correr `seed_all` primero
> causa errores de clave duplicada en los fixtures.

---

### Poblar con datos masivos realistas (seed_massive)

`seed_massive` está diseñado para la DB de desarrollo (`comercial_db`). Siempre sobreescribir `DB_NAME`:

```powershell
# Con escala por defecto (SCALE=100)
$env:DB_NAME="comercial_db"; py scripts/seed_massive.py

# Con escala 10× (SCALE=1000)
$env:DB_NAME="comercial_db"; $env:SEED_SCALE=1000; py scripts/seed_massive.py

# Semilla aleatoria distinta en cada ejecución
$env:DB_NAME="comercial_db"; $env:SEED_RANDOM=0; py scripts/seed_massive.py

# Limpiar primero y luego poblar en un solo flujo
$env:DB_NAME="comercial_db"
py scripts/clear_db.py --yes; if ($?) { py scripts/seed_massive.py }
```

Genera datos realistas con Faker (`es_ES`). Con `SCALE=100` produce aprox.:
- 200 productos, 280 presentaciones
- 100 clientes, 20 proveedores, 100 empleados
- 200 órdenes de compra, 160 recepciones
- 500 facturas + escenarios de borde (ver `docs/seed_scenarios.md`)
- ~200 pagos de clientes, ~140 pagos a proveedores

Inyecta 10 escenarios de prueba de negocio (ESC-01..ESC-10).

Variables de entorno relevantes (definir en `.env` o en la sesión):

| Variable      | Default | Efecto |
|---------------|---------|--------|
| `DB_NAME`     | `comercial_db_test` (desde `.env`) | DB destino — sobreescribir con `comercial_db` |
| `SEED_SCALE`  | `100`   | Multiplicador de volumen |
| `SEED_RANDOM` | `42`    | Semilla aleatoria; `0` = aleatorio real |

---

## Tests

### Ejecutar todos los tests

```powershell
pytest
```

### Ejecutar un módulo específico

```powershell
pytest tests/reportes/test_inventario.py
pytest tests/reportes/test_ventas.py
pytest tests/reportes/test_compras.py
pytest tests/reportes/test_gerenciales.py
pytest tests/reportes/test_tesoreria.py
```

### Con salida detallada y parar en primer fallo

```powershell
pytest -v --tb=short -x
```

### Filtrar por nombre de test o clase

```powershell
pytest -k "kardex"
pytest -k "TestStockPorBodega"
pytest -k "not tesoreria"
```

### Ver cobertura (si pytest-cov está instalado)

```powershell
pytest --cov=tests --cov-report=term-missing
```

Los tests usan `comercial_db_test` (`.env` → `DB_NAME`). Cada test corre en una transacción que se revierte automáticamente (`conftest.py` → fixture `rollback`), por lo que no dejan datos residuales.

---

## Flujos completos frecuentes

### Ciclo completo de pruebas desde cero

```powershell
# 1. Crear esquema en DB de test (si no existe)
py scripts/create_schema.py

# 2. Limpiar datos previos
py scripts/clear_db.py --yes

# 3. Correr todos los tests
pytest
```

### Inspeccionar DB de test con datos mínimos (seed manual)

```powershell
py scripts/clear_db.py --yes
py scripts/seed_all.py
# Ahora puedes explorar comercial_db_test con DBeaver u otro cliente
```

### Inspeccionar DB de desarrollo (datos masivos)

```powershell
# Crear esquema en comercial_db si no existe
$env:DB_NAME="comercial_db"; py scripts/create_schema.py

# Limpiar y repoblar con escala 1000
$env:DB_NAME="comercial_db"; $env:SEED_SCALE=1000
py scripts/clear_db.py --yes; if ($?) { py scripts/seed_massive.py }
```

---

## Consultas SQL de referencia

Los archivos en `tests/queries/` son queries parametrizadas usadas por los tests pero también ejecutables directamente:

| Archivo | Qué consulta |
|---------|-------------|
| `tests/queries/inventario.sql` | Stock actual por bodega |
| `tests/queries/productos_bajo_minimo.sql` | Productos con stock < mínimo |
| `tests/queries/kardex.sql` | Movimientos de inventario (kardex) por producto y período |
| `tests/queries/ventas_por_periodo.sql` | Facturas y totales por rango de fechas |
| `tests/queries/ventas_por_producto.sql` | Ranking de ventas y margen por producto |
| `tests/queries/compras_por_proveedor.sql` | Órdenes de compra agrupadas por proveedor |
| `tests/queries/top_productos_vendidos.sql` | Top N productos más vendidos |
| `tests/queries/cuentas_por_cobrar.sql` | Cartera por cobrar con antigüedad |

---

## Escenarios de prueba inyectados por seed_massive

Ver `docs/seed_scenarios.md` para descripción completa. Resumen:

| ESC | Escenario |
|-----|-----------|
| 01 | Cliente moroso — 15 facturas vencidas +90 días sin cobrar |
| 02 | Stock bajo mínimo — 5 productos al 20% de su mínimo |
| 03 | Proveedor inactivo — sin OC en 200 días |
| 04 | Pico estacional — 20% de facturas en diciembre |
| 05 | Sucursal bajo rendimiento — Cuenca con solo 5% de ventas |
| 06 | Stock en cero con demanda reciente — 3 productos |
| 07 | Notas de crédito pendientes — 8 notas activas |
| 08 | Recepciones parciales — ~15% de OC aprobadas |
| 09 | Cartera parcialmente cobrada — 30% de facturas activas con pago parcial |
| 10 | Producto top-seller — `PROD-00001` con líneas extra en SCALE/2 facturas |
