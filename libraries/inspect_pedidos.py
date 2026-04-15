"""
Step-by-step UI inspection: Login → Movimientos → Ventas → PE-Pedidos → PE02 form
Uses brayan/cafe123. credentials. Captures element info at each step.
"""
import json, time, subprocess, sys
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
    els = []
    if isinstance(val, list):
        for e in val:
            if isinstance(e, dict):
                eid = e.get("ELEMENT") or list(e.values())[0]
                els.append(eid)
    return els

def at(sid, eid, n):
    r = api("GET", f"/session/{sid}/element/{eid}/attribute/{n}")
    return r.get("value", "")

def clk(sid, eid): return api("POST", f"/session/{sid}/element/{eid}/click", {})
def ky(sid, eid, t): return api("POST", f"/session/{sid}/element/{eid}/value", {"value": list(t)})
def cl(sid, eid): return api("POST", f"/session/{sid}/element/{eid}/clear", {})
def ds(sid):
    try: api("DELETE", f"/session/{sid}")
    except: pass

def describe_elements(sid, strategy, value, label="", max_items=30):
    """Find elements and print their properties."""
    els = fes(sid, strategy, value)
    print(f"  [{label}] Found {len(els)} elements via {strategy}='{value}'")
    for i, eid in enumerate(els[:max_items]):
        name = at(sid, eid, "Name")
        aid = at(sid, eid, "AutomationId")
        cls = at(sid, eid, "ClassName")
        enabled = at(sid, eid, "IsEnabled")
        print(f"    [{i}] name='{name}' | aid='{aid}' | class='{cls}' | enabled={enabled}")
    return els

def wait_and_find(sid, strategy, value, timeout=30):
    for i in range(timeout):
        e = fe(sid, strategy, value)
        if e: return e
        time.sleep(1)
    return None

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP])
    time.sleep(20)
    
    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]
    print(f"Root session: {sid}")
    
    try:
        # === STEP 1: LOGIN ===
        print("\n" + "="*60)
        print("STEP 1: LOGIN")
        print("="*60)
        wait_and_find(sid, "accessibility id", "txtUser")
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, "brayan")
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, "cafe123.")
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        
        frm = wait_and_find(sid, "accessibility id", "frmInicioComercial", 30)
        if not frm:
            print("ERROR: frmInicioComercial not found")
            return
        print("Login OK - frmInicioComercial visible")
        time.sleep(5)
        
        # === STEP 2: CLICK MOVIMIENTOS ===
        print("\n" + "="*60)
        print("STEP 2: CLICK MOVIMIENTOS")
        print("="*60)
        mov = fe(sid, "name", "Movimientos")
        if mov:
            print(f"  Found 'Movimientos': aid='{at(sid, mov, 'AutomationId')}' class='{at(sid, mov, 'ClassName')}'")
            clk(sid, mov)
            time.sleep(3)
            print("  Clicked Movimientos")
        else:
            print("  ERROR: Movimientos not found")
            return

        # === STEP 3: LOOK FOR VENTAS SUB-OPTION ===
        print("\n" + "="*60)
        print("STEP 3: SEARCH FOR 'Ventas' SUB-OPTION")
        print("="*60)
        
        # Try various name patterns
        for name in ["Ventas", "ventas", "Venta", "VE-Ventas", "Ventas ", " Ventas"]:
            e = fe(sid, "name", name)
            if e:
                print(f"  FOUND '{name}': aid='{at(sid, e, 'AutomationId')}' class='{at(sid, e, 'ClassName')}'")
                clk(sid, e)
                time.sleep(2)
                print(f"  Clicked '{name}'")
                break
        else:
            print("  'Ventas' not found by direct name. Searching TreeItems...")
            describe_elements(sid, "xpath", "//TreeItem", "TreeItems")
            
            # Also search by partial name
            for partial in ["Vent", "vent", "PE", "Pedido", "pedido"]:
                e = fe(sid, "name", partial)
                if e:
                    print(f"  Found partial match '{partial}': aid='{at(sid, e, 'AutomationId')}'")
        
        # === STEP 4: LOOK FOR PE-PEDIDOS ===
        print("\n" + "="*60)
        print("STEP 4: SEARCH FOR 'PE-Pedidos' OR SIMILAR")
        print("="*60)
        
        for name in ["PE-Pedidos", "PE - Pedidos", "Pedidos", "PE-PEDIDOS", "pe-pedidos", 
                      "PE Pedidos", "Pedidos de Venta", "PE-Pedido"]:
            e = fe(sid, "name", name)
            if e:
                print(f"  FOUND '{name}': aid='{at(sid, e, 'AutomationId')}' class='{at(sid, e, 'ClassName')}'")
                clk(sid, e)
                time.sleep(2)
                print(f"  Clicked '{name}'")
                break
        else:
            print("  PE-Pedidos not found. Listing all visible TreeItems again...")
            describe_elements(sid, "xpath", "//TreeItem", "TreeItems after Ventas")
        
        # === STEP 5: LOOK FOR PE02 DOCUMENT ===
        print("\n" + "="*60)
        print("STEP 5: SEARCH FOR 'PE02' DOCUMENT")
        print("="*60)
        time.sleep(2)
        
        for name in ["PE02", "PE-02", "PE 02", "pe02"]:
            e = fe(sid, "name", name)
            if e:
                print(f"  FOUND '{name}': aid='{at(sid, e, 'AutomationId')}' class='{at(sid, e, 'ClassName')}'")
                break
        else:
            print("  PE02 not found directly. Checking what appeared...")
            # Look for common form controls
            describe_elements(sid, "xpath", "//DataGrid", "DataGrids")
            describe_elements(sid, "xpath", "//List", "Lists")
            describe_elements(sid, "xpath", "//ListItem", "ListItems")
            describe_elements(sid, "xpath", "//DataItem", "DataItems")
            
            # Check for any new windows/forms
            for aid in ["frmDocumentos", "frmPedido", "frmPedidos", "frmMovimientos",
                        "frmDocumentoBuscar", "frmSeleccion", "gridView"]:
                e = fe(sid, "accessibility id", aid)
                if e:
                    print(f"  Found form '{aid}': name='{at(sid, e, 'Name')}' class='{at(sid, e, 'ClassName')}'")
        
        # === STEP 6: CAPTURE CURRENT WINDOW STATE === 
        print("\n" + "="*60)
        print("STEP 6: CURRENT VISIBLE ELEMENTS (buttons, edits, combos)")
        print("="*60)
        describe_elements(sid, "xpath", "//Button", "Buttons", 20)
        describe_elements(sid, "xpath", "//Edit", "Edits", 20)
        describe_elements(sid, "xpath", "//ComboBox", "ComboBoxes", 15)
        describe_elements(sid, "xpath", "//Custom", "Custom controls", 15)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        ds(sid)
        subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
        print("\nDone.")

if __name__ == "__main__":
    main()
