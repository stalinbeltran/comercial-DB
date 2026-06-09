"""
seed_massive.py — Genera datos realistas a escala para comercial_db.

Parámetros .env:
  SEED_SCALE   Multiplicador de volumen (default: 100).
               Con 100 → ~200 productos, ~500 facturas, ~200 OC, etc.
               Con 1000 → 10x todo.
  SEED_RANDOM  Semilla aleatoria; 0 = aleatorio real (default: 42).
"""
import os, sys, itertools, random
from datetime import date, timedelta
import mysql.connector
from faker import Faker
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "comercial_db"),
}
SCALE  = int(os.getenv("SEED_SCALE", 100))
_SEED  = int(os.getenv("SEED_RANDOM", 42))
if _SEED:
    random.seed(_SEED)
fake = Faker("es_ES")
if _SEED:
    Faker.seed(_SEED)

TODAY  = date.today()
D_INI  = date(2023, 1, 1)
D_FIN  = date(2025, 12, 31)

# ---------------------------------------------------------------------------
# Generadores
# ---------------------------------------------------------------------------
_ced_seq  = itertools.count(1710000001)
_ruc_seq  = itertools.count(1790100001)

def next_ced():  return str(next(_ced_seq))
def next_ruc():  return str(next(_ruc_seq)) + "001"

def r2(v):       return round(float(v), 2)

def gen_tel():
    return f"09{random.randint(10_000_000, 99_999_999)}"

def gen_email(slug: str) -> str:
    dom = random.choice(["gmail.com","hotmail.com","outlook.com","empresa.ec"])
    s = "".join(c for c in slug.lower()[:12] if c.isalpha())
    return f"{s or 'user'}{random.randint(1,999)}@{dom}"

def gen_fecha(ini: date = D_INI, fin: date = D_FIN) -> date:
    return ini + timedelta(days=random.randint(0, (fin - ini).days))

def gen_num_doc(prefijo: str, n: int, pad: int = 5) -> str:
    return f"{prefijo}-{str(n).zfill(pad)}"

def bulk(cur, sql: str, rows: list, batch: int = 500) -> int:
    for i in range(0, len(rows), batch):
        cur.executemany(sql, rows[i:i+batch])
    return len(rows)

def calc_totales(lineas):
    """lineas = list[(cantidad, precio_unit, descuento_total, pct_imp)]
    Retorna (subtotal, descuento, impuesto, total)"""
    sub  = r2(sum(q * p - d for q, p, d, _ in lineas))
    desc = r2(sum(d for _, _, d, _ in lineas))
    imp  = r2(sum(q * p * pct / 100 for q, p, _, pct in lineas))
    tot  = r2(sub + imp)
    return sub, desc, imp, tot


# ---------------------------------------------------------------------------
# 1. Catálogos (IDs fijos)
# ---------------------------------------------------------------------------
def seed_catalogos(cur):
    unidades = [
        (1,"Unidad","UN"),(2,"Kilogramo","KG"),(3,"Libra","LB"),
        (4,"Litro","LT"),(5,"Metro","MT"),(6,"Caja","CJ"),
        (7,"Paquete","PQ"),(8,"Rollo","RL"),(9,"Par","PR"),
        (10,"Docena","DZ"),(11,"Gramo","GR"),(12,"Mililitro","ML"),
        (13,"Metro Cuadrado","M2"),(14,"Metro Cúbico","M3"),(15,"Tonelada","TN"),
    ]
    bulk(cur, "INSERT INTO unidades_medida (id,nombre,abreviatura) VALUES (%s,%s,%s)", unidades)

    marcas_nm = [
        "ProTech","EliteMax","BrandX","NovaPro","TechLine","AquaFlow","EcoGreen",
        "MetalMax","UltraFit","SuperBrand","PowerPlus","FlexiPro","NaturalLine",
        "CraftPro","TechVision","BlueLine","RedMax","GoldStar","SilverEdge","PlatinumX",
        "ValueBrand","PrimeLine","ApexPro","CoreMax","ZenithPro","VanguardX",
        "TitanPro","FusionMax","OmegaLine","SpectraPro",
    ]
    marcas = [(i+1, m) for i, m in enumerate(marcas_nm)]
    bulk(cur, "INSERT INTO marcas (id,nombre) VALUES (%s,%s)", marcas)

    cats = [
        (1,None,"Electrónica"),(2,None,"Alimentos"),(3,None,"Ferretería"),
        (4,None,"Ropa y Calzado"),(5,None,"Hogar"),(6,None,"Oficina"),
        (7,1,"Computación"),(8,1,"Telefonía"),(9,1,"Audio y Video"),
        (10,2,"Bebidas"),(11,2,"Alimentos Secos"),(12,2,"Lácteos"),
        (13,3,"Herramientas"),(14,3,"Materiales"),(15,5,"Muebles"),
    ]
    bulk(cur, "INSERT INTO categorias (id,id_categoria_padre,nombre) VALUES (%s,%s,%s)", cats)

    tipos = [(1,"Cédula","CED"),(2,"RUC","RUC"),(3,"Pasaporte","PAS")]
    bulk(cur, "INSERT INTO tipos_identificacion (id,nombre,codigo) VALUES (%s,%s,%s)", tipos)

    fps = [
        (1,"Efectivo","efectivo",0,1),
        (2,"Tarjeta Crédito","tarjeta",1,1),
        (3,"Tarjeta Débito","tarjeta",1,1),
        (4,"Transferencia Bancaria","transferencia",1,1),
        (5,"Cheque","cheque",1,1),
        (6,"Crédito Directo","credito",0,1),
    ]
    bulk(cur, "INSERT INTO formas_pago (id,nombre,tipo,requiere_referencia,estado) VALUES (%s,%s,%s,%s,%s)", fps)

    print("  [OK] catálogos")
    return {
        "u_ids":  [r[0] for r in unidades],
        "m_ids":  [r[0] for r in marcas],
        "cat_hoja_ids": [r[0] for r in cats if r[1] is not None],
        "fp_ids": [r[0] for r in fps],
    }


# ---------------------------------------------------------------------------
# 2. Organización
# ---------------------------------------------------------------------------
def seed_organizacion(cur):
    cur.execute("""INSERT INTO empresas (id,razon_social,ruc_rif,moneda)
                   VALUES (1,'Comercial Ecuador S.A.','1791000000001','USD')""")

    areas_nm = ["Ventas","Compras","Bodega","Finanzas","Gerencia","Sistemas","RRHH","Marketing"]
    areas = [(i+1,1,n) for i,n in enumerate(areas_nm)]
    bulk(cur, "INSERT INTO areas (id,id_empresa,nombre) VALUES (%s,%s,%s)", areas)

    cargos_nm = [
        "Gerente General","Jefe de Ventas","Vendedor","Jefe de Compras",
        "Bodeguero","Contador","Cajero","Mensajero","Asistente Administrativo","Supervisor",
    ]
    cargos = [(i+1,1,n) for i,n in enumerate(cargos_nm)]
    bulk(cur, "INSERT INTO cargos (id,id_empresa,nombre) VALUES (%s,%s,%s)", cargos)

    ciudades = [("Quito","SUC-001"),("Guayaquil","SUC-002"),("Cuenca","SUC-003")]
    sucursales = [(i+1,1,f"Sucursal {c}",cod,1) for i,(c,cod) in enumerate(ciudades)]
    bulk(cur, "INSERT INTO sucursales (id,id_empresa,nombre,codigo,estado) VALUES (%s,%s,%s,%s,%s)", sucursales)

    bodegas = []
    suc_bods = {}
    bid = 1
    for sid,_,snm,_,_ in sucursales:
        suc_bods[sid] = []
        for j in range(2):
            tipo = "Principal" if j == 0 else "Secundaria"
            bodegas.append((bid, sid, f"Bodega {tipo} {snm}", f"BOD-{str(bid).zfill(3)}", 1))
            suc_bods[sid].append(bid)
            bid += 1
    bulk(cur, "INSERT INTO bodegas (id,id_sucursal,nombre,codigo,estado) VALUES (%s,%s,%s,%s,%s)", bodegas)

    bancos = ["Banco Pichincha","Banco Guayaquil","Produbanco"]
    cuentas = [
        (i+1,1,b,f"220{random.randint(1_000_000,9_999_999)}","corriente","USD",0.00,1)
        for i,b in enumerate(bancos)
    ]
    bulk(cur, """INSERT INTO cuentas_bancarias
        (id,id_empresa,banco,numero_cuenta,tipo_cuenta,moneda,saldo_actual,estado)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", cuentas)

    suc_ids   = [s[0] for s in sucursales]
    area_ids  = [a[0] for a in areas]
    cargo_ids = [c[0] for c in cargos]
    emp_rows  = []
    for i in range(SCALE):
        eid = i + 1
        nm  = fake.first_name()
        ap  = fake.last_name()
        emp_rows.append((
            eid, random.choice(suc_ids), random.choice(area_ids), random.choice(cargo_ids),
            nm, ap, "cedula", next_ced(),
            gen_email(f"{nm}{ap}"),
            gen_tel(),
            str(gen_fecha(date(2015,1,1), date(2023,12,31))), 1,
        ))
    bulk(cur, """INSERT INTO empleados
        (id,id_sucursal,id_area,id_cargo,nombres,apellidos,tipo_identificacion,
         numero_identificacion,email,telefono,fecha_ingreso,estado)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", emp_rows)

    roles_d = [(1,"Administrador"),(2,"Vendedor"),(3,"Bodeguero"),(4,"Contador"),(5,"Consulta")]
    bulk(cur, "INSERT INTO roles (id,nombre) VALUES (%s,%s)", roles_d)
    n_usr = max(5, SCALE // 20)
    usr_rows = []
    for i in range(n_usr):
        uid = i + 1
        nm  = fake.first_name().lower()
        usr_rows.append((uid, None, f"user{uid:04d}", gen_email(nm),
                         "hash_placeholder", fake.name(), "activo"))
    bulk(cur, """INSERT INTO usuarios (id,id_empleado,username,email,password_hash,nombre_completo,estado)
        VALUES (%s,%s,%s,%s,%s,%s,%s)""", usr_rows)
    ur_rows = [(i+1, u[0], random.choice([r[0] for r in roles_d]), None) for i,u in enumerate(usr_rows)]
    bulk(cur, "INSERT INTO usuarios_roles (id,id_usuario,id_rol,id_sucursal) VALUES (%s,%s,%s,%s)", ur_rows)

    print(f"  [OK] organización ({SCALE} empleados, {n_usr} usuarios, 3 sucursales, 6 bodegas)")
    return {
        "suc_ids":   suc_ids,
        "bod_ids":   [b[0] for b in bodegas],
        "suc_bods":  suc_bods,
        "emp_ids":   [e[0] for e in emp_rows],
        "cuenta_ids": [c[0] for c in cuentas],
        "usr_ids":   [u[0] for u in usr_rows],
    }


# ---------------------------------------------------------------------------
# 3. Productos
# ---------------------------------------------------------------------------
def seed_productos(cur, cat):
    n_prod = SCALE * 2
    adjs = ["Premium","Pro","Max","Lite","Ultra","Standard","Basic","Plus","Elite","Mini"]
    tipos = [
        "Cable","Sensor","Monitor","Teclado","Cámara","Disco","Memoria","Batería","Cargador",
        "Botella","Filtro","Herramienta","Tornillo","Tubo","Válvula","Lámpara","Ventilador",
        "Motor","Bomba","Tanque","Conector","Panel","Switch","Router","Impresora",
    ]
    pcts = [0.0, 12.0, 15.0]
    prods = []
    for i in range(n_prod):
        pid = i + 1
        nm  = f"{random.choice(adjs)} {random.choice(tipos)} {random.randint(100,999)}"
        pct = random.choice(pcts)
        prods.append((
            pid,
            random.choice(cat["cat_hoja_ids"]),
            random.choice(cat["m_ids"]),
            random.choice(cat["u_ids"]),
            f"PROD-{str(pid).zfill(5)}",
            nm, 1 if pct > 0 else 0, pct, 1,
        ))
    bulk(cur, """INSERT INTO productos
        (id,id_categoria,id_marca,id_unidad_medida,codigo,nombre,
         aplica_impuesto,porcentaje_impuesto,estado)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", prods)

    pres_rows   = []
    pres_by_prod = {}
    pid_pres = 1
    pres_opts = [("Unidad",1.0),("Caja x12",12.0),("Paquete x6",6.0),("Docena",12.0)]
    for p in prods:
        prod_id = p[0]
        pres_by_prod[prod_id] = []
        n_p = random.choices([1, 2], weights=[65, 35])[0]
        selected = [pres_opts[0]] + (random.sample(pres_opts[1:], 1) if n_p > 1 else [])
        for nm_p, fc in selected:
            pres_rows.append((pid_pres, prod_id, nm_p, fc, 1))
            pres_by_prod[prod_id].append((pid_pres, fc))
            pid_pres += 1
    bulk(cur, """INSERT INTO productos_presentaciones
        (id,id_producto,nombre,factor_conversion,estado) VALUES (%s,%s,%s,%s,%s)""", pres_rows)

    costo_by_prod = {p[0]: r2(random.uniform(2.0, 150.0)) for p in prods}
    pct_by_prod   = {p[0]: p[7] for p in prods}
    prod_ids = [p[0] for p in prods]

    print(f"  [OK] productos ({n_prod} productos, {len(pres_rows)} presentaciones)")
    return {
        "prod_ids":     prod_ids,
        "pres_by_prod": pres_by_prod,
        "costo_by_prod": costo_by_prod,
        "pct_by_prod":  pct_by_prod,
    }


# ---------------------------------------------------------------------------
# 4. Terceros (clientes y proveedores)
# ---------------------------------------------------------------------------
def seed_terceros(cur):
    n_cli  = SCALE
    n_prov = max(10, SCALE // 5)
    ter_rows  = []
    tipo_rows = []
    tid = 1

    # Clientes (persona natural con cédula)
    for _ in range(n_cli):
        nm = fake.company() if random.random() < 0.3 else f"{fake.last_name()} {fake.last_name()}"
        ter_rows.append((tid, 1, next_ced(), nm, 1))
        tipo_rows.append((tid, tid, "cliente"))
        tid += 1

    # Proveedores (empresas con RUC)
    for _ in range(n_prov):
        sufijos = ["S.A.","Cía. Ltda.","Corp.","Group","S.A.S."]
        nm = f"{fake.last_name()} & {fake.last_name()} {random.choice(sufijos)}"
        ter_rows.append((tid, 2, next_ruc(), nm, 1))
        tipo_rows.append((tid, tid, "proveedor"))
        tid += 1

    bulk(cur, """INSERT INTO terceros
        (id,id_tipo_identificacion,numero_identificacion,razon_social,estado)
        VALUES (%s,%s,%s,%s,%s)""", ter_rows)
    bulk(cur, "INSERT INTO terceros_tipos (id,id_tercero,tipo) VALUES (%s,%s,%s)", tipo_rows)

    cli_ids  = list(range(1, n_cli + 1))
    prov_ids = list(range(n_cli + 1, n_cli + n_prov + 1))

    print(f"  [OK] terceros ({n_cli} clientes, {n_prov} proveedores)")
    return {"cli_ids": cli_ids, "prov_ids": prov_ids}


# ---------------------------------------------------------------------------
# 5. Inventario inicial
# ---------------------------------------------------------------------------
def seed_inventario(cur, pd, org):
    inv_rows  = []
    mov_rows  = []
    iid = 1
    mid = 1
    bod_ids = org["bod_ids"]

    for prod_id, pres_list in pd["pres_by_prod"].items():
        # Solo asignar stock a la primera bodega de cada sucursal (bodegas principales)
        for bod_id in [org["suc_bods"][s][0] for s in org["suc_bods"]]:
            qty  = r2(random.uniform(10.0, 500.0))
            qmin = r2(random.uniform(5.0, 50.0))
            qmax = r2(qmin * random.uniform(5.0, 20.0))
            pres_id = pres_list[0][0]
            inv_rows.append((iid, prod_id, pres_id, bod_id, qty, qmin, qmax))

            # Movimiento de entrada inicial
            costo = pd["costo_by_prod"][prod_id]
            mov_rows.append((mid, prod_id, pres_id, bod_id,
                             "entrada", qty, 0.0, qty, costo, None, "ajuste", "Inventario inicial"))
            iid += 1
            mid += 1

    bulk(cur, """INSERT INTO inventario
        (id,id_producto,id_presentacion,id_bodega,cantidad,cantidad_minima,cantidad_maxima)
        VALUES (%s,%s,%s,%s,%s,%s,%s)""", inv_rows)
    bulk(cur, """INSERT INTO movimientos_inventario
        (id,id_producto,id_presentacion,id_bodega,tipo_movimiento,cantidad,
         cantidad_anterior,cantidad_posterior,costo_unitario,id_referencia,tipo_referencia,observacion)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", mov_rows)

    # índice: (prod_id, pres_id, bod_id) -> iid
    inv_index = {(r[1],r[2],r[3]): r[0] for r in inv_rows}
    print(f"  [OK] inventario ({len(inv_rows)} registros, {len(mov_rows)} movimientos iniciales)")
    return {"inv_rows": inv_rows, "inv_index": inv_index, "next_mov_id": mid}


# ---------------------------------------------------------------------------
# 6. Compras
# ---------------------------------------------------------------------------
def seed_compras(cur, pd, ter, org, next_mov_id):
    n_oc     = SCALE * 2
    prov_ids = ter["prov_ids"]
    suc_ids  = org["suc_ids"]
    suc_bods = org["suc_bods"]
    prod_ids = pd["prod_ids"]
    pres_by  = pd["pres_by_prod"]
    costo_by = pd["costo_by_prod"]
    pct_by   = pd["pct_by_prod"]

    oc_rows   = []
    ocd_rows  = []
    rec_rows  = []
    recd_rows = []
    pago_prov = []
    mov_rows  = []

    ocd_id = 1
    rec_id = 1
    recd_id = 1
    pago_p_id = 1
    mid = next_mov_id

    for i in range(n_oc):
        oc_id  = i + 1
        suc_id = random.choice(suc_ids)
        bod_id = suc_bods[suc_id][0]
        prov   = random.choice(prov_ids)
        fecha  = gen_fecha(D_INI, D_FIN)
        estado = random.choices(
            ["aprobada","completa","cancelada","borrador"],
            weights=[40, 35, 15, 10]
        )[0]

        # 2-4 líneas por OC
        n_lin = random.randint(2, 4)
        lineas_oc = []
        for _ in range(n_lin):
            pid   = random.choice(prod_ids)
            pres  = pres_by[pid][0]
            pres_id = pres[0]
            qty   = r2(random.uniform(5.0, 100.0))
            pu    = r2(costo_by[pid] * random.uniform(0.9, 1.1))
            sub   = r2(qty * pu)
            pct   = pct_by[pid]
            lineas_oc.append((ocd_id, oc_id, pid, pres_id, qty, 0.0, pu, 0.0, sub, pct))
            ocd_rows.append((ocd_id, oc_id, pid, pres_id, qty, 0.0, pu, 0.0, sub))
            ocd_id += 1

        sub_total = r2(sum(l[8] for l in lineas_oc))
        imp_total = r2(sum(l[8] * l[9] / 100 for l in lineas_oc))
        tot_total = r2(sub_total + imp_total)

        oc_rows.append((oc_id, suc_id, prov, bod_id,
                        gen_num_doc("OC", oc_id), str(fecha), estado,
                        sub_total, 0.0, imp_total, tot_total))

        # Recepciones para OC aprobadas/completas
        if estado in ("aprobada", "completa"):
            parcial = estado == "aprobada" and random.random() < 0.15  # ESC-08 parcial
            fecha_rec = fecha + timedelta(days=random.randint(3, 15))
            if fecha_rec > D_FIN:
                fecha_rec = D_FIN
            est_rec = "parcial" if parcial else "completa"
            cur_rec_id = rec_id
            rec_rows.append((cur_rec_id, oc_id, bod_id,
                             gen_num_doc("REC", cur_rec_id), str(fecha_rec), est_rec))
            rec_id += 1

            for lin in lineas_oc:
                ocd_lid, _, pid, pres_id, qty_esp, _, _, _, _, _ = lin
                qty_rec = r2(qty_esp * random.uniform(0.5, 0.9)) if parcial else qty_esp
                costo   = costo_by[pid]
                recd_rows.append((recd_id, cur_rec_id, ocd_lid, pid, pres_id, qty_esp, qty_rec, costo))
                recd_id += 1

                # Movimiento inventario entrada por recepción
                mov_rows.append((mid, pid, pres_id, bod_id,
                                 "entrada", qty_rec, 0.0, qty_rec, costo,
                                 cur_rec_id, "recepcion", None))
                mid += 1

            # Pago proveedor (70% de las OC recibidas)
            if random.random() < 0.70:
                fp = random.choice([1, 4, 5])
                fecha_pago = fecha_rec + timedelta(days=random.randint(1, 30))
                if fecha_pago > D_FIN:
                    fecha_pago = D_FIN
                pago_prov.append((pago_p_id, oc_id, prov, fp, None, None,
                                  str(fecha_pago), tot_total))
                pago_p_id += 1

    bulk(cur, """INSERT INTO ordenes_compra
        (id,id_sucursal,id_proveedor,id_bodega_destino,numero,fecha_emision,
         estado,subtotal,descuento,impuesto,total)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", oc_rows)

    bulk(cur, """INSERT INTO ordenes_compra_detalle
        (id,id_orden_compra,id_producto,id_presentacion,cantidad,
         cantidad_recibida,precio_unitario,descuento,subtotal)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", ocd_rows)

    bulk(cur, """INSERT INTO recepciones
        (id,id_orden_compra,id_bodega,numero,fecha_recepcion,estado)
        VALUES (%s,%s,%s,%s,%s,%s)""", rec_rows)

    bulk(cur, """INSERT INTO recepciones_detalle
        (id,id_recepcion,id_orden_compra_detalle,id_producto,id_presentacion,
         cantidad_esperada,cantidad_recibida,costo_unitario)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", recd_rows)

    bulk(cur, """INSERT INTO pagos_proveedores
        (id,id_orden_compra,id_proveedor,id_forma_pago,id_cuenta_bancaria,
         numero_referencia,fecha_pago,monto)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", pago_prov)

    bulk(cur, """INSERT INTO movimientos_inventario
        (id,id_producto,id_presentacion,id_bodega,tipo_movimiento,cantidad,
         cantidad_anterior,cantidad_posterior,costo_unitario,id_referencia,tipo_referencia,observacion)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", mov_rows)

    print(f"  [OK] compras ({n_oc} OC, {len(rec_rows)} recepciones, {len(pago_prov)} pagos proveedor)")
    return {
        "oc_ids": [r[0] for r in oc_rows],
        "next_mov_id": mid,
    }


# ---------------------------------------------------------------------------
# 7. Ventas (facturas con distribución estacional)
# ---------------------------------------------------------------------------
def seed_ventas(cur, pd, ter, org, next_mov_id):
    n_fac    = SCALE * 5
    cli_ids  = ter["cli_ids"]
    suc_ids  = org["suc_ids"]
    suc_bods = org["suc_bods"]
    prod_ids = pd["prod_ids"]
    pres_by  = pd["pres_by_prod"]
    costo_by = pd["costo_by_prod"]
    pct_by   = pd["pct_by_prod"]

    # ESC-04: diciembre concentra 20% de las facturas (pico estacional)
    n_dic = n_fac // 5
    n_resto = n_fac - n_dic

    fac_rows  = []
    facd_rows = []
    mov_rows  = []
    fac_id_counter = 0
    facd_id   = 1
    mid       = next_mov_id

    # ESC-05: Sucursal Cuenca (id=3) solo recibe 5% de facturas
    suc_weights = [47, 48, 5]

    def _gen_fac_rows(count, fecha_gen_fn, suc_wts=None):
        nonlocal facd_id, mid, fac_id_counter
        rows = []
        d_rows = []
        m_rows = []
        for i in range(count):
            fac_id_counter += 1
            fac_id  = fac_id_counter
            suc_id  = random.choices(suc_ids, weights=suc_wts or [1]*len(suc_ids))[0]
            bod_id  = suc_bods[suc_id][0]
            cli_id  = random.choice(cli_ids)
            fecha   = fecha_gen_fn()
            venc    = fecha + timedelta(days=random.choice([30, 60, 90]))
            estado  = random.choices(
                ["activa","pagada","anulada","vencida"],
                weights=[50, 30, 5, 15]
            )[0]

            n_lin = random.randint(1, 4)
            lineas = []
            for _ in range(n_lin):
                pid    = random.choice(prod_ids)
                pres_id = pres_by[pid][0][0]
                qty    = r2(random.uniform(1.0, 20.0))
                costo  = costo_by[pid]
                pu     = r2(costo * random.uniform(1.20, 1.60))
                pct    = pct_by[pid]
                desc   = 0.0
                sub_l  = r2(qty * pu)
                lineas.append((facd_id, fac_id, pid, pres_id, bod_id,
                               qty, pu, desc, sub_l, costo, pct))
                facd_id += 1

            sub, desc, imp, tot = calc_totales(
                [(l[5], l[6], l[7], l[10]) for l in lineas]
            )
            saldo = 0.0 if estado == "pagada" else tot

            rows.append((fac_id, suc_id, cli_id,
                         gen_num_doc("FAC", fac_id), str(fecha), str(venc),
                         estado, sub, desc, imp, tot, saldo))

            for lin in lineas:
                d_rows.append(lin[:10])  # sin pct

            # Movimientos de salida solo para facturas activas/pagadas
            if estado in ("activa", "pagada"):
                for lin in lineas:
                    _, _, pid, pres_id, bod_id_l, qty, _, _, _, costo, _ = lin
                    m_rows.append((mid, pid, pres_id, bod_id_l,
                                   "salida", qty, qty, 0.0, costo,
                                   fac_id, "factura", None))
                    mid += 1

        return rows, d_rows, m_rows

    rows1, d1, m1 = _gen_fac_rows(n_resto, lambda: gen_fecha(D_INI, date(2025,11,30)), suc_weights)
    rows2, d2, m2 = _gen_fac_rows(n_dic,   lambda: gen_fecha(date(2025,12,1), D_FIN),  suc_weights)
    fac_rows  = rows1 + rows2
    facd_rows = d1   + d2
    mov_rows  = m1   + m2

    bulk(cur, """INSERT INTO facturas
        (id,id_sucursal,id_cliente,numero,fecha_emision,fecha_vencimiento,
         estado,subtotal,descuento,impuesto,total,saldo)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", fac_rows)

    bulk(cur, """INSERT INTO facturas_detalle
        (id,id_factura,id_producto,id_presentacion,id_bodega,
         cantidad,precio_unitario,descuento,subtotal,costo_unitario)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", facd_rows)

    bulk(cur, """INSERT INTO movimientos_inventario
        (id,id_producto,id_presentacion,id_bodega,tipo_movimiento,cantidad,
         cantidad_anterior,cantidad_posterior,costo_unitario,id_referencia,tipo_referencia,observacion)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", mov_rows)

    print(f"  [OK] ventas ({len(fac_rows)} facturas, {len(facd_rows)} líneas, {len(mov_rows)} movimientos)")
    return {
        "fac_rows": fac_rows,
        "next_mov_id": mid,
    }


# ---------------------------------------------------------------------------
# 8. Pagos a clientes (cobros)
# ---------------------------------------------------------------------------
def seed_pagos_clientes(cur, fac_rows):
    pago_rows = []
    caja_rows = []
    pid  = 1
    cid  = 1

    for fac in fac_rows:
        fac_id, suc_id, cli_id = fac[0], fac[1], fac[2]
        estado, tot, saldo     = fac[6], fac[10], fac[11]

        if estado == "pagada":
            # Pago total
            fecha_pago = date.fromisoformat(fac[4]) + timedelta(days=random.randint(1, 20))
            if fecha_pago > D_FIN:
                fecha_pago = D_FIN
            fp = random.choice([1, 2, 3, 4])
            pago_rows.append((pid, fac_id, cli_id, fp, None, None, str(fecha_pago), tot))

            caja_rows.append((cid, suc_id, 1, "ingreso", tot, 0.0, tot,
                              f"Cobro factura {fac[3]}", fac_id, "pago_cliente",
                              str(fecha_pago)))
            pid += 1; cid += 1

        elif estado == "activa" and random.random() < 0.30:
            # Pago parcial (ESC-09)
            pago_parcial = r2(tot * random.uniform(0.20, 0.80))
            fecha_pago = date.fromisoformat(fac[4]) + timedelta(days=random.randint(1, 30))
            if fecha_pago > D_FIN:
                fecha_pago = D_FIN
            fp = random.choice([1, 2, 3, 4])
            pago_rows.append((pid, fac_id, cli_id, fp, None, None, str(fecha_pago), pago_parcial))
            caja_rows.append((cid, suc_id, 1, "ingreso", pago_parcial, 0.0, pago_parcial,
                              f"Cobro parcial {fac[3]}", fac_id, "pago_cliente",
                              str(fecha_pago)))
            pid += 1; cid += 1

    bulk(cur, """INSERT INTO pagos_clientes
        (id,id_factura,id_cliente,id_forma_pago,id_cuenta_bancaria,
         numero_referencia,fecha_pago,monto)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", pago_rows)

    bulk(cur, """INSERT INTO caja
        (id,id_sucursal,id_usuario,tipo_movimiento,monto,saldo_anterior,saldo_posterior,
         concepto,id_referencia,tipo_referencia,fecha_movimiento)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", caja_rows)

    print(f"  [OK] cobros ({len(pago_rows)} pagos, {len(caja_rows)} movimientos de caja)")
    return {"pago_cli_ids": [r[0] for r in pago_rows]}


# ---------------------------------------------------------------------------
# 9. Inyección de escenarios
# ---------------------------------------------------------------------------
def inject_scenarios(cur, pd, ter, org, fac_rows):
    print("  Inyectando escenarios...")
    cli_ids  = ter["cli_ids"]
    prov_ids = ter["prov_ids"]
    prod_ids = pd["prod_ids"]
    suc_ids  = org["suc_ids"]
    suc_bods = org["suc_bods"]
    pres_by  = pd["pres_by_prod"]
    inv_by   = {(r[1],r[2],r[3]): r[0] for r in org.get("inv_rows",[])}

    # --- ESC-01: Cliente moroso (facturas vencidas +90 días sin cobrar) ---
    cliente_moroso_id = cli_ids[-1]
    base_id = 90001
    corte_venc = TODAY - timedelta(days=95)
    morosas = []
    for k in range(15):
        fid  = base_id + k
        fec  = corte_venc - timedelta(days=random.randint(0, 60))
        venc = fec + timedelta(days=30)
        tot  = r2(random.uniform(500, 3000))
        morosas.append((fid, suc_ids[0], cliente_moroso_id,
                        gen_num_doc("FAC-MOR", k+1), str(fec), str(venc),
                        "vencida", tot, 0.0, r2(tot*0.12), r2(tot*1.12), r2(tot*1.12)))
    bulk(cur, """INSERT INTO facturas
        (id,id_sucursal,id_cliente,numero,fecha_emision,fecha_vencimiento,
         estado,subtotal,descuento,impuesto,total,saldo)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", morosas)
    print(f"    [ESC-01] cliente moroso id={cliente_moroso_id}: 15 facturas vencidas insertadas")

    # --- ESC-02: Stock bajo mínimo (5 productos) ---
    prods_bajos = random.sample(prod_ids, 5)
    for pid in prods_bajos:
        cur.execute("""UPDATE inventario SET cantidad = cantidad_minima * 0.2
                       WHERE id_producto=%s LIMIT 1""", (pid,))
    print(f"    [ESC-02] stock bajo mínimo: {prods_bajos}")

    # --- ESC-03: Proveedor inactivo (sin OC en 180 días) ---
    proveedor_inactivo_id = prov_ids[-2]
    cur.execute("""UPDATE ordenes_compra SET fecha_emision = %s
                   WHERE id_proveedor=%s""",
                (str(TODAY - timedelta(days=200)), proveedor_inactivo_id))
    print(f"    [ESC-03] proveedor inactivo id={proveedor_inactivo_id}: OC movidas al pasado")

    # --- ESC-06: Stock en cero (3 productos) ---
    prods_cero = random.sample([p for p in prod_ids if p not in prods_bajos], 3)
    for pid in prods_cero:
        cur.execute("UPDATE inventario SET cantidad=0 WHERE id_producto=%s LIMIT 1", (pid,))
    print(f"    [ESC-06] stock en cero: {prods_cero}")

    # --- ESC-07: Notas de crédito pendientes (8 notas) ---
    facs_activas = [f for f in fac_rows if f[6] == "activa"]
    facs_nc = random.sample(facs_activas, min(8, len(facs_activas)))
    nc_rows = []
    ncd_rows = []
    nc_id = 1
    ncd_id = 1
    for f in facs_nc:
        motivos = ["Devolución de mercadería","Error en precio","Descuento acordado","Producto defectuoso"]
        tot_nc  = r2(float(f[10]) * random.uniform(0.10, 0.40))
        imp_nc  = r2(tot_nc * 0.12)
        sub_nc  = r2(tot_nc - imp_nc)
        nc_rows.append((nc_id, f[0], f[2],
                        gen_num_doc("NC", nc_id), str(gen_fecha(D_INI, D_FIN)),
                        random.choice(motivos), "activa", sub_nc, imp_nc, tot_nc))
        ncd_rows.append((ncd_id, nc_id,
                         random.choice(pd["prod_ids"]),
                         pres_by[random.choice(pd["prod_ids"])][0][0],
                         r2(random.uniform(1,5)), r2(tot_nc/5), sub_nc))
        nc_id += 1; ncd_id += 1
    bulk(cur, """INSERT INTO notas_credito
        (id,id_factura,id_cliente,numero,fecha_emision,motivo,estado,subtotal,impuesto,total)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", nc_rows)
    bulk(cur, """INSERT INTO notas_credito_detalle
        (id,id_nota_credito,id_producto,id_presentacion,cantidad,precio_unitario,subtotal)
        VALUES (%s,%s,%s,%s,%s,%s,%s)""", ncd_rows)
    print(f"    [ESC-07] {len(nc_rows)} notas de crédito activas insertadas")

    # --- ESC-10: Producto top-seller (inserta líneas extra en facturas existentes) ---
    top_prod_id  = prod_ids[0]
    top_pres_id  = pres_by[top_prod_id][0][0]
    top_bod_id   = suc_bods[suc_ids[0]][0]
    top_costo    = pd["costo_by_prod"][top_prod_id]
    top_facs     = random.sample(facs_activas, min(SCALE//2, len(facs_activas)))
    extra_det    = []
    facd_base    = 80001
    for k, f in enumerate(top_facs):
        qty  = r2(random.uniform(5.0, 50.0))
        pu   = r2(top_costo * 1.40)
        sub  = r2(qty * pu)
        extra_det.append((facd_base+k, f[0], top_prod_id, top_pres_id, top_bod_id,
                          qty, pu, 0.0, sub, top_costo))
    bulk(cur, """INSERT INTO facturas_detalle
        (id,id_factura,id_producto,id_presentacion,id_bodega,
         cantidad,precio_unitario,descuento,subtotal,costo_unitario)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", extra_det)
    print(f"    [ESC-10] producto top-seller id={top_prod_id}: {len(extra_det)} líneas extra")

    print("  [OK] escenarios inyectados")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    db = DB_CONFIG["database"]
    print(f"=== seed_massive.py | DB={db} | SCALE={SCALE} ===\n")
    conn = mysql.connector.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    # Verificar que la DB esté vacía; si no, abortar con mensaje claro
    cur.execute("SELECT COUNT(*) FROM tipos_identificacion")
    (n,) = cur.fetchone()
    if n > 0:
        cur.close()
        conn.close()
        print(
            f"Error: '{db}' no está vacía ({n} fila(s) en tipos_identificacion).\n"
            "Ejecuta primero:  py scripts/clear_db.py --yes",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        cat = seed_catalogos(cur)
        org = seed_organizacion(cur)
        pd  = seed_productos(cur, cat)
        ter = seed_terceros(cur)
        inv = seed_inventario(cur, pd, org)
        org["inv_rows"] = inv["inv_rows"]

        comp = seed_compras(cur, pd, ter, org, inv["next_mov_id"])
        vta  = seed_ventas(cur, pd, ter, org, comp["next_mov_id"])
        seed_pagos_clientes(cur, vta["fac_rows"])
        inject_scenarios(cur, pd, ter, org, vta["fac_rows"])

        conn.commit()
        print(f"\n=== Seed completado exitosamente ===")
    except Exception as exc:
        conn.rollback()
        print(f"\nError: {exc}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
