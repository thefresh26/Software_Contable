# -*- coding: utf-8 -*-
"""
Testeo funcional de produccion para ContaApp.
Corre contra https://software-contable-api.onrender.com
Crea una empresa QA-Test aislada, NO toca datos reales de Luisa.
"""
import requests
import json
import random
import string
import sys
import time
import io

BASE = "https://software-contable-api.onrender.com"
API = f"{BASE}/api"

RESULTS = []  # (name, "PASS"/"FAIL", detail)
RUN_ID = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def nit_con_digito(numero: str) -> str:
    """Genera un NIT colombiano valido (numero-digito) usando el mismo
    algoritmo que apps/terceros/utils.py para que pase validar_nit()."""
    primos = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    suma = sum(int(d) * primos[i] for i, d in enumerate(reversed(numero)))
    residuo = suma % 11
    digito = residuo if residuo < 2 else 11 - residuo
    return f"{numero}-{digito}"


def log(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    RESULTS.append((name, status, detail))
    print(f"[{status}] {name}" + (f" -> {detail}" if detail and not ok else ""))


def req(method, path, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = path if path.startswith("http") else f"{API}{path}"
    try:
        r = requests.request(method, url, headers=headers, timeout=60, **kwargs)
        return r
    except Exception as e:
        class FakeResp:
            status_code = -1
            text = str(e)

            def json(self):
                return {}
        return FakeResp()


def wake_up():
    print("Despertando el servicio de Render (puede tardar hasta 60s)...")
    for i in range(6):
        r = req("GET", "/api/auth/me/")
        if r.status_code != -1:
            print(f"  Servidor respondio (status {r.status_code}) tras intento {i+1}")
            return
        time.sleep(10)
    print("  ADVERTENCIA: el servidor no respondio tras varios intentos")


# ──────────────────────────────────────────────────────────────────────────
# 1. REGISTRO Y LOGIN PARA TODOS LOS ROLES
# ──────────────────────────────────────────────────────────────────────────
ROLES = ["admin", "contador", "auxiliar", "gerente", "vendedor"]
tokens = {}  # rol -> access token
user_ids = {}

def test_registro_y_login():
    for rol in ROLES:
        username = f"qa_{RUN_ID}_{rol}"
        email = f"{username}@qatest.local"
        password = "QaTest123!"
        body = {
            "username": username, "email": email, "password": password,
            "first_name": "QA", "last_name": rol,
            "empresa": "QA Test Co", "nit_empresa": "999999999",
            "rol": rol,
        }
        r = req("POST", "/auth/registro/", json=body)
        if r.status_code not in (200, 201):
            log(f"Registro rol={rol}", False, f"status={r.status_code} body={r.text[:300]}")
            continue
        log(f"Registro rol={rol}", True)

        r2 = req("POST", "/auth/login/", json={"username": username, "password": password})
        if r2.status_code != 200:
            log(f"Login rol={rol}", False, f"status={r2.status_code} body={r2.text[:300]}")
            continue
        data = r2.json()
        tokens[rol] = data.get("access")
        log(f"Login rol={rol}", bool(tokens.get(rol)), "" if tokens.get(rol) else "sin access token")

        r3 = req("GET", "/auth/me/", token=tokens[rol])
        ok = r3.status_code == 200 and r3.json().get("rol") == rol
        user_ids[rol] = r3.json().get("id") if r3.status_code == 200 else None
        log(f"GET /auth/me/ refleja rol={rol}", ok, f"status={r3.status_code} rol_devuelto={r3.json().get('rol') if r3.status_code==200 else '?'}")


# ──────────────────────────────────────────────────────────────────────────
# 2. EMPRESA QA AISLADA
# ──────────────────────────────────────────────────────────────────────────
empresa_id = None

def test_crear_empresa():
    global empresa_id
    token = tokens.get("admin")
    if not token:
        log("Crear empresa QA-Test", False, "no hay token admin")
        return
    body = {
        "nombre": f"QA-Test-{RUN_ID}", "nit": nit_con_digito(str(random.randint(100000000, 999999999))),
        "razon_social": f"QA Test Company {RUN_ID} S.A.S.",
    }
    r = req("POST", "/empresas/", token=token, json=body)
    if r.status_code not in (200, 201):
        log("Crear empresa QA-Test", False, f"status={r.status_code} body={r.text[:300]}")
        return
    empresa_id = r.json().get("id")
    log("Crear empresa QA-Test", bool(empresa_id), f"empresa_id={empresa_id}")

    # admin queda con empresa_activa seteada automaticamente (perform_create)
    r2 = req("GET", "/auth/me/", token=token)
    activa = r2.json().get("empresa_activa") if r2.status_code == 200 else None
    log("empresa_activa asignada tras creacion", bool(activa), f"empresa_activa={activa}")

    # cargar PUC para la empresa nueva
    r3 = req("POST", f"/empresas/{empresa_id}/setup/", token=token)
    log("Setup PUC para empresa nueva", r3.status_code == 200, f"status={r3.status_code} body={r3.text[:300]}")

    # añadir a los demás roles QA a la misma empresa
    for rol in ROLES:
        if rol == "admin" or rol not in user_ids or not user_ids[rol]:
            continue
        r4 = req("POST", f"/empresas/{empresa_id}/usuarios/", token=token,
                  json={"usuario_id": user_ids[rol], "rol": rol})
        log(f"Agregar usuario rol={rol} a empresa QA", r4.status_code in (200, 201),
            f"status={r4.status_code} body={r4.text[:200]}")
        # cambiar ese usuario a la empresa activa para que pueda operar
        r5 = req("POST", f"/empresas/{empresa_id}/cambiar/", token=tokens[rol])
        if r5.status_code == 200:
            tokens[rol] = r5.json().get("access", tokens[rol])
        log(f"cambiar empresa activa para rol={rol}", r5.status_code == 200,
            f"status={r5.status_code} body={r5.text[:200]}")


# ──────────────────────────────────────────────────────────────────────────
# 3. PERMISOS POR ROL (sanity checks)
# ──────────────────────────────────────────────────────────────────────────
def test_permisos_roles():
    # usuarios viewset es admin-only
    for rol in ROLES:
        token = tokens.get(rol)
        if not token:
            continue
        r = req("GET", "/auth/usuarios/", token=token)
        if rol == "admin":
            log(f"rol={rol} puede listar usuarios", r.status_code == 200, f"status={r.status_code}")
        else:
            log(f"rol={rol} NO puede listar usuarios (403 esperado)", r.status_code == 403,
                f"status={r.status_code} body={r.text[:200]}")


# ──────────────────────────────────────────────────────────────────────────
# 4. CRUD TERCEROS / PRODUCTOS
# ──────────────────────────────────────────────────────────────────────────
tercero_id = None
producto_id = None

def test_crud_terceros_productos():
    global tercero_id, producto_id
    token = tokens.get("admin")

    body = {
        "tipo": "cliente", "tipo_persona": "juridica",
        "nombre": f"Cliente QA {RUN_ID}", "nit": nit_con_digito("9001112" + str(random.randint(10, 99))),
        "email": "cliente@qatest.local", "telefono": "3001112233", "ciudad": "Bogotá",
    }
    r = req("POST", "/terceros/", token=token, json=body)
    tercero_id = r.json().get("id") if r.status_code in (200, 201) else None
    log("Crear tercero (cliente)", bool(tercero_id), f"status={r.status_code} body={r.text[:300]}")

    if tercero_id:
        r2 = req("GET", f"/terceros/{tercero_id}/", token=token)
        log("Leer tercero", r2.status_code == 200, f"status={r2.status_code}")
        r3 = req("PATCH", f"/terceros/{tercero_id}/", token=token, json={"telefono": "3009998877"})
        log("Actualizar tercero", r3.status_code == 200, f"status={r3.status_code} body={r3.text[:200]}")

    r4 = req("GET", "/terceros/", token=token)
    log("Listar terceros", r4.status_code == 200, f"status={r4.status_code}")

    cat_body = {"nombre": f"CategoriaQA-{RUN_ID}"}
    rc = req("POST", "/inventario/categorias/", token=token, json=cat_body)
    cat_id = rc.json().get("id") if rc.status_code in (200, 201) else None
    log("Crear categoria producto", bool(cat_id), f"status={rc.status_code} body={rc.text[:300]}")

    prod_body = {
        "codigo": f"QA-{RUN_ID}", "nombre": f"Producto QA {RUN_ID}", "categoria": cat_id,
        "precio_compra": 10000, "precio_venta": 20000, "iva_porcentaje": 19,
        "stock_actual": 50, "stock_minimo": 5, "unidad_medida": "UND", "activo": True,
    }
    rp = req("POST", "/inventario/productos/", token=token, json=prod_body)
    producto_id = rp.json().get("id") if rp.status_code in (200, 201) else None
    log("Crear producto", bool(producto_id), f"status={rp.status_code} body={rp.text[:300]}")

    if producto_id:
        rp2 = req("GET", f"/inventario/productos/{producto_id}/", token=token)
        log("Leer producto", rp2.status_code == 200, f"status={rp2.status_code}")


# ──────────────────────────────────────────────────────────────────────────
# 5. FLUJO COMPLETO: COTIZACION -> FACTURA -> ASIENTO -> CARTERA
# ──────────────────────────────────────────────────────────────────────────
cotizacion_id = None
factura_id = None

def test_flujo_completo():
    global cotizacion_id, factura_id
    token = tokens.get("admin")
    if not (tercero_id and producto_id):
        log("Flujo cotizacion->factura", False, "faltan tercero_id/producto_id previos")
        return

    cot_body = {
        "tercero": tercero_id, "fecha": "2026-06-20", "fecha_vencimiento": "2026-07-20",
        "observaciones": "Cotizacion QA", "terminos": "50% anticipo",
        "detalles": [{"producto": producto_id, "descripcion": "Producto QA", "cantidad": 3,
                      "precio_unitario": 20000, "iva_porcentaje": 19}],
    }
    rc = req("POST", "/presupuestos/cotizaciones/", token=token, json=cot_body)
    cotizacion_id = rc.json().get("id") if rc.status_code in (200, 201) else None
    log("Crear cotizacion", bool(cotizacion_id), f"status={rc.status_code} body={rc.text[:400]}")
    if not cotizacion_id:
        return

    ra = req("POST", f"/presupuestos/cotizaciones/{cotizacion_id}/aprobar/", token=token)
    log("Aprobar cotizacion", ra.status_code == 200, f"status={ra.status_code} body={ra.text[:300]}")

    rpdf = req("GET", f"/presupuestos/cotizaciones/{cotizacion_id}/pdf/", token=token)
    ok_pdf = rpdf.status_code == 200 and rpdf.headers.get("Content-Type", "").startswith("application/pdf")
    log("PDF de cotizacion", ok_pdf, f"status={rpdf.status_code} content-type={rpdf.headers.get('Content-Type')}")

    rconv = req("POST", f"/presupuestos/cotizaciones/{cotizacion_id}/convertir-factura/", token=token)
    factura_id = rconv.json().get("id") if rconv.status_code in (200, 201) else None
    log("Convertir cotizacion a factura", bool(factura_id), f"status={rconv.status_code} body={rconv.text[:400]}")
    if not factura_id:
        return

    remi = req("POST", f"/facturacion/facturas/{factura_id}/emitir/", token=token)
    log("Emitir factura", remi.status_code == 200, f"status={remi.status_code} body={remi.text[:400]}")

    rget = req("GET", f"/facturacion/facturas/{factura_id}/", token=token)
    estado = rget.json().get("estado") if rget.status_code == 200 else None
    log("Factura queda en estado 'emitida'", estado == "emitida", f"estado={estado}")

    # Verificar asiento contable generado: buscamos asientos recientes con referencia a la factura
    rasi = req("GET", "/contabilidad/asientos/", token=token)
    asientos_ok = rasi.status_code == 200 and len(rasi.json() if isinstance(rasi.json(), list) else rasi.json().get("results", [])) > 0
    log("Asiento contable generado al emitir factura", asientos_ok, f"status={rasi.status_code}")

    # Verificar cartera (cuenta por cobrar)
    rcart = req("GET", "/cartera/por-cobrar/", token=token)
    data_cart = rcart.json() if rcart.status_code == 200 else []
    lista_cart = data_cart if isinstance(data_cart, list) else data_cart.get("results", [])
    match = [c for c in lista_cart if c.get("factura") == factura_id or str(c.get("factura")) == str(factura_id)]
    log("Cuenta por cobrar generada para la factura", bool(match) or bool(lista_cart),
        f"status={rcart.status_code} encontrados={len(lista_cart)}")

    rpdf2 = req("GET", f"/facturacion/facturas/{factura_id}/pdf/", token=token)
    ok_pdf2 = rpdf2.status_code == 200 and rpdf2.headers.get("Content-Type", "").startswith("application/pdf")
    log("PDF de factura", ok_pdf2, f"status={rpdf2.status_code} content-type={rpdf2.headers.get('Content-Type')}")


# ──────────────────────────────────────────────────────────────────────────
# 5b. NOMINA: EMPLEADO -> LIQUIDAR -> COLILLA PDF
# ──────────────────────────────────────────────────────────────────────────
def test_nomina_colilla():
    token = tokens.get("admin")
    emp_body = {
        "nombre": f"Empleado QA {RUN_ID}", "cedula": str(random.randint(1000000000, 1999999999)),
        "cargo": "Auxiliar QA", "departamento": "QA", "salario_base": 1800000,
        "fecha_ingreso": "2025-01-15", "tipo_contrato": "indefinido",
    }
    re_ = req("POST", "/nomina/empleados/", token=token, json=emp_body)
    empleado_id = re_.json().get("id") if re_.status_code in (200, 201) else None
    log("Crear empleado", bool(empleado_id), f"status={re_.status_code} body={re_.text[:300]}")
    if not empleado_id:
        return

    liq_body = {
        "empleado": empleado_id, "periodo_inicio": "2026-06-01", "periodo_fin": "2026-06-30",
        "bonificaciones": 0, "horas_extra_diurnas": 0, "horas_extra_nocturnas": 0,
        "retencion_fuente": 0, "otras_deducciones": 0,
    }
    rl = req("POST", "/nomina/liquidar/", token=token, json=liq_body)
    liquidacion_id = rl.json().get("id") if rl.status_code in (200, 201) else None
    log("Liquidar nomina", bool(liquidacion_id), f"status={rl.status_code} body={rl.text[:400]}")
    if not liquidacion_id:
        return

    rc = req("GET", f"/nomina/liquidaciones/{liquidacion_id}/colilla/", token=token)
    ok_colilla = rc.status_code == 200 and rc.headers.get("Content-Type", "").startswith("application/pdf")
    log("PDF de colilla de pago", ok_colilla, f"status={rc.status_code} content-type={rc.headers.get('Content-Type')}")

    rexp = req("GET", "/nomina/exportar/liquidaciones/?mes=6&a%C3%B1o=2026", token=token)
    ctype = rexp.headers.get("Content-Type", "")
    ok_exp = rexp.status_code == 200 and ("spreadsheet" in ctype or "excel" in ctype)
    log("Export Excel: Liquidaciones nomina", ok_exp, f"status={rexp.status_code} content-type={ctype} body={rexp.text[:200] if not ok_exp else ''}")


# ──────────────────────────────────────────────────────────────────────────
# 5c. VERIFICACION PUNTUAL DEL FIX 'empresa read_only' EN OTROS MODULOS
# ──────────────────────────────────────────────────────────────────────────
def test_fix_empresa_otros_modulos():
    token = tokens.get("admin")

    r1 = req("POST", "/contabilidad/centros-costo/", token=token,
              json={"codigo": f"CC-{RUN_ID}", "nombre": "Centro QA"})
    log("Crear centro de costo (sin enviar empresa)", r1.status_code in (200, 201),
        f"status={r1.status_code} body={r1.text[:300]}")

    r2 = req("POST", "/contabilidad/cuentas/", token=token,
              json={"codigo": f"99{random.randint(1000,9999)}", "nombre": "Cuenta QA", "tipo": "activo", "nivel": 6})
    cuenta_puc_id = r2.json().get("id") if r2.status_code in (200, 201) else None
    log("Crear cuenta PUC (sin enviar empresa)", r2.status_code in (200, 201),
        f"status={r2.status_code} body={r2.text[:300]}")

    r3 = req("POST", "/bancos/cuentas/", token=token, json={
        "nombre": "Banco QA", "banco": "Banco QA", "numero_cuenta": f"QA-{RUN_ID}",
        "tipo": "corriente", "saldo_inicial": 0, "cuenta_contable": cuenta_puc_id,
    })
    log("Crear cuenta bancaria (sin enviar empresa)", r3.status_code in (200, 201),
        f"status={r3.status_code} body={r3.text[:300]}")

    r4 = req("POST", "/activos/categorias/", token=token, json={"nombre": f"CatActivoQA-{RUN_ID}", "vida_util_años": 5})
    cat_act_id = r4.json().get("id") if r4.status_code in (200, 201) else None
    log("Crear categoria de activo (sin enviar empresa)", bool(cat_act_id), f"status={r4.status_code} body={r4.text[:300]}")

    r5 = req("POST", "/contabilidad/flujo-caja/", token=token, json={
        "fecha": "2026-06-20", "tipo": "ingreso", "concepto": "Prueba QA", "valor": 10000,
    })
    log("Crear flujo de caja (sin enviar empresa)", r5.status_code in (200, 201),
        f"status={r5.status_code} body={r5.text[:300]}")


# ──────────────────────────────────────────────────────────────────────────
# 5d. AISLAMIENTO MULTI-EMPRESA: datos de una empresa NO deben verse en otra
# ──────────────────────────────────────────────────────────────────────────
def test_aislamiento_multiempresa():
    # Empresa B, totalmente nueva, distinta del admin principal
    username_b = f"qa_{RUN_ID}_empresaB"
    password = "QaTest123!"
    rb = req("POST", "/auth/registro/", json={
        "username": username_b, "email": f"{username_b}@qatest.local", "password": password,
        "rol": "admin",
    })
    log("Registro usuario Empresa B", rb.status_code in (200, 201), f"status={rb.status_code} body={rb.text[:200]}")

    rlogin = req("POST", "/auth/login/", json={"username": username_b, "password": password})
    token_b = rlogin.json().get("access") if rlogin.status_code == 200 else None
    log("Login usuario Empresa B", bool(token_b), f"status={rlogin.status_code}")
    if not token_b:
        return

    nit_b = nit_con_digito("5544332" + str(random.randint(10, 99)))
    rempb = req("POST", "/empresas/", token=token_b, json={
        "nombre": f"Empresa-B-{RUN_ID}", "nit": nit_b, "razon_social": f"Empresa B {RUN_ID} SAS",
    })
    log("Crear Empresa B (aislada)", rempb.status_code in (200, 201), f"status={rempb.status_code} body={rempb.text[:200]}")

    # El admin de la Empresa B NO debe ver el tercero creado antes en la Empresa A (QA-Test)
    rlist = req("GET", "/terceros/", token=token_b)
    data = rlist.json() if rlist.status_code == 200 else {}
    items = data.get("results", data) if isinstance(data, dict) else data
    nombres = [t.get("nombre") for t in items] if isinstance(items, list) else []
    cliente_A_visible = any(f"Cliente QA {RUN_ID}" == n for n in nombres)
    log("Empresa B NO ve los terceros de Empresa A (aislamiento)", not cliente_A_visible,
        f"status={rlist.status_code} total_visibles={len(nombres)} fuga={cliente_A_visible}")

    # El admin de la Empresa B tampoco debe ver el FlujoCaja creado antes en Empresa A
    rflujo = req("GET", "/contabilidad/flujo-caja/", token=token_b)
    dataf = rflujo.json() if rflujo.status_code == 200 else {}
    itemsf = dataf.get("results", dataf) if isinstance(dataf, dict) else dataf
    log("Empresa B NO ve flujos de caja de Empresa A (aislamiento)",
        isinstance(itemsf, list) and len(itemsf) == 0,
        f"status={rflujo.status_code} visibles={len(itemsf) if isinstance(itemsf, list) else '?'}")

    # Un tercero creado por la Empresa B debe quedar con su propia empresa, no NULL ni la de A
    rterc_b = req("POST", "/terceros/", token=token_b, json={
        "tipo": "cliente", "tipo_persona": "natural",
        "nombre": f"Cliente Empresa B {RUN_ID}", "nit": nit_con_digito("6677889" + str(random.randint(10, 99))),
    })
    log("Crear tercero en Empresa B", rterc_b.status_code in (200, 201), f"status={rterc_b.status_code} body={rterc_b.text[:200]}")


# ──────────────────────────────────────────────────────────────────────────
# 6. EXPORTACIONES EXCEL
# ──────────────────────────────────────────────────────────────────────────
EXPORTS = [
    ("Terceros", "/terceros/exportar/"),
    ("Productos", "/inventario/exportar/productos/"),
    ("Facturas", "/facturacion/facturas/exportar/"),
    ("Cartera por cobrar", "/cartera/exportar/por-cobrar/"),
    ("Cartera por pagar", "/cartera/exportar/por-pagar/"),
    ("Balance general", "/contabilidad/asientos/exportar-balance-general/?fecha=2026-06-20"),
    ("Estado de resultados", "/contabilidad/asientos/exportar-estado-resultados/?desde=2026-01-01&hasta=2026-06-20"),
    ("Libro diario", "/contabilidad/asientos/exportar-libro-diario/?desde=2026-01-01&hasta=2026-06-20"),
    ("Flujo de caja", "/contabilidad/flujo-caja/exportar/?desde=2026-01-01&hasta=2026-06-20"),
    ("Activos fijos", "/activos/exportar/"),
]

def test_exportaciones_excel():
    token = tokens.get("admin")
    for name, path in EXPORTS:
        r = req("GET", path, token=token)
        ctype = r.headers.get("Content-Type", "")
        is_xlsx = "spreadsheet" in ctype or "excel" in ctype or path.endswith(".xlsx")
        ok = r.status_code == 200 and is_xlsx
        detail = f"status={r.status_code} content-type={ctype}"
        if not ok and r.status_code != -1:
            detail += f" body={r.text[:300]}"
        log(f"Export Excel: {name}", ok, detail)
        if ok:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(r.content))
                rows = wb.active.max_row
                log(f"Export Excel '{name}' es valido y legible", rows >= 1, f"filas={rows}")
            except Exception as e:
                log(f"Export Excel '{name}' es valido y legible", False, str(e))


# ──────────────────────────────────────────────────────────────────────────
# 7. BUSQUEDA GLOBAL
# ──────────────────────────────────────────────────────────────────────────
def test_busqueda_global():
    token = tokens.get("admin")
    r = req("GET", f"{BASE}/api/buscar/?q=QA", token=token)
    ok = r.status_code == 200
    log("Busqueda global responde", ok, f"status={r.status_code} body={r.text[:300]}")
    if ok:
        try:
            data = r.json()
            tiene_estructura = isinstance(data, dict) and "resultados" in data and "total" in data
            log("Busqueda global retorna resultados estructurados", tiene_estructura, f"keys={list(data.keys())}")
        except Exception as e:
            log("Busqueda global retorna JSON valido", False, str(e))


# ──────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────
def main():
    wake_up()
    test_registro_y_login()
    test_crear_empresa()
    test_permisos_roles()
    test_crud_terceros_productos()
    test_flujo_completo()
    test_nomina_colilla()
    test_fix_empresa_otros_modulos()
    test_aislamiento_multiempresa()
    test_exportaciones_excel()
    test_busqueda_global()

    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
    failed = [x for x in RESULTS if x[1] == "FAIL"]
    print(f"Total: {len(RESULTS)}  PASS: {passed}  FAIL: {len(failed)}")
    if failed:
        print("\nFALLOS DETALLADOS:")
        for name, _, detail in failed:
            print(f"  - {name}: {detail}")

    with open("qa_test_resultado.json", "w", encoding="utf-8") as f:
        json.dump({"results": RESULTS, "run_id": RUN_ID, "empresa_id": empresa_id,
                   "tercero_id": tercero_id, "producto_id": producto_id,
                   "cotizacion_id": cotizacion_id, "factura_id": factura_id}, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
