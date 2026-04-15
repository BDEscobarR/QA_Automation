"""
Detailed grid inspection: enter 3 articles one by one and check grid state.
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

def count_grid_rows(sid):
    """Count how many Artículo Fila cells exist"""
    arts = fes(sid, "xpath", "//DataGrid[@AutomationId='GridVent']//DataItem[starts-with(@Name,'Artículo Fila')]")
    return len(arts)

def get_row_values(sid, fila):
    """Get key values from a grid row"""
    result = {}
    for col_name_pattern in ["Artículo", "Cant.", "Precio", "Total"]:
        if col_name_pattern == "Artículo":
            cell = fe(sid, "name", f"Artículo Fila {fila}")
        else:
            cell = fe(sid, "name", f"{col_name_pattern} Fila {fila}, Sin orden.")
        if cell:
            val = at(sid, cell, "Value.Value")
            name = at(sid, cell, "Name")
            result[col_name_pattern] = f"name='{name}' value='{val}'"
        else:
            result[col_name_pattern] = "NOT FOUND"
    return result

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)

    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]
    scoped_sid = None

    try:
        # LOGIN
        wait_find(sid, "accessibility id", "txtUser")
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, "brayan")
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, "cafe123.")
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        frm = wait_find(sid, "accessibility id", "frmInicioComercial", 30)
        print("Login OK"); time.sleep(5)

        # SCOPED SESSION + NAVIGATE
        nwh = int(at(sid, frm, "NativeWindowHandle"))
        scoped_sid = api("POST", "/session", {
            "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": hex(nwh)}
        }).get("sessionId")
        mov = fe(sid, "name", "Movimientos"); clk(sid, mov); time.sleep(4)
        pe = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']"); clk(scoped_sid, pe); time.sleep(3)
        pe02 = fe(scoped_sid, "name", "PE02 - PEDIDO"); clk(scoped_sid, pe02); time.sleep(8)
        print("Formulario PE02 abierto")

        # Enter client
        txt_cl = fe(sid, "accessibility id", "txtCliente")
        cl(sid, txt_cl); ky(sid, txt_cl, "100723"); ky(sid, txt_cl, ["\ue004"]); time.sleep(5)
        
        # Check client was accepted
        client_val = at(sid, txt_cl, "Value.Value")
        client_name = at(sid, txt_cl, "Name")
        print(f"Client: name='{client_name}' value='{client_val}'")

        # Check initial grid state
        rows0 = count_grid_rows(sid)
        print(f"\n=== INITIAL GRID: {rows0} Artículo cells ===")
        
        # Article 1: 000001
        articles = ["000001", "000002", "000003"]
        for idx, code in enumerate(articles):
            fila = idx
            print(f"\n--- Entering article {code} in Fila {fila} ---")
            
            art_cell = fe(sid, "name", f"Artículo Fila {fila}")
            if not art_cell:
                print(f"  *** Artículo Fila {fila} NOT FOUND! Trying to wait...")
                art_cell = wait_find(sid, "name", f"Artículo Fila {fila}", 10)
                if not art_cell:
                    print(f"  *** Still not found. Checking all Artículo cells:")
                    arts = fes(sid, "xpath", "//DataItem[starts-with(@Name,'Artículo Fila')]")
                    for a in arts:
                        print(f"      '{at(sid, a, 'Name')}'")
                    
                    # Try Add button
                    agregar = fe(sid, "name", "Agregar")
                    if agregar:
                        print("  Trying 'Agregar' button...")
                        clk(sid, agregar)
                        time.sleep(2)
                        art_cell = fe(sid, "name", f"Artículo Fila {fila}")
                        if art_cell:
                            print(f"  Found after Agregar!")
                        else:
                            print(f"  Still not found after Agregar. Aborting.")
                            break
                    else:
                        break
            
            print(f"  Clicking Artículo Fila {fila}...")
            clk(sid, art_cell)
            time.sleep(1)
            
            print(f"  Typing {code}...")
            ky(sid, art_cell, code)
            time.sleep(1)
            
            print(f"  Tab...")
            ky(sid, art_cell, ["\ue004"])
            time.sleep(3)
            
            # Check if article was accepted - look at cell value
            art_check = fe(sid, "name", f"Artículo Fila {fila}")
            if art_check:
                art_val = at(sid, art_check, "Value.Value")
                art_name = at(sid, art_check, "Name")
                print(f"  After Tab: name='{art_name}' value='{art_val}'")
            
            # Enter quantity
            cant_cell = fe(sid, "name", f"Cant. Fila {fila}, Sin orden.")
            if cant_cell:
                print(f"  Clicking Cant. Fila {fila}...")
                clk(sid, cant_cell)
                time.sleep(1)
                print(f"  Typing 1...")
                ky(sid, cant_cell, "1")
                ky(sid, cant_cell, ["\ue004"])
                time.sleep(3)
                
                # Check quantity value
                cant_check = fe(sid, "name", f"Cant. Fila {fila}, Sin orden.")
                if cant_check:
                    cant_val = at(sid, cant_check, "Value.Value")
                    cant_name = at(sid, cant_check, "Name")
                    print(f"  After Qty: name='{cant_name}' value='{cant_val}'")
            else:
                print(f"  *** Cant. cell NOT FOUND!")
            
            # Check grid state
            rows = count_grid_rows(sid)
            print(f"  Grid rows after article {idx+1}: {rows}")
            
            # Check row values
            vals = get_row_values(sid, fila)
            for k, v in vals.items():
                print(f"    {k}: {v}")
            
            # Check if a modal/dialog appeared
            dialog = fe(sid, "class name", "#32770")
            if dialog:
                dialog_name = at(sid, dialog, "Name")
                print(f"  *** DIALOG DETECTED: '{dialog_name}'")
                # Try to dismiss
                ok = fe(sid, "name", "Aceptar")
                if ok: clk(sid, ok); time.sleep(2)
                else:
                    ok = fe(sid, "name", "OK")
                    if ok: clk(sid, ok); time.sleep(2)

        # Final state
        print("\n=== FINAL GRID STATE ===")
        total_rows = count_grid_rows(sid)
        print(f"Total Artículo cells: {total_rows}")
        
        # Check totals
        for aid in ["txtVrSubtotal", "txtVrTotal", "txtFilas"]:
            e = fe(sid, "accessibility id", aid)
            if e:
                val = at(sid, e, "Value.Value")
                name = at(sid, e, "Name")
                print(f"  {aid}: name='{name}' value='{val}'")

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
