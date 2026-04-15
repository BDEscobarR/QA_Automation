"""
Inspect the pedido grid after entering client 100723.
Discover how to interact with grid cells for articles.
"""
import json, time, subprocess, xml.etree.ElementTree as ET
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
        if "error" in val or "message" in val: return None
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
        # LOGIN
        wait_find(sid, "accessibility id", "txtUser")
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, "brayan")
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, "cafe123.")
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        frm = wait_find(sid, "accessibility id", "frmInicioComercial", 30)
        print("Login OK")
        time.sleep(5)

        # SCOPED SESSION
        nwh = int(at(sid, frm, "NativeWindowHandle"))
        scoped_sid = api("POST", "/session", {
            "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": hex(nwh)}
        }).get("sessionId")

        # Navigate: Movimientos → PE-PEDIDO → PE02
        mov = fe(sid, "name", "Movimientos"); clk(sid, mov); time.sleep(4)
        pe = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']"); clk(scoped_sid, pe); time.sleep(3)
        pe02 = fe(scoped_sid, "name", "PE02 - PEDIDO"); clk(scoped_sid, pe02); time.sleep(8)
        
        print("Formulario PE02 abierto")
        
        # Enter client
        print("\n=== Entering client 100723 ===")
        txt_cl = fe(sid, "accessibility id", "txtCliente")
        if txt_cl:
            cl(sid, txt_cl)
            ky(sid, txt_cl, "100723")
            # Tab to confirm
            ky(sid, txt_cl, ["\ue004"])
            time.sleep(5)
            print("Client entered. Checking form state...")
        
        # Check vendedor and lista precio after client
        cbo_vend = fe(sid, "accessibility id", "cboVendedor")
        if cbo_vend:
            vend_val = at(sid, cbo_vend, "Name")
            print(f"Vendedor: '{vend_val}'")
        
        cbo_lp = fe(sid, "accessibility id", "cboListprecio")
        if cbo_lp:
            lp_val = at(sid, cbo_lp, "Name")
            print(f"Lista Precio: '{lp_val}'")
        
        # === INSPECT GRID ===
        print("\n=== INSPECTING GRID ===")
        grid = fe(sid, "accessibility id", "GridVent")
        if grid:
            print(f"Grid found: class='{at(sid, grid, 'ClassName')}'")
            
            # Get grid's child elements
            # Try DataItem children
            data_items = fes(sid, "xpath", "//DataGrid[@AutomationId='GridVent']//DataItem")
            print(f"DataItems in grid: {len(data_items)}")
            for i, di in enumerate(data_items[:20]):
                name = at(sid, di, "Name")
                aid = at(sid, di, "AutomationId")
                print(f"  [{i}] name='{name}' aid='{aid}'")
            
            # Try Custom children (rows)
            customs = fes(sid, "xpath", "//DataGrid[@AutomationId='GridVent']//Custom")
            print(f"\nCustom rows: {len(customs)}")
            for i, c in enumerate(customs[:5]):
                name = at(sid, c, "Name")
                print(f"  [{i}] name='{name}'")
            
            # Click the first Artículo cell
            print("\n=== Clicking 'Artículo Fila 0' ===")
            art_cell = fe(sid, "name", "Artículo Fila 0")
            if art_cell:
                print(f"  Found! aid='{at(sid, art_cell, 'AutomationId')}' class='{at(sid, art_cell, 'ClassName')}'")
                clk(sid, art_cell)
                time.sleep(1)
                
                # After clicking, check what's focused/editable
                # Type article code
                print("  Typing 000001...")
                ky(sid, art_cell, "000001")
                time.sleep(1)
                
                # Tab to move to next column
                print("  Tab...")
                ky(sid, art_cell, ["\ue004"])
                time.sleep(2)
                
                # Check grid state after article entry
                data_items2 = fes(sid, "xpath", "//DataGrid[@AutomationId='GridVent']//DataItem")
                print(f"\nDataItems after article: {len(data_items2)}")
                for i, di in enumerate(data_items2[:20]):
                    name = at(sid, di, "Name")
                    print(f"  [{i}] '{name}'")
                
                # Look for Cant cell
                cant_cell = fe(sid, "name", "Cant. Fila 0, Sin orden.")
                if cant_cell:
                    print(f"\nCant cell found: '{at(sid, cant_cell, 'Name')}'")
                    clk(sid, cant_cell)
                    time.sleep(1)
                    ky(sid, cant_cell, "5")
                    ky(sid, cant_cell, ["\ue004"])
                    time.sleep(2)
                    print("  Quantity entered")
            else:
                print("  Artículo Fila 0 NOT FOUND")
                # Try clicking grid directly
                clk(sid, grid)
                time.sleep(1)
                
                # Check what Edit appeared
                edits = fes(sid, "xpath", "//Edit")
                print(f"\n  Edits after grid click: {len(edits)}")
                for e in edits[:10]:
                    name = at(sid, e, "Name")
                    aid = at(sid, e, "AutomationId")
                    print(f"    name='{name}' aid='{aid}'")
        
        # Check totals
        print("\n=== TOTALS ===")
        for aid in ["txtVrSubtotal", "txtVrTotal", "txtFilas", "txtCantPos", "txtCantNeg"]:
            e = fe(sid, "accessibility id", aid)
            if e:
                val = at(sid, e, "Name")
                print(f"  {aid}: '{val}'")
        
        # Check Grabar button
        print("\n=== GRABAR BUTTON ===")
        grabar = fe(sid, "name", "Grabar")
        if grabar:
            print(f"  Found: aid='{at(sid, grabar, 'AutomationId')}' enabled='{at(sid, grabar, 'IsEnabled')}'")

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
