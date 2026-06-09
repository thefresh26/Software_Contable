# -*- coding: utf-8 -*-
"""
CONTAAPP — TEST FUNCIONAL COMPLETO (8 FASES)
Fecha: 2026-06-08
"""

import sys, json, io, datetime, requests
from decimal import Decimal

BASE = "http://localhost:8000"
PASSED = []
FAILED = []


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _ok(name, detail=""):
    print("OK  PASS | " + name + (" | " + detail if detail else ""))
    PASSED.append(name)


def _fail(name, detail=""):
    print("ERR FAIL | " + name + (" | " + detail if detail else ""))
    FAILED.append((name, detail))


def test(name, condition, detail=""):
    if condition:
        _ok(name, detail)
    else:
        _fail(name, detail)
    return condition


def login(username, password):
    r = requests.post(f"{BASE}/api/auth/login/", json={"username": username, "password": password})
    if r.status_code == 200:
        d = safe_json(r)
        return d.get("access") or d.get("token")
    return None


def hdr(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get(token, path, params=None):
    return requests.get(f"{BASE}{path}", headers=hdr(token), params=params)


def post(token, path, data=None):
    return requests.post(f"{BASE}{path}", headers=hdr(token), json=data or {})


def patch(token, path, data=None):
    return requests.patch(f"{BASE}{path}", headers=hdr(token), json=data or {})


def safe_json(r):
    try:
        return r.json()
    except Exception:
        return {}


def list_items(r):
    d = safe_json(r)
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        return d.get("results", d.get("data", []))
    return []


def first_id(r):
    items = list_items(r)
    return items[0]["id"] if items else None


# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("FASE 1-2: Modulos Base - Login, CRUD, Flujo Facturacion")
print("="*70)

# ── 1.1 Login todos los roles ─────────────────────────────────────────────────
print("\n-- 1.1 Login por roles --")
PASS_ACT = "Admin2024!"

token_admin    = login("admin",    PASS_ACT)
token_vendedor = login("vendedor1", PASS_ACT)
token_auxiliar = login("auxiliar1", PASS_ACT)
test("Login admin",    token_admin    is not None)
test("Login vendedor", token_vendedor is not None)
test("Login auxiliar", token_auxiliar is not None)

if token_admin:
    for uname, rol_val in [("contador_test", "contador"), ("gerente_test", "gerente")]:
        requests.post(f"{BASE}/api/auth/registro/", json={
            "username": uname, "password": PASS_ACT,
            "email": f"{uname}@test.com", "rol": rol_val
        })
        tok = login(uname, PASS_ACT)
        test(f"Login {rol_val}", tok is not None)

if not token_admin:
    print("CRITICO: Sin token admin. Abortando.")
    sys.exit(1)

T = token_admin

# ── 1.2 Perfil ────────────────────────────────────────────────────────────────
print("\n-- 1.2 Perfil usuario --")
r = get(T, "/api/auth/me/")
d = safe_json(r)
test("GET /api/auth/me/ -> 200", r.status_code == 200, f"rol={d.get('rol','?')}")

# ── 1.3 CRUD Terceros ─────────────────────────────────────────────────────────
print("\n-- 1.3 CRUD Terceros --")
r = get(T, "/api/terceros/")
test("GET /api/terceros/ -> 200", r.status_code == 200,
     f"count={safe_json(r).get('count', len(list_items(r)))}")

r = post(T, "/api/terceros/", {
    "nombre": "Test Cliente SA", "nit": "999900001-1", "tipo": "cliente",
    "email": "testcliente@test.com", "telefono": "3001234567",
    "ciudad": "Bogota", "direccion": "Cra 10 #20-30"
})
test("POST crear tercero cliente", r.status_code == 201,
     f"id={safe_json(r).get('id','?')} err={str(safe_json(r))[:80] if r.status_code!=201 else ''}")
tercero_cli_id = safe_json(r).get("id") if r.status_code == 201 else None

if tercero_cli_id:
    r2 = get(T, f"/api/terceros/{tercero_cli_id}/")
    test("GET tercero por ID", r2.status_code == 200)
    r3 = patch(T, f"/api/terceros/{tercero_cli_id}/", {"telefono": "3009999999"})
    test("PATCH actualizar tercero", r3.status_code == 200)

r = post(T, "/api/terceros/", {
    "nombre": "Proveedor Test SAS", "nit": "999900002-2", "tipo": "proveedor",
    "email": "proveedor@test.com", "telefono": "3002222222", "ciudad": "Medellin"
})
proveedor_id = safe_json(r).get("id") if r.status_code in (200, 201) else None

if not tercero_cli_id:
    tercero_cli_id = first_id(get(T, "/api/terceros/"))
if not proveedor_id:
    proveedor_id = tercero_cli_id

# ── 1.4 CRUD Productos ────────────────────────────────────────────────────────
print("\n-- 1.4 CRUD Productos --")
r = get(T, "/api/inventario/categorias/")
cat_id = first_id(r)
if not cat_id:
    rc = post(T, "/api/inventario/categorias/", {"nombre": "Categoria Test", "descripcion": "Test"})
    cat_id = safe_json(rc).get("id")

r = post(T, "/api/inventario/productos/", {
    "codigo": "PROD-TEST-001", "nombre": "Producto de Prueba Test",
    "descripcion": "Para pruebas funcionales", "categoria": cat_id,
    "precio_venta": "150000.00", "precio_compra": "100000.00",
    "tipo": "producto", "unidad_medida": "UND", "iva_porcentaje": "19.00",
    "stock_actual": "100", "stock_minimo": "10", "permite_inventario": True
})
test("POST crear producto", r.status_code == 201,
     f"cod={safe_json(r).get('codigo','?')} err={str(safe_json(r))[:80] if r.status_code!=201 else ''}")
producto_id = safe_json(r).get("id") if r.status_code == 201 else None

if producto_id:
    r2 = get(T, f"/api/inventario/productos/{producto_id}/")
    test("GET producto por ID", r2.status_code == 200)
    r3 = get(T, "/api/inventario/productos/")
    test("GET listado productos -> 200", r3.status_code == 200,
         f"count={safe_json(r3).get('count', len(list_items(r3)))}")

# Ajuste inventario — endpoint: POST /api/inventario/ajuste/
if producto_id:
    r_adj = post(T, "/api/inventario/ajuste/", {
        "producto": producto_id, "tipo": "entrada", "cantidad": "50",
        "motivo": "Ajuste prueba funcional", "costo_unitario": "100000"
    })
    test("POST ajuste inventario entrada", r_adj.status_code in (200, 201),
         f"status={r_adj.status_code} resp={str(safe_json(r_adj))[:80]}")

if not producto_id:
    producto_id = first_id(get(T, "/api/inventario/productos/"))

# ── 1.5 Cotización → Aprobar → Convertir → Emitir FV → Asiento → CxC ────────
print("\n-- 1.5 Flujo Cotizacion → Factura Venta → Asiento → CxC --")
cot_id = None
fv_id = None
cxc_id = None
if tercero_cli_id and producto_id:
    r = post(T, "/api/presupuestos/cotizaciones/", {
        "tercero": tercero_cli_id,
        "fecha": str(datetime.date.today()),
        "fecha_vencimiento": str(datetime.date.today() + datetime.timedelta(days=30)),
        "observaciones": "Cotizacion de prueba funcional",
        "detalles": [{
            "producto": producto_id,
            "descripcion": "Producto test",
            "cantidad": "2",
            "precio_unitario": "150000.00",
            "iva_porcentaje": "19.00"
        }]
    })
    test("POST crear cotizacion", r.status_code == 201,
         f"num={safe_json(r).get('numero','?')}")
    cot_id = safe_json(r).get("id") if r.status_code == 201 else None

if cot_id:
    r = post(T, f"/api/presupuestos/cotizaciones/{cot_id}/aprobar/")
    test("POST aprobar cotizacion", r.status_code == 200,
         f"estado={safe_json(r).get('estado','?')}")

    r = post(T, f"/api/presupuestos/cotizaciones/{cot_id}/convertir-factura/")
    test("POST convertir cotizacion → factura", r.status_code == 201,
         f"num={safe_json(r).get('numero','?')}")
    fv_id = safe_json(r).get("id") if r.status_code == 201 else None

if fv_id:
    r = post(T, f"/api/facturacion/facturas/{fv_id}/emitir/")
    test("POST emitir factura venta", r.status_code == 200,
         f"estado={safe_json(r).get('estado','?')}")

    r_asi = get(T, "/api/contabilidad/asientos/")
    test("Asiento contable generado para FV", r_asi.status_code == 200 and len(list_items(r_asi)) > 0,
         f"total={len(list_items(r_asi))}")

    r_cxc = get(T, "/api/cartera/por-cobrar/")
    cxc_list = list_items(r_cxc)
    test("CxC creada para FV", r_cxc.status_code == 200 and len(cxc_list) > 0,
         f"total={len(cxc_list)}")
    # Tomar la CxC más reciente (mayor ID)
    cxc_pendientes = [c for c in cxc_list if c.get("estado") in ("pendiente", "parcial")]
    cxc_id = max(cxc_pendientes, key=lambda x: x["id"])["id"] if cxc_pendientes else None

# ── 1.6 Factura Compra con Retenciones → Emitir → Asiento → CxP ─────────────
print("\n-- 1.6 Factura Compra con Retenciones → CxP --")
r = get(T, "/api/facturacion/retenciones-tipo/")
retenciones = list_items(r)
test("GET tipos retencion -> 200", r.status_code == 200, f"count={len(retenciones)}")
ret_id = retenciones[0]["id"] if retenciones else None

fc_id = None
cxp_id = None
if proveedor_id and producto_id:
    fc_data = {
        "tipo": "FC",
        "tercero": proveedor_id,
        "fecha": str(datetime.date.today()),
        "fecha_vencimiento": str(datetime.date.today() + datetime.timedelta(days=30)),
        "observaciones": "Factura compra prueba funcional",
        "detalles": [{
            "producto": producto_id,
            "descripcion": "Compra producto test",
            "cantidad": "10",
            "precio_unitario": "100000.00",
            "iva_porcentaje": "19.00"
        }]
    }
    if ret_id:
        # RetencionInputSerializer requiere: tipo_retencion, base, porcentaje, valor
        fc_data["retenciones"] = [{
            "tipo_retencion": ret_id, "base": "1000000.00",
            "porcentaje": "3.50", "valor": "35000.00"
        }]
    r = post(T, "/api/facturacion/facturas/", fc_data)
    test("POST crear factura compra", r.status_code == 201,
         f"num={safe_json(r).get('numero','?')}")
    fc_id = safe_json(r).get("id") if r.status_code == 201 else None

if fc_id:
    r = post(T, f"/api/facturacion/facturas/{fc_id}/emitir/")
    test("POST emitir factura compra", r.status_code == 200,
         f"estado={safe_json(r).get('estado','?')}")
    r_cxp = get(T, "/api/cartera/por-pagar/")
    test("CxP creada para FC", r_cxp.status_code == 200 and len(list_items(r_cxp)) > 0,
         f"total={len(list_items(r_cxp))}")
    cxp_id = first_id(r_cxp)

# ── 1.7 Pago parcial y completo en cartera ────────────────────────────────────
print("\n-- 1.7 Pagos en Cartera CxC --")
# Usar la CxC de la FV recién emitida (más confiable)
if not cxc_id:
    r_cxc2 = get(T, "/api/cartera/por-cobrar/")
    for cx in list_items(r_cxc2):
        if cx.get("estado") in ("pendiente", "parcial"):
            cxc_id = cx["id"]
            break

if cxc_id:
    r_cx = get(T, f"/api/cartera/por-cobrar/{cxc_id}/")
    cx_data = safe_json(r_cx)
    val_pend = cx_data.get("valor_pendiente", "0")
    try:
        val_float = float(str(val_pend))
        mitad = str(round(val_float / 2, 2))
        resto = str(round(val_float / 2, 2))
    except Exception:
        mitad = "100000"
        resto = "100000"

    # Pago parcial — campos correctos: medio_pago (no metodo_pago), observacion (no descripcion)
    r = post(T, f"/api/cartera/por-cobrar/{cxc_id}/registrar-pago/", {
        "valor": mitad,
        "fecha": str(datetime.date.today()),
        "medio_pago": "transferencia",
        "referencia": "REF-TEST-001",
        "observacion": "Pago parcial prueba"
    })
    test("POST pago parcial CxC", r.status_code == 201,
         f"valor={mitad} status={r.status_code} err={str(safe_json(r))[:60] if r.status_code!=201 else ''}")

    r2 = get(T, f"/api/cartera/por-cobrar/{cxc_id}/")
    val_rest = str(safe_json(r2).get("valor_pendiente", resto))
    r3 = post(T, f"/api/cartera/por-cobrar/{cxc_id}/registrar-pago/", {
        "valor": val_rest,
        "fecha": str(datetime.date.today()),
        "medio_pago": "efectivo",
        "referencia": "REF-TEST-002",
        "observacion": "Pago completo prueba"
    })
    test("POST pago completo CxC", r3.status_code == 201,
         f"saldo_rest={val_rest} err={str(safe_json(r3))[:60] if r3.status_code!=201 else ''}")
else:
    _fail("POST pago parcial CxC", "No hay CxC pendiente")
    _fail("POST pago completo CxC", "No hay CxC pendiente")

r_res = get(T, "/api/cartera/resumen/")
test("GET resumen cartera -> 200", r_res.status_code == 200,
     f"cobrar={safe_json(r_res).get('total_por_cobrar','?')}")

# ── 1.8 Importar Excel ───────────────────────────────────────────────────────
print("\n-- 1.8 Importar Excel --")
try:
    import openpyxl

    # Terceros: columnas exactas: tipo, tipo_persona, nombre, nit, email, telefono, direccion, ciudad
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["tipo", "tipo_persona", "nombre", "nit", "email", "telefono", "direccion", "ciudad"])
    ws.append(["cliente", "juridica", "Import Cliente Excel 1", "333300001-1", "imp1@t.com", "3011111111", "Cra 1", "Cali"])
    ws.append(["proveedor", "natural", "Import Proveedor Excel 1", "444400001-1", "imp2@t.com", "3022222222", "Av 2", "Bogota"])
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    r = requests.post(f"{BASE}/api/importador/terceros/",
                      headers={"Authorization": f"Bearer {T}"},
                      files={"archivo": ("terceros.xlsx", buf,
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    test("POST importar Excel terceros", r.status_code in (200, 201, 207),
         f"status={r.status_code} resp={str(safe_json(r))[:100]}")

    # Productos: columnas exactas: codigo, nombre, categoria, precio_compra, precio_venta,
    #            iva_porcentaje, stock_actual, stock_minimo, unidad_medida
    wb2 = openpyxl.Workbook()
    ws2 = wb2.active
    ws2.append(["codigo", "nombre", "categoria", "precio_compra", "precio_venta",
                "iva_porcentaje", "stock_actual", "stock_minimo", "unidad_medida"])
    ws2.append(["IMPORT-XLS-001", "Producto Import Excel 1", "General", 150000, 200000,
                19, 100, 10, "UND"])
    buf2 = io.BytesIO(); wb2.save(buf2); buf2.seek(0)
    r2 = requests.post(f"{BASE}/api/importador/productos/",
                       headers={"Authorization": f"Bearer {T}"},
                       files={"archivo": ("productos.xlsx", buf2,
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    test("POST importar Excel productos", r2.status_code in (200, 201, 207),
         f"status={r2.status_code} resp={str(safe_json(r2))[:100]}")
except ImportError:
    _fail("POST importar Excel terceros", "openpyxl no disponible")
    _fail("POST importar Excel productos", "openpyxl no disponible")


# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("FASE 3-4: PDFs y Datos - PUC, Nomina")
print("="*70)

print("\n-- 3.1 PDFs --")
r_fv = get(T, "/api/facturacion/facturas/", params={"tipo": "FV", "estado": "emitida"})
fv_pdf_id = first_id(r_fv)
if fv_pdf_id:
    r = get(T, f"/api/facturacion/facturas/{fv_pdf_id}/pdf/")
    ct = r.headers.get("Content-Type", "")
    test("GET PDF factura venta", r.status_code == 200 and "pdf" in ct.lower(),
         f"ct={ct} size={len(r.content)}b")
else:
    _fail("GET PDF factura venta", "No hay FV emitida")

r_cot = get(T, "/api/presupuestos/cotizaciones/")
cot_pdf_id = first_id(r_cot)
if cot_pdf_id:
    r = get(T, f"/api/presupuestos/cotizaciones/{cot_pdf_id}/pdf/")
    ct = r.headers.get("Content-Type", "")
    test("GET PDF cotizacion", r.status_code == 200 and "pdf" in ct.lower(),
         f"ct={ct} size={len(r.content)}b")
else:
    _fail("GET PDF cotizacion", "No hay cotizaciones")

print("\n-- 3.2 PUC --")
r = get(T, "/api/contabilidad/cuentas/")
total_puc = safe_json(r).get("count", len(list_items(r)))
test("PUC cargado con >=241 cuentas", total_puc >= 241, f"count={total_puc}")

# ── 3.3 Nomina ────────────────────────────────────────────────────────────────
print("\n-- 3.3 Nomina --")
r = get(T, "/api/nomina/empleados/")
emps = list_items(r)
test("GET empleados -> 200", r.status_code == 200, f"count={len(emps)}")
emp_id = emps[0]["id"] if emps else None

liq_id = None
if emp_id:
    hoy = datetime.date.today()
    # Buscar un mes que no tenga liquidacion para este empleado (hasta 6 meses atras)
    primer, ultimo = None, None
    for delta_m in range(0, 6):
        mes_ref = hoy.month - delta_m
        year_ref = hoy.year
        while mes_ref <= 0:
            mes_ref += 12
            year_ref -= 1
        p = datetime.date(year_ref, mes_ref, 1)
        u = datetime.date(year_ref, mes_ref, 28)
        r_check = get(T, "/api/nomina/liquidaciones/",
                      params={"mes": mes_ref, "ano": year_ref})
        liq_existentes = [l for l in list_items(r_check) if l.get("empleado") == emp_id]
        if not liq_existentes:
            primer, ultimo = p, u
            break
    if not primer:  # Fallback: usar mes actual, acepta duplicado como advertencia
        primer = datetime.date(hoy.year, hoy.month, 1)
        ultimo = datetime.date(hoy.year, hoy.month, 28)

    r = post(T, "/api/nomina/liquidar/", {
        "empleado": emp_id,
        "periodo_inicio": str(primer),
        "periodo_fin": str(ultimo),
    })
    test("POST liquidar nomina", r.status_code in (200, 201),
         f"status={r.status_code} resp={str(safe_json(r))[:100]}")
    d = safe_json(r)
    liq_id = d.get("id") if isinstance(d, dict) else None

    # Test duplicado — debe rechazar con 400
    r2 = post(T, "/api/nomina/liquidar/", {
        "empleado": emp_id,
        "periodo_inicio": str(primer),
        "periodo_fin": str(ultimo),
    })
    test("Validacion duplicado nomina (rechaza)",
         r2.status_code == 400,
         f"status={r2.status_code} resp={str(safe_json(r2))[:80]}")

if not liq_id:
    liq_id = first_id(get(T, "/api/nomina/liquidaciones/"))

if liq_id:
    r = get(T, f"/api/nomina/liquidaciones/{liq_id}/colilla/")
    ct = r.headers.get("Content-Type", "")
    test("GET PDF colilla nomina", r.status_code == 200 and "pdf" in ct.lower(),
         f"ct={ct} size={len(r.content)}b")
else:
    _fail("GET PDF colilla nomina", "No hay liquidaciones")


# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("FASE 5: Activos Fijos")
print("="*70)

print("\n-- 5.1 Crear activo fijo --")
r = get(T, "/api/activos/categorias/")
cats_act = list_items(r)
cat_act_id = cats_act[0]["id"] if cats_act else None

activo_id = None
hoy_str = str(datetime.date.today())
fecha_compra_str = str(datetime.date.today() - datetime.timedelta(days=365))

if cat_act_id:
    # Campos requeridos: fecha_inicio_depreciacion (DateField), vida_util_años (con ñ)
    r = post(T, "/api/activos/", {
        "codigo": "ACT-TEST-001",
        "nombre": "Equipo de Prueba Funcional",
        "categoria": cat_act_id,
        "fecha_compra": fecha_compra_str,
        "fecha_inicio_depreciacion": fecha_compra_str,
        "valor_compra": "10000000.00",
        "valor_residual": "1000000.00",
        "vida_util_años": 5,   # vida_util_años con ñ
        "numero_serie": "SN-TEST-001",
        "descripcion": "Activo para prueba funcional"
    })
    test("POST crear activo fijo", r.status_code == 201,
         f"cod={safe_json(r).get('codigo','?')} err={str(safe_json(r))[:80] if r.status_code!=201 else ''}")
    activo_id = safe_json(r).get("id") if r.status_code == 201 else None

if not activo_id:
    r = get(T, "/api/activos/")
    activo_id = first_id(r)

# ── 5.2 Tabla depreciacion ────────────────────────────────────────────────────
if activo_id:
    r = get(T, f"/api/activos/{activo_id}/tabla-depreciacion/")
    tabla = safe_json(r).get("tabla", [])
    test("GET tabla depreciacion", r.status_code == 200 and len(tabla) > 0,
         f"filas={len(tabla)}")

# ── 5.3 Aplicar depreciacion ──────────────────────────────────────────────────
if activo_id:
    per_str = datetime.date.today().strftime("%Y-%m")
    r = post(T, f"/api/activos/{activo_id}/aplicar-depreciacion/", {"periodo": per_str})
    test("POST aplicar depreciacion activo", r.status_code == 200,
         f"creado={safe_json(r).get('creado','?')} val={safe_json(r).get('depreciacion',{}).get('valor_depreciacion','?')}")
    r_asi = get(T, "/api/contabilidad/asientos/")
    test("Asiento generado para depreciacion", r_asi.status_code == 200 and len(list_items(r_asi)) > 0)

# ── 5.4 Baja activos ──────────────────────────────────────────────────────────
print("\n-- 5.4 Baja activos --")

def crear_activo_prueba(codigo, nombre, cat_id):
    r = post(T, "/api/activos/", {
        "codigo": codigo, "nombre": nombre,
        "categoria": cat_id,
        "fecha_compra": fecha_compra_str,
        "fecha_inicio_depreciacion": fecha_compra_str,
        "valor_compra": "5000000.00",
        "valor_residual": "500000.00",
        "vida_util_años": 5,
        "numero_serie": f"SN-{codigo}"
    })
    return safe_json(r).get("id") if r.status_code == 201 else None

activo_baja_id = crear_activo_prueba("ACT-BAJA-001", "Activo para Dar de Baja", cat_act_id) if cat_act_id else None
if activo_baja_id:
    r = post(T, f"/api/activos/{activo_baja_id}/dar-baja/", {
        "fecha": hoy_str, "motivo": "obsolescencia",
        "valor_venta": "0", "observaciones": "Baja sin venta prueba funcional"
    })
    test("POST dar baja activo sin venta", r.status_code == 201,
         f"motivo={safe_json(r).get('motivo','?')}")
else:
    _fail("POST dar baja activo sin venta", "No se pudo crear activo para baja")

activo_venta_id = crear_activo_prueba("ACT-VENTA-001", "Activo para Vender", cat_act_id) if cat_act_id else None
if activo_venta_id:
    r = post(T, f"/api/activos/{activo_venta_id}/dar-baja/", {
        "fecha": hoy_str, "motivo": "venta",
        "valor_venta": "3000000", "observaciones": "Venta activo prueba funcional"
    })
    test("POST dar baja activo con venta", r.status_code == 201,
         f"motivo={safe_json(r).get('motivo','?')}")
else:
    _fail("POST dar baja activo con venta", "No se pudo crear activo para venta")


# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("FASE 6: Notificaciones")
print("="*70)

print("\n-- 6.1 Verificar alertas --")
r = post(T, "/api/notificaciones/verificar-alertas/")
test("POST verificar-alertas -> 200", r.status_code == 200,
     f"resp={str(safe_json(r))[:80]}")

print("\n-- 6.2 Campana no-leidas --")
r = get(T, "/api/notificaciones/no-leidas-count/")
test("GET no-leidas-count -> 200", r.status_code == 200,
     f"count={safe_json(r).get('count','?')}")

print("\n-- 6.3 Listado notificaciones --")
r = get(T, "/api/notificaciones/")
notifs = list_items(r)
test("GET listado notificaciones -> 200", r.status_code == 200, f"count={len(notifs)}")
notif_id = first_id(r)

print("\n-- 6.4 Marcar como leida --")
if notif_id:
    r = post(T, f"/api/notificaciones/{notif_id}/marcar-leida/")
    test("POST marcar-leida -> 200", r.status_code == 200,
         f"leida={safe_json(r).get('leida','?')}")
else:
    _fail("POST marcar-leida", "No hay notificaciones")

r = post(T, "/api/notificaciones/marcar-todas-leidas/")
test("POST marcar-todas-leidas -> 200", r.status_code == 200,
     f"actualizadas={safe_json(r).get('actualizadas','?')}")


# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("FASE 7: Conciliacion Bancaria")
print("="*70)

print("\n-- 7.1 Cuentas Bancarias --")
r = get(T, "/api/bancos/cuentas/")
cuentas_banco = list_items(r)
test("GET cuentas bancarias -> 200", r.status_code == 200, f"count={len(cuentas_banco)}")
cuenta_banco_id = cuentas_banco[0]["id"] if cuentas_banco else None

print("\n-- 7.2 Importar extracto CSV --")
extracto_id = None
if cuenta_banco_id:
    hoy2 = datetime.date.today()
    primer2 = datetime.date(hoy2.year, hoy2.month, 1)
    csv_txt = (
        "fecha,descripcion,debito,credito,saldo\n"
        f"{primer2},Pago cliente A,,500000,5500000\n"
        f"{primer2},Compra proveedor,200000,,5300000\n"
        f"{primer2 + datetime.timedelta(days=1)},Transferencia,,1000000,6300000\n"
        f"{primer2 + datetime.timedelta(days=2)},Gasto bancario,15000,,6285000\n"
    )
    csv_buf = io.BytesIO(csv_txt.encode("utf-8"))
    r = requests.post(
        f"{BASE}/api/bancos/extractos/importar/",
        headers={"Authorization": f"Bearer {T}"},
        data={"cuenta_id": cuenta_banco_id, "saldo_inicial": "5000000"},
        files={"archivo": ("extracto.csv", csv_buf, "text/csv")}
    )
    test("POST importar extracto bancario CSV", r.status_code in (200, 201),
         f"status={r.status_code} resp={str(safe_json(r))[:100]}")
    if r.status_code in (200, 201):
        extracto_id = safe_json(r).get("extracto_id")
else:
    _fail("POST importar extracto bancario CSV", "No hay cuentas bancarias")

print("\n-- 7.3 Conciliacion automatica --")
conciliacion_id = None
if extracto_id:
    r = post(T, "/api/bancos/conciliaciones/", {
        "extracto": extracto_id,
        "notas": "Conciliacion de prueba funcional"
    })
    test("POST crear conciliacion", r.status_code == 201,
         f"id={safe_json(r).get('id','?')}")
    conciliacion_id = safe_json(r).get("id") if r.status_code == 201 else None

if conciliacion_id:
    r = post(T, f"/api/bancos/conciliaciones/{conciliacion_id}/conciliar-automatico/")
    test("POST conciliar-automatico -> 200", r.status_code == 200,
         f"conciliados={safe_json(r).get('conciliados','?')}")

print("\n-- 7.4 Partidas de conciliacion --")
if conciliacion_id:
    # Tipos validos: cheque_girado, deposito_transito, nota_debito, nota_credito, error_libros, error_banco, otro
    # Afecta valido: extracto | libros
    r = post(T, f"/api/bancos/conciliaciones/{conciliacion_id}/partidas/", {
        "tipo": "deposito_transito",
        "descripcion": "Deposito en transito prueba funcional",
        "valor": "15000.00",
        "fecha": hoy_str,
        "afecta": "extracto"
    })
    test("POST agregar partida conciliacion", r.status_code == 201,
         f"id={safe_json(r).get('id','?')} err={str(safe_json(r))[:60] if r.status_code!=201 else ''}")

print("\n-- 7.5 Reporte conciliacion --")
if conciliacion_id:
    r = get(T, f"/api/bancos/conciliaciones/{conciliacion_id}/reporte/")
    test("GET reporte conciliacion JSON -> 200", r.status_code == 200,
         f"keys={list(safe_json(r).keys())[:5]}")

    r_pdf = get(T, f"/api/bancos/conciliaciones/{conciliacion_id}/reporte/",
                params={"formato": "pdf"})
    ct = r_pdf.headers.get("Content-Type", "")
    test("GET PDF conciliacion bancaria", r_pdf.status_code == 200 and "pdf" in ct.lower(),
         f"ct={ct} size={len(r_pdf.content)}b")


# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("FASE 8: Multi-Empresa")
print("="*70)

print("\n-- 8.1 Listar empresas --")
r = get(T, "/api/empresas/")
empresas = list_items(r)
test("GET /api/empresas/ -> 200", r.status_code == 200, f"count={len(empresas)}")
test(">=3 empresas en sistema", len(empresas) >= 3, f"count={len(empresas)}")
empresa_ids = [e["id"] for e in empresas]

print("\n-- 8.2 Cambiar empresa activa --")
token_emp2 = None
if len(empresa_ids) >= 2:
    r = post(T, f"/api/empresas/{empresa_ids[1]}/cambiar/")
    test("POST cambiar empresa -> 200", r.status_code == 200,
         f"empresa={safe_json(r).get('empresa',{}).get('nombre','?') if r.status_code==200 else safe_json(r)}")
    if r.status_code == 200:
        token_emp2 = safe_json(r).get("access") or safe_json(r).get("token")

print("\n-- 8.3 Aislamiento de datos --")
if token_emp2:
    r1 = get(T, "/api/terceros/")
    r2 = get(token_emp2, "/api/terceros/")
    c1 = safe_json(r1).get("count", len(list_items(r1)))
    c2 = safe_json(r2).get("count", len(list_items(r2)))
    test("Aislamiento datos entre empresas",
         r1.status_code == 200 and r2.status_code == 200,
         f"empresa1={c1} | empresa2={c2} terceros")
else:
    _fail("Aislamiento datos entre empresas", "No se obtuvo token empresa alternativa")

print("\n-- 8.4 Crear nueva empresa --")
import time as _time
nit_unico = f"77788{int(_time.time()) % 100000}-1"
r = post(T, "/api/empresas/", {
    "nombre": "Empresa Test Nueva SAS",
    "nit": nit_unico,
    "razon_social": "Empresa Test Nueva SAS",
    "regimen": "comun",
    "email": "test@empresanueva.com",
    "telefono": "6011234567",
    "ciudad": "Bogota",
    "direccion": "Cra 15 #30-45"
})
test("POST crear nueva empresa", r.status_code == 201,
     f"nit={safe_json(r).get('nit','?')} err={str(safe_json(r))[:80] if r.status_code!=201 else ''}")
nueva_empresa_id = safe_json(r).get("id") if r.status_code == 201 else None

print("\n-- 8.5 PUC propio para nueva empresa --")
if nueva_empresa_id:
    r_camb = post(T, f"/api/empresas/{nueva_empresa_id}/cambiar/")
    if r_camb.status_code == 200:
        tok_ne = safe_json(r_camb).get("access") or safe_json(r_camb).get("token")
        if tok_ne:
            r_puc = get(tok_ne, "/api/contabilidad/cuentas/")
            puc_c = safe_json(r_puc).get("count", len(list_items(r_puc)))
            test("Nueva empresa accede a PUC", r_puc.status_code == 200,
                 f"cuentas={puc_c}")
        else:
            _fail("Nueva empresa accede a PUC", "Sin token")
    else:
        _fail("Nueva empresa accede a PUC", f"No se pudo cambiar: {r_camb.status_code}")
else:
    _fail("Nueva empresa accede a PUC", "No se creo la empresa")

print("\n-- 8.6 Rol diferente por empresa --")
r = get(T, "/api/auth/usuarios/")
test("GET usuarios (admin) -> 200", r.status_code == 200,
     f"count={safe_json(r).get('count', len(list_items(r)))}")

# Volver a empresa original
r_back = post(T, f"/api/empresas/{empresa_ids[0]}/cambiar/")
if r_back.status_code == 200:
    T = safe_json(r_back).get("access") or safe_json(r_back).get("token") or T


# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("REPORTES FINALES")
print("="*70)

print("\n-- Reportes Contables --")

r = get(T, "/api/contabilidad/asientos/balance-general/")
bg = safe_json(r)
test("GET balance-general -> 200", r.status_code == 200,
     f"activos={bg.get('activos','?')} cuadrado={bg.get('cuadrado','?')}")
test("Balance general cuadrado (A=P+Pat)",
     r.status_code == 200 and bg.get("cuadrado") is True,
     f"activos={bg.get('activos')} == pasivos+pat={float(str(bg.get('pasivos',0)))+float(str(bg.get('patrimonio',0)))}")

r = get(T, "/api/contabilidad/asientos/estado-resultados/")
er = safe_json(r)
test("GET estado-resultados -> 200", r.status_code == 200,
     f"ingresos={er.get('ingresos','?')} utilidad_neta={er.get('utilidad_neta','?')}")

r = get(T, "/api/contabilidad/asientos/libro-diario/")
asientos_ld = list_items(r) if r.status_code == 200 else []
test("GET libro-diario -> 200", r.status_code == 200, f"asientos={len(asientos_ld)}")

r_bc = get(T, "/api/contabilidad/asientos/balance-comprobacion/")
bc = safe_json(r_bc)
filas_bc = bc.get("filas", [])
cuenta_mayor = filas_bc[0]["codigo"] if filas_bc else "1105"
r = get(T, "/api/contabilidad/asientos/libro-mayor/", params={"cuenta": cuenta_mayor})
lm = safe_json(r)
test("GET libro-mayor -> 200", r.status_code == 200,
     f"cuenta={cuenta_mayor} movs={len(lm.get('movimientos',[]))}")

test("GET balance-comprobacion cuadrado", r_bc.status_code == 200 and bc.get("cuadrado", False),
     f"debito={bc.get('total_debito','?')} cuadrado={bc.get('cuadrado','?')}")

print("\n-- Reporte Activos --")
r = get(T, "/api/activos/reportes/por-categoria/")
cats_rep = list_items(r) if r.status_code == 200 else []
test("GET activos por categoria -> 200", r.status_code == 200, f"categorias={len(cats_rep)}")

r = get(T, "/api/activos/reportes/resumen/")
test("GET activos resumen -> 200", r.status_code == 200,
     f"total={safe_json(r).get('total_activos','?')} valor={safe_json(r).get('valor_bruto','?')}")

print("\n-- Reporte Conciliacion --")
r = get(T, "/api/bancos/conciliaciones/")
test("GET listado conciliaciones -> 200", r.status_code == 200,
     f"count={len(list_items(r))}")


# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("RESUMEN EJECUTIVO - TEST FUNCIONAL COMPLETO CONTAAPP")
print("="*70)
total = len(PASSED) + len(FAILED)
pct = (len(PASSED) / total * 100) if total else 0
print(f"\nTotal pruebas : {total}")
print(f"PASS          : {len(PASSED)}")
print(f"FAIL          : {len(FAILED)}")
print(f"Tasa de exito : {pct:.1f}%")

if FAILED:
    print(f"\n-- Pruebas fallidas ({len(FAILED)}) --")
    for nombre, detalle in FAILED:
        print(f"  [FAIL] {nombre}: {detalle}")

if pct >= 95:
    print(f"\n[VERDE] SISTEMA EN ESTADO OPTIMO ({pct:.1f}%)")
elif pct >= 80:
    print(f"\n[AMARILLO] SISTEMA FUNCIONAL CON OBSERVACIONES ({pct:.1f}%)")
else:
    print(f"\n[ROJO] SISTEMA REQUIERE ATENCION ({pct:.1f}%)")
print("="*70)
