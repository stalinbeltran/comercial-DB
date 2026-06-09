# Escenarios de Prueba — seed_massive.py

Datos insertados intencionalmente para cubrir casos de borde, alertas y reportes críticos del negocio.

---

## ESC-01 — Cliente Moroso

**Descripción:** Un cliente específico (`terceros.id = cli_ids[-1]`, el último cliente insertado) acumula 15 facturas en estado `vencida` con más de 90 días de antigüedad y saldo igual al total (ningún pago recibido).

**Datos insertados:** IDs de facturas 90001–90015, serie `FAC-MOR-00001` a `FAC-MOR-00015`.

**Consultas que lo activan:**
- Reporte de cuentas por cobrar (rango `+90 días`)
- Ranking de clientes por cartera vencida
- Alerta de riesgo crediticio

---

## ESC-02 — Stock Bajo Mínimo

**Descripción:** 5 productos aleatorios tienen su `inventario.cantidad` reducida al 20% de su `cantidad_minima`.

**Implementación:** `UPDATE inventario SET cantidad = cantidad_minima * 0.2 WHERE id_producto = X LIMIT 1`

**Consultas que lo activan:**
- Reporte `productos_bajo_minimo.sql`
- Alerta de reposición de inventario

---

## ESC-03 — Proveedor Inactivo

**Descripción:** El penúltimo proveedor insertado tiene todas sus órdenes de compra con `fecha_emision` en una fecha mayor a 200 días en el pasado, simulando inactividad por más de 6 meses.

**Consultas que lo activan:**
- Análisis de proveedores activos/inactivos
- Evaluación de base de proveedores

---

## ESC-04 — Pico Estacional en Diciembre

**Descripción:** El 20% del total de facturas se concentra en el período diciembre 2025 (rango `2025-12-01` a `2025-12-31`), generando aproximadamente 3–4× el volumen mensual promedio.

**Implementación:** El generador crea `n_fac // 5` facturas en ese período y `n_fac * 4 / 5` distribuidas en el resto del año.

**Consultas que lo activan:**
- Comparativo de ventas por mes
- Análisis estacional de demanda

---

## ESC-05 — Sucursal Bajo Rendimiento

**Descripción:** La Sucursal Cuenca (id=3) recibe solo el 5% de las facturas, mientras Quito y Guayaquil se distribuyen el 95% restante (47% y 48% respectivamente).

**Implementación:** `random.choices(suc_ids, weights=[47, 48, 5])` en cada factura.

**Consultas que lo activan:**
- Ventas por sucursal
- Comparativo de rendimiento entre sucursales
- Análisis de rentabilidad por punto de venta

---

## ESC-06 — Stock en Cero con Demanda Reciente

**Descripción:** 3 productos distintos a los de ESC-02 tienen `inventario.cantidad = 0`, pero aparecen en facturas recientes del volumen general, generando una ruptura de stock detectable.

**Implementación:** `UPDATE inventario SET cantidad=0 WHERE id_producto=X LIMIT 1`

**Consultas que lo activan:**
- Stock por bodega (muestra cantidad=0)
- Cruce con facturas recientes para detectar ventas sin stock

---

## ESC-07 — Notas de Crédito Pendientes

**Descripción:** 8 notas de crédito en estado `activa` asociadas a facturas distintas, con montos entre el 10% y el 40% del total de la factura original. Motivos variados (devolución, error de precio, producto defectuoso).

**Datos insertados:** IDs `1` a `8` en tablas `notas_credito` y `notas_credito_detalle`.

**Consultas que lo activan:**
- Listado de notas de crédito pendientes de aplicar
- Cartera neta de ventas (descontando NCs)

---

## ESC-08 — Órdenes de Compra con Recepción Parcial

**Descripción:** Aproximadamente el 15% de las órdenes de compra en estado `aprobada` tienen recepciones con `estado = 'parcial'`, donde `cantidad_recibida < cantidad` en el detalle de recepción.

**Implementación:** `if random.random() < 0.15: est_rec = "parcial"; qty_rec = qty_esp * uniform(0.5, 0.9)`

**Consultas que lo activan:**
- Órdenes de compra pendientes de recepción completa
- Análisis de cumplimiento de proveedores

---

## ESC-09 — Cartera Parcialmente Cobrada

**Descripción:** El 30% de las facturas en estado `activa` tienen al menos un pago parcial registrado en `pagos_clientes`, con un monto entre el 20% y el 80% del total de la factura. El `saldo` original en la factura no se actualiza automáticamente (queda igual al `total`), lo que permite detectar la diferencia total vs cobrado en reportes.

**Consultas que lo activan:**
- Cuentas por cobrar vs cobros realizados
- Reporte de efectividad de cobranza

---

## ESC-10 — Producto Top Seller

**Descripción:** El primer producto insertado (`prod_ids[0]`, código `PROD-00001`) aparece en líneas extra de `facturas_detalle` asociadas a `SCALE/2` facturas activas, con cantidades de 5 a 50 unidades por línea. Esto lo convierte en el producto con mayor volumen de ventas.

**Datos insertados:** IDs de detalle 80001–80(SCALE/2) en `facturas_detalle`.

**Consultas que lo activan:**
- Top N productos más vendidos
- Análisis ABC de inventario
- Reporte de márgenes por producto

---

## Resumen de Volúmenes (SCALE=100)

| Tabla                     | Registros aprox. |
|---------------------------|-----------------|
| productos                 | 200             |
| productos_presentaciones  | 280             |
| terceros (clientes)       | 100             |
| terceros (proveedores)    | 20              |
| empleados                 | 100             |
| ordenes_compra            | 200             |
| ordenes_compra_detalle    | 600             |
| recepciones               | 160             |
| recepciones_detalle       | 480             |
| inventario                | 600             |
| movimientos_inventario    | 1 200+          |
| facturas                  | 500 + 15 (ESC-01)|
| facturas_detalle          | 1 500 + 50 (ESC-10)|
| notas_credito             | 8 (ESC-07)      |
| pagos_clientes            | ~200            |
| pagos_proveedores         | ~140            |
| caja                      | ~200            |

Con `SEED_SCALE=1000` todos los valores se multiplican ~10×.

---

## Uso

```bash
# Poblar con escala por defecto (100)
python scripts/seed_massive.py

# Poblar con 1000 registros base
SEED_SCALE=1000 python scripts/seed_massive.py

# Limpiar todo primero, luego poblar
python scripts/clear_db.py --yes && python scripts/seed_massive.py
```
