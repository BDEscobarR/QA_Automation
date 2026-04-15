"""
Simple flow: enter client 100723, then enter articles one by one.
Always use the last available empty Artículo row.
"""
import json, time, subprocess
from urllib.request import Request, urlopen

REMOTE_URL = "http://127.0.0.1:4723"
APP = r"C:\Users\BrayanEscobar\AppData\Local\BnetEmpresarial\current\ERP.Empresarial.exe"

def api(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body else None
    h = {"Content-Type": "application/json"} if data else {}
    req = Request(f"{REMOTE_URL}{path}", data=data, headers=h, method=method)
    try:
        return json.loads(urlopen(req, timeout=60).read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def fe(sid, s, v):
    r = api("POST", f"/session/{sid}/element", {"using": s, "value": v})
    val = r.get("value", {})
    if isinstance(val, dict):
        if "error" in val: return None
        return val.get("ELEMENT") or (list(val.values())[0] if val else None)
    return val

def fes(sid, s, v):
    r = api("POST", f"/session/{sid}/elements", {"using": s, "value": v})
    val = r.get("value", [])
    return [e.get("ELEMENT") or list(e.values())[0] for e in val if isinstance(e, dict)]

def at(sid, eid, n):
    return api("GET", f"/session/{sid}/element/{eid}/attribute/{n}").get("value", "")

def clk(sid, eid): api("POST", f"/session/{sid}/element/{eid}/click", {})
def ky(sid, eid, t): api("POST", f"/session/{sid}/element/{eid}/value", {"value": list(t)})
def cl(sid, eid): api("POST", f"/session/{sid}/element/{eid}/clear", {})
def ds(sid):
    try: api("DELETE", f"/session/{sid}")
    except: pass

def wait_find(sid, s, v, t=30):
    for _ in range(t):
        e = fe(sid, s, v)
        if e: return e
        time.sleep(1)
    return None

def find_last_art_fila(sid):
    """Find the highest numbered empty Artículo Fila cell."""
    last = None
    last_i = -1
    for i in range(20):
        a = fe(sid, "name", f"Artículo Fila {i}")
        if a:
            last = a
            last_i = i
        else:
            break
    return last, last_i

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)

    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]
    scoped_sid = None

    try:
        # LOGIN + NAVIGATE
        wait_find(sid, "accessibility id", "txtUser")
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, "brayan")
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, "cafe123.")
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        frm = wait_find(sid, "accessibility id", "frmInicioComercial", 30)
        print("Login OK"); time.sleep(5)
        nwh = int(at(sid, frm, "NativeWindowHandle"))
        scoped_sid = api("POST", "/session", {
            "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": hex(nwh)}
        }).get("sessionId")
        mov = fe(sid, "name", "Movimientos"); clk(sid, mov); time.sleep(4)
        pe = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']"); clk(scoped_sid, pe); time.sleep(3)
        pe02 = fe(scoped_sid, "name", "PE02 - PEDIDO"); clk(scoped_sid, pe02); time.sleep(8)
        print("Formulario PE02 abierto")

        # === ENTER CLIENT ===
        txt_cl = fe(sid, "accessibility id", "txtCliente")
        cl(sid, txt_cl)
        ky(sid, txt_cl, "100723")
        ky(sid, txt_cl, ["\ue004"])  # Tab
        time.sleep(5)
        print(f"Vendedor: '{at(sid, fe(sid, 'accessibility id', 'cboVendedor'), 'Name')}'")

        # Check initial state
        last, last_i = find_last_art_fila(sid)
        print(f"Initial last row: Fila {last_i}")

        # === ENTER 5 ARTICLES ===
        articles = ["000001", "000002", "000003", "000004", "000005"]
        
        for idx, code in enumerate(articles):
            print(f"\n--- Article {idx+1}: {code} ---")
            
            # Find the last available empty row
            art_cell, fila = find_last_art_fila(sid)
            if not art_cell:
                print(f"  No Artículo cell found! Trying to wait...")
                time.sleep(3)
                art_cell, fila = find_last_art_fila(sid)
            
            if not art_cell:
                print(f"  Still no cell. Aborting.")
                break
            
            print(f"  Using Artículo Fila {fila}")
            clk(sid, art_cell)
            time.sleep(1)
            
            # Type the full article code
            ky(sid, art_cell, code)
            time.sleep(2)
            
            # Tab to confirm
            ky(sid, art_cell, ["\ue004"])
            time.sleep(4)
            
            # Enter quantity
            cant_cell = fe(sid, "name", f"Cant. Fila {fila}, Sin orden.")
            if cant_cell:
                clk(sid, cant_cell)
                time.sleep(1)
                ky(sid, cant_cell, "1")
                ky(sid, cant_cell, ["\ue004"])
                time.sleep(3)
                print(f"  Quantity entered")
            else:
                print(f"  Cant. cell not found for Fila {fila}")
            
            # Check state
            _, new_last = find_last_art_fila(sid)
            print(f"  After: last row is Fila {new_last}")
            
            # Check totals
            filas_f = fe(sid, "accessibility id", "txtFilas")
            total_f = fe(sid, "accessibility id", "txtVrTotal")
            if filas_f: print(f"  Filas: '{at(sid, filas_f, 'Name')}'")
            if total_f: print(f"  Total: '{at(sid, total_f, 'Name')}'")

        # === FINAL STATE ===
        print(f"\n{'='*50}")
        print("FINAL STATE")
        print(f"{'='*50}")
        _, last_f = find_last_art_fila(sid)
        print(f"Last Artículo Fila: {last_f}")
        
        for aid in ["txtFilas", "txtVrSubtotal", "txtVrTotal"]:
            e = fe(sid, "accessibility id", aid)
            if e:
                print(f"  {aid}: '{at(sid, e, 'Name')}'")
        
        # Check row values
        for i in range(last_f + 1):
            art = fe(sid, "name", f"Artículo Fila {i}")
            cant = fe(sid, "name", f"Cant. Fila {i}, Sin orden.")
            total = fe(sid, "name", f"Total Fila {i}, Sin orden.")
            if art:
                a_name = at(sid, art, "Name")
                c_name = at(sid, cant, "Name") if cant else "N/A"
                t_name = at(sid, total, "Name") if total else "N/A"
                print(f"  Row {i}: art='{a_name}' cant='{c_name}' total='{t_name}'")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        ds(sid)
        if scoped_sid: ds(scoped_sid)
        subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
        print("\nDone.")

if __name__ == "__main__":
    main()
