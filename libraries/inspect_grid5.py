"""
Try different approaches to add 3+ articles to grid:
1. DOWN arrow after quantity entry
2. Check if grid re-numbers rows
3. Try clicking grid after rows to force new row
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
def dbl(sid, eid): api("POST", f"/session/{sid}/element/{eid}/doubleclick", {})
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

def list_art_filas(sid):
    arts = fes(sid, "xpath", "//DataItem[starts-with(@Name,'Artículo Fila')]")
    names = [at(sid, a, "Name") for a in arts]
    print(f"  Artículo cells ({len(names)}): {names}")
    return names

def active_element(sid):
    r = api("POST", f"/session/{sid}/element/active", {})
    val = r.get("value", {})
    if isinstance(val, dict) and "error" not in val:
        eid = val.get("ELEMENT") or (list(val.values())[0] if val else None)
        if eid:
            return eid, at(sid, eid, "Name"), at(sid, eid, "AutomationId"), at(sid, eid, "ClassName")
    return None, None, None, None

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

        # Enter client
        txt_cl = fe(sid, "accessibility id", "txtCliente")
        cl(sid, txt_cl); ky(sid, txt_cl, "100723"); ky(sid, txt_cl, ["\ue004"]); time.sleep(5)
        print(f"Vendedor: '{at(sid, fe(sid, 'accessibility id', 'cboVendedor'), 'Name')}'")

        # === ARTICLE 1: 000001 ===
        print("\n=== ARTICLE 1: 000001 ===")
        art0 = fe(sid, "name", "Artículo Fila 0")
        clk(sid, art0); time.sleep(1)
        ky(sid, art0, "000001")
        ky(sid, art0, ["\ue004"])  # Tab
        time.sleep(3)
        
        cant0 = fe(sid, "name", "Cant. Fila 0, Sin orden.")
        clk(sid, cant0); time.sleep(1)
        ky(sid, cant0, "1")
        time.sleep(1)
        
        # Before leaving, check active element
        eid, n, aid, cls = active_element(sid)
        print(f"Active after typing qty: name='{n}' aid='{aid}'")
        
        # Try DOWN arrow key to go to next row
        print("Pressing DOWN arrow...")
        ky(sid, cant0, ["\ue015"])  # DOWN arrow
        time.sleep(3)
        
        eid2, n2, aid2, cls2 = active_element(sid)
        print(f"Active after DOWN: name='{n2}' aid='{aid2}'")
        list_art_filas(sid)
        
        # === ARTICLE 2: 000002 ===
        print("\n=== ARTICLE 2: 000002 ===")
        # After DOWN, what's the last Artículo Fila?
        art1 = fe(sid, "name", "Artículo Fila 1")
        if art1:
            clk(sid, art1); time.sleep(1)
            ky(sid, art1, "000002")
            ky(sid, art1, ["\ue004"])
            time.sleep(3)
            
            cant1 = fe(sid, "name", "Cant. Fila 1, Sin orden.")
            if cant1:
                clk(sid, cant1); time.sleep(1)
                ky(sid, cant1, "1")
                time.sleep(1)
                
                # Try DOWN arrow again
                print("Pressing DOWN arrow...")
                ky(sid, cant1, ["\ue015"])
                time.sleep(3)
                
                eid3, n3, aid3, cls3 = active_element(sid)
                print(f"Active after DOWN: name='{n3}' aid='{aid3}'")
                list_art_filas(sid)
        
        # === ARTICLE 3: 000003 ===
        print("\n=== ARTICLE 3: 000003 ===")
        # Check all art filas
        names = list_art_filas(sid)
        
        # Try to find Fila 2
        art2 = fe(sid, "name", "Artículo Fila 2")
        if art2:
            print("  Fila 2 EXISTS!")
            clk(sid, art2); time.sleep(1)
            ky(sid, art2, "000003")
            ky(sid, art2, ["\ue004"])
            time.sleep(3)
        else:
            print("  Fila 2 not found. Trying alternative approaches...")
            
            # APPROACH A: Use the grid element and keyboard
            print("\n  APPROACH A: Grid + keyboard navigation")
            grid = fe(sid, "accessibility id", "GridVent")
            if grid:
                # Check if grid can receive DOWN key
                ky(sid, grid, ["\ue015"])  # DOWN
                time.sleep(2)
                art2a = fe(sid, "name", "Artículo Fila 2")
                if art2a:
                    print("  Found Fila 2 after grid DOWN!")
                else:
                    print("  Still no Fila 2")
            
            # APPROACH B: Click below the last row in the grid
            print("\n  APPROACH B: Check last row, try to click below it")
            # Get the bounding rectangle of the grid
            grid_bbox = at(sid, grid, "BoundingRectangle") if grid else "N/A"
            print(f"  Grid bbox: {grid_bbox}")
            
            # Get last row's bbox
            art1b = fe(sid, "name", "Artículo Fila 1")
            if art1b:
                row1_bbox = at(sid, art1b, "BoundingRectangle")
                print(f"  Fila 1 bbox: {row1_bbox}")
            
            # APPROACH C: Send CTRL+DOWN or INSERT to grid  
            print("\n  APPROACH C: INSERT key on grid")
            if grid:
                ky(sid, grid, ["\ue03c"])  # INSERT
                time.sleep(2)
                art2c = fe(sid, "name", "Artículo Fila 2")
                if art2c:
                    print("  Found Fila 2 after INSERT!")
                else:
                    print("  Still no Fila 2")
                    list_art_filas(sid)
            
            # APPROACH D: Click on Artículo Fila 1 and check if it's empty (for new entry)
            print("\n  APPROACH D: Is Fila 1 an empty row? Check its value")
            art1d = fe(sid, "name", "Artículo Fila 1")
            if art1d:
                # Check all attributes of the cell
                for attr_name in ["Value.Value", "LegacyIAccessible.Value", "Name", "HelpText"]:
                    v = at(sid, art1d, attr_name)
                    print(f"  Fila 1 {attr_name}: '{v}'")
                
                # Also check Cant Fila 1
                cant1d = fe(sid, "name", "Cant. Fila 1, Sin orden.")
                if cant1d:
                    for attr_name in ["Value.Value", "LegacyIAccessible.Value", "Name"]:
                        v = at(sid, cant1d, attr_name)
                        print(f"  Cant Fila 1 {attr_name}: '{v}'")
            
            # Also check Fila 0 values for comparison
            print("\n  Fila 0 comparison:")
            art0d = fe(sid, "name", "Artículo Fila 0")
            if art0d:
                for attr_name in ["Value.Value", "LegacyIAccessible.Value", "Name", "HelpText"]:
                    v = at(sid, art0d, attr_name)
                    print(f"  Fila 0 {attr_name}: '{v}'")
            
            cant0d = fe(sid, "name", "Cant. Fila 0, Sin orden.")
            if cant0d:
                for attr_name in ["Value.Value", "LegacyIAccessible.Value"]:
                    v = at(sid, cant0d, attr_name)
                    print(f"  Cant Fila 0 {attr_name}: '{v}'")
            
            # APPROACH E: Check all DataItems in the grid
            print("\n  APPROACH E: Complete DataItem dump for GridVent")
            all_items = fes(sid, "xpath", "//DataGrid[@AutomationId='GridVent']//DataItem")
            print(f"  Total DataItems: {len(all_items)}")
            for i, item in enumerate(all_items):
                n = at(sid, item, "Name")
                print(f"    [{i}] '{n}'")
                if i > 40: break

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
