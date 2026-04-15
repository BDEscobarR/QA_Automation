"""
Inspect: proper client entry + article entry flow.
Focus on how the client field and grid behave after typing.
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

def src(sid):
    return api("GET", f"/session/{sid}/source").get("value", "")

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

        # ===========================
        # CLIENT ENTRY - DETAILED
        # ===========================
        print("\n=== CLIENT ENTRY ===")
        txt_cl = fe(sid, "accessibility id", "txtCliente")
        print(f"txtCliente before: Name='{at(sid, txt_cl, 'Name')}' ClassName='{at(sid, txt_cl, 'ClassName')}'")
        
        cl(sid, txt_cl)
        ky(sid, txt_cl, "100723")
        time.sleep(2)
        print(f"After typing 100723: Name='{at(sid, txt_cl, 'Name')}'")
        
        # Check if a popup/list appeared after typing
        lists = fes(sid, "class name", "WindowsForms10.LISTBOX.app.0.3d893c_r3_ad1")
        print(f"Listboxes found: {len(lists)}")
        for lb in lists[:5]:
            print(f"  Listbox: Name='{at(sid, lb, 'Name')}' BBox='{at(sid, lb, 'BoundingRectangle')}'")
        
        popups = fes(sid, "xpath", "//Window")
        print(f"Windows found: {len(popups)}")
        
        # Try pressing Enter to confirm (instead of Tab)
        print("\nPressing ENTER to confirm client...")
        ky(sid, txt_cl, ["\ue007"])
        time.sleep(5)
        
        # Check if a search dialog appeared
        print("Checking for search dialogs...")
        dialog = fe(sid, "class name", "#32770")
        if dialog:
            dname = at(sid, dialog, "Name")
            print(f"  Dialog found: '{dname}'")
            # Save page source snippet
            page = src(sid)
            # Find dialog-related XML
            idx = page.find("#32770")
            if idx > 0:
                print(f"  Dialog XML snippet: {page[max(0,idx-200):idx+500]}")
        
        # Check if a new form/window appeared (like a client search form)
        forms = fes(sid, "xpath", "//Window[contains(@Name,'Buscar') or contains(@Name,'buscar') or contains(@Name,'Cliente') or contains(@Name,'Search')]")
        print(f"Search-like windows: {len(forms)}")
        for f in forms[:3]:
            print(f"  '{at(sid, f, 'Name')}' class='{at(sid, f, 'ClassName')}'")
        
        # Check any new window
        all_wins = fes(sid, "xpath", "//Window")
        print(f"\nAll top-level windows: {len(all_wins)}")
        for w in all_wins[:10]:
            name = at(sid, w, "Name")
            aid = at(sid, w, "AutomationId")
            cls = at(sid, w, "ClassName")
            print(f"  name='{name}' aid='{aid}' class='{cls}'")

        # Check vendedor field - if it auto-populated, client was accepted
        cbo_v = fe(sid, "accessibility id", "cboVendedor")
        if cbo_v:
            vname = at(sid, cbo_v, "Name")
            print(f"\nVendedor: '{vname}'")
        
        # Check client field again
        txt_cl2 = fe(sid, "accessibility id", "txtCliente")
        if txt_cl2:
            cname = at(sid, txt_cl2, "Name")
            print(f"txtCliente now: '{cname}'")

        # Try Tab from client
        print("\n--- Now trying TAB from client field ---")
        ky(sid, txt_cl2, ["\ue004"])
        time.sleep(5)
        
        # Check again
        cbo_v2 = fe(sid, "accessibility id", "cboVendedor")
        if cbo_v2:
            vname2 = at(sid, cbo_v2, "Name")
            print(f"Vendedor after Tab: '{vname2}'")
        
        txt_cl3 = fe(sid, "accessibility id", "txtCliente")
        if txt_cl3:
            cname3 = at(sid, txt_cl3, "Name")
            print(f"txtCliente after Tab: '{cname3}'")

        # Now check if there's a search dialog we missed
        all_wins2 = fes(sid, "xpath", "//Window")
        print(f"\nWindows after Tab: {len(all_wins2)}")
        for w in all_wins2[:10]:
            name = at(sid, w, "Name")
            aid = at(sid, w, "AutomationId")
            if name:
                print(f"  name='{name}' aid='{aid}'")

        # ===========================
        # TRY GRID ARTICLE
        # ===========================
        print("\n=== GRID ARTICLE TEST ===")
        art0 = fe(sid, "name", "Artículo Fila 0")
        if art0:
            print(f"Artículo Fila 0 found. Clicking...")
            clk(sid, art0)
            time.sleep(1)
            
            print("Typing 000001...")
            ky(sid, art0, "000001")
            time.sleep(2)
            
            # Check for autocomplete/popup before Tab
            lists2 = fes(sid, "class name", "WindowsForms10.LISTBOX.app.0.3d893c_r3_ad1")
            print(f"Listboxes after typing article: {len(lists2)}")
            
            print("Pressing ENTER to confirm article...")
            ky(sid, art0, ["\ue007"])
            time.sleep(4)
            
            # Check if something happened
            art0b = fe(sid, "name", "Artículo Fila 0")
            if art0b:
                artname = at(sid, art0b, "Name")
                print(f"Artículo Fila 0 after Enter: '{artname}'")
            
            # Check Cant
            cant0 = fe(sid, "name", "Cant. Fila 0, Sin orden.")
            if cant0:
                cantname = at(sid, cant0, "Name")
                print(f"Cant. Fila 0: '{cantname}'")
                clk(sid, cant0)
                time.sleep(1)
                ky(sid, cant0, "5")
                ky(sid, cant0, ["\ue004"])
                time.sleep(3)
                
                cant0b = fe(sid, "name", "Cant. Fila 0, Sin orden.")
                if cant0b:
                    print(f"Cant after input: '{at(sid, cant0b, 'Name')}'")
            
            # Check if Fila 1 appeared  
            art1 = fe(sid, "name", "Artículo Fila 1")
            if art1:
                print(f"\nArtículo Fila 1 exists: '{at(sid, art1, 'Name')}'")
            else:
                print(f"\nArtículo Fila 1 NOT FOUND")
                
                # Check what the active element is
                active = api("POST", f"/session/{sid}/element/active", {})
                av = active.get("value", {})
                if av and not isinstance(av, str):
                    ae = av.get("ELEMENT") or (list(av.values())[0] if av else None)
                    if ae:
                        print(f"Active element: name='{at(sid, ae, 'Name')}' aid='{at(sid, ae, 'AutomationId')}' class='{at(sid, ae, 'ClassName')}'")
            
            # Check total
            total = fe(sid, "accessibility id", "txtVrTotal")
            if total:
                tname = at(sid, total, "Name")
                print(f"\nTotal: '{tname}'")
            
            filas = fe(sid, "accessibility id", "txtFilas")
            if filas:
                fname = at(sid, filas, "Name")
                print(f"Filas: '{fname}'")
        else:
            print("Artículo Fila 0 NOT FOUND - grid may not be ready")
            
            # Check grid
            grid = fe(sid, "accessibility id", "GridVent")
            if grid:
                print(f"Grid exists: class='{at(sid, grid, 'ClassName')}'")
                # Try clicking grid directly
                clk(sid, grid)
                time.sleep(2)
                art0c = fe(sid, "name", "Artículo Fila 0")
                if art0c:
                    print("Artículo Fila 0 appeared after clicking grid!")

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
