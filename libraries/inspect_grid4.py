"""
Enter 3 articles sequentially, debug row creation.
Check if we need to use "Agregar" button for new rows.
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

        # Enter client 100723
        txt_cl = fe(sid, "accessibility id", "txtCliente")
        cl(sid, txt_cl)
        ky(sid, txt_cl, "100723")
        ky(sid, txt_cl, ["\ue004"])  # Tab
        time.sleep(5)
        
        cbo_v = fe(sid, "accessibility id", "cboVendedor")
        vname = at(sid, cbo_v, "Name") if cbo_v else "N/A"
        print(f"Vendedor: '{vname}'")
        
        # Check how many rows exist initially
        art_cells = fes(sid, "xpath", "//DataItem[starts-with(@Name,'Artículo Fila')]")
        print(f"\nInitial Artículo cells: {len(art_cells)}")
        for a in art_cells:
            print(f"  '{at(sid, a, 'Name')}'")
        
        # Check "Agregar" button
        agregar = fe(sid, "name", "Agregar")
        if agregar:
            print(f"\nAgregar button: aid='{at(sid, agregar, 'AutomationId')}' enabled='{at(sid, agregar, 'IsEnabled')}'")
        
        # === ENTER 3 ARTICLES ===
        articles = ["000001", "000002", "000003"]
        
        for idx, code in enumerate(articles):
            fila = idx
            print(f"\n{'='*50}")
            print(f"ARTICLE {idx+1}: {code} -> Fila {fila}")
            print(f"{'='*50}")
            
            # Check if the row exists
            art_cell = fe(sid, "name", f"Artículo Fila {fila}")
            if not art_cell:
                print(f"  Artículo Fila {fila} NOT FOUND.")
                
                # List all existing Artículo cells
                existing = fes(sid, "xpath", "//DataItem[starts-with(@Name,'Artículo Fila')]")
                print(f"  Existing Artículo cells: {len(existing)}")
                for e in existing:
                    print(f"    '{at(sid, e, 'Name')}'")
                
                # Try clicking "Agregar" button to add a new row
                agregar = fe(sid, "name", "Agregar")
                if agregar:
                    print(f"  Clicking 'Agregar' button...")
                    clk(sid, agregar)
                    time.sleep(3)
                    
                    art_cell = fe(sid, "name", f"Artículo Fila {fila}")
                    if art_cell:
                        print(f"  Row created! Artículo Fila {fila} now exists.")
                    else:
                        # Maybe Agregar doesn't increment the fila index, check again
                        existing2 = fes(sid, "xpath", "//DataItem[starts-with(@Name,'Artículo Fila')]")
                        print(f"  After Agregar: {len(existing2)} Artículo cells")
                        for e in existing2:
                            print(f"    '{at(sid, e, 'Name')}'")
                        # Try finding the last Artículo cell
                        for f in range(10):
                            c = fe(sid, "name", f"Artículo Fila {f}")
                            if c:
                                last_fila = f
                        art_cell = fe(sid, "name", f"Artículo Fila {last_fila}")
                        print(f"  Using last found: Artículo Fila {last_fila}")
                        fila = last_fila
                
                if not art_cell:
                    print(f"  STILL NOT FOUND. Trying to Tab from previous position to reach new row...")
                    # The active element might be positioned at the end of previous row
                    # More tabs might reach the new row
                    active = api("POST", f"/session/{sid}/element/active", {})
                    av = active.get("value", {})
                    ae = None
                    if av and not isinstance(av, str):
                        ae = av.get("ELEMENT") or (list(av.values())[0] if av else None)
                    if ae:
                        aname = at(sid, ae, "Name")
                        print(f"  Active element: '{aname}'")
                        # Type article code directly into active element
                        print(f"  Typing {code} into active element...")
                        ky(sid, ae, code)
                        ky(sid, ae, ["\ue004"])
                        time.sleep(3)
                        continue
                    else:
                        print(f"  No active element. Cannot continue.")
                        break
            
            print(f"  Clicking Artículo Fila {fila}...")
            clk(sid, art_cell)
            time.sleep(1)
            
            print(f"  Typing {code}...")
            ky(sid, art_cell, code)
            time.sleep(1)
            
            # Use Tab to confirm article
            print(f"  Tab to confirm...")
            ky(sid, art_cell, ["\ue004"])
            time.sleep(4)
            
            # Check if a search/selection popup appeared
            dialog = fe(sid, "class name", "#32770")
            if dialog:
                dname = at(sid, dialog, "Name")
                print(f"  *** DIALOG: '{dname}' ***")
                # Try to accept it
                ok_btn = fe(sid, "name", "Aceptar")
                if not ok_btn: ok_btn = fe(sid, "name", "OK")
                if ok_btn:
                    clk(sid, ok_btn)
                    time.sleep(2)
            
            # Enter quantity in Cant cell
            cant_cell = fe(sid, "name", f"Cant. Fila {fila}, Sin orden.")
            if cant_cell:
                print(f"  Clicking Cant. Fila {fila}...")
                clk(sid, cant_cell)
                time.sleep(1)
                print(f"  Typing 1...")
                ky(sid, cant_cell, "1")
                # Use Tab to move out of Cant cell
                ky(sid, cant_cell, ["\ue004"])
                time.sleep(3)
            else:
                print(f"  Cant. cell NOT FOUND")
            
            # Check what rows exist now
            arts_after = fes(sid, "xpath", "//DataItem[starts-with(@Name,'Artículo Fila')]")
            print(f"  After entering: {len(arts_after)} Artículo cells")
            for a in arts_after:
                print(f"    '{at(sid, a, 'Name')}'")
            
            # Check row count / filas field
            filas_f = fe(sid, "accessibility id", "txtFilas")
            if filas_f:
                print(f"  txtFilas: '{at(sid, filas_f, 'Name')}'")

        # Final check
        print(f"\n{'='*50}")
        print("FINAL STATE")
        print(f"{'='*50}")
        
        total = fe(sid, "accessibility id", "txtVrTotal")
        if total: print(f"Total: '{at(sid, total, 'Name')}'")
        
        filas = fe(sid, "accessibility id", "txtFilas")
        if filas: print(f"Filas: '{at(sid, filas, 'Name')}'")
        
        subtotal = fe(sid, "accessibility id", "txtVrSubtotal")
        if subtotal: print(f"SubTotal: '{at(sid, subtotal, 'Name')}'")

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
