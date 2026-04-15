"""
Approach: After clicking PE-PEDIDO, check ALL windows in the system via Root.
Also try: search box approach and keyboard tree navigation.
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

def wait_find(sid, strategy, value, timeout=30):
    for i in range(timeout):
        e = fe(sid, strategy, value)
        if e: return e
        time.sleep(1)
    return None

def list_windows(sid, label):
    """Find all Window elements via Root session"""
    windows = fes(sid, "xpath", "//Window")
    print(f"\n  [{label}] All windows ({len(windows)}):")
    for i, w in enumerate(windows[:20]):
        name = at(sid, w, "Name")
        aid = at(sid, w, "AutomationId")
        cls = at(sid, w, "ClassName")
        if name:
            print(f"    [{i}] name='{name}' aid='{aid}' class='{cls}'")
    return windows

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)
    
    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]
    print(f"Root: {sid}")
    scoped_sid = None
    
    try:
        # LOGIN
        wait_find(sid, "accessibility id", "txtUser")
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, "brayan")
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, "cafe123.")
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        
        frm = wait_find(sid, "accessibility id", "frmInicioComercial", 30)
        if not frm: print("ERROR: no frmInicioComercial"); return
        print("Login OK")
        time.sleep(5)
        
        # SCOPED SESSION
        nwh = int(at(sid, frm, "NativeWindowHandle"))
        scoped = api("POST", "/session", {
            "desiredCapabilities": {
                "platformName": "Windows", "deviceName": "WindowsPC",
                "appTopLevelWindow": hex(nwh)
            }
        })
        scoped_sid = scoped.get("sessionId")
        
        # Baseline windows
        print("=== BASELINE WINDOWS ===")
        list_windows(sid, "Before")
        
        # Expand Movimientos
        mov = fe(sid, "name", "Movimientos")
        clk(sid, mov)
        time.sleep(4)
        
        # Find and click PE - PEDIDO
        pe = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
        if not pe: print("PE - PEDIDO not found!"); return
        print(f"\nPE - PEDIDO found. Clicking...")
        clk(scoped_sid, pe)
        time.sleep(8)
        
        # Check ALL windows now
        print("\n=== AFTER CLICK - ALL WINDOWS ===")
        list_windows(sid, "After click")
        
        # Check for dialog boxes
        for name in ["Documentos", "Seleccionar", "Documento", "Pedido", "PE02", "Seleccione"]:
            e = fe(sid, "name", name) 
            if e:
                print(f"\n*** Found dialog: '{name}' aid='{at(sid, e, 'AutomationId')}' class='{at(sid, e, 'ClassName')}'")
        
        # Check if main window title changed
        frm2 = fe(sid, "accessibility id", "frmInicioComercial")
        if frm2:
            title = at(sid, frm2, "Name")
            print(f"\nMain window title: '{title}'")
        
        # === APPROACH B: Use search box ===
        print("\n\n=== APPROACH B: SEARCH BOX ===")
        search = fe(sid, "accessibility id", "teSearch")
        if search:
            print("teSearch found in Root. Clicking...")
            clk(sid, search)
            time.sleep(1)
            print("Typing 'Pedido'...")
            ky(sid, search, "Pedido")
            time.sleep(3)
            
            # Now look for filtered results - the tree should update
            # Try pressing Down + Enter
            print("Pressing Down arrow...")
            ky(sid, search, ["\uE015"])  # Down arrow
            time.sleep(1)
            print("Pressing Enter...")
            ky(sid, search, ["\uE007"])  # Enter
            time.sleep(8)
            
            # Check what happened
            print("=== AFTER SEARCH + ENTER ===")
            list_windows(sid, "After search")
            
            # Also try finding PE02 or any document form
            for name in ["PE02", "Documentos", "Pedido", "Seleccion", "Documento"]:
                e = fe(sid, "name", name)
                if e:
                    print(f"  Found: '{name}' aid='{at(sid, e, 'AutomationId')}' class='{at(sid, e, 'ClassName')}'")
            
            # Scoped check
            ds(scoped_sid)
            frm3 = fe(sid, "accessibility id", "frmInicioComercial")
            nwh3 = int(at(sid, frm3, "NativeWindowHandle"))
            scoped3 = api("POST", "/session", {
                "desiredCapabilities": {
                    "platformName": "Windows", "deviceName": "WindowsPC",
                    "appTopLevelWindow": hex(nwh3)
                }
            })
            scoped_sid = scoped3.get("sessionId")
            
            # Quick check for new elements in scoped
            for xpath in ["//DataGrid", "//Table", "//ComboBox", "//Custom"]:
                els = fes(scoped_sid, "xpath", xpath)
                if els:
                    print(f"  {xpath}: {len(els)} found")
                    for eid in els[:5]:
                        print(f"    name='{at(scoped_sid, eid, 'Name')}' aid='{at(scoped_sid, eid, 'AutomationId')}'")
            
            # Count all Edit fields
            edits = fes(scoped_sid, "xpath", "//Edit")
            print(f"\n  Edit fields: {len(edits)}")
            for eid in edits:
                name = at(scoped_sid, eid, "Name")
                aid = at(scoped_sid, eid, "AutomationId")
                print(f"    name='{name}' aid='{aid}'")
            
            # Count all Tab items
            tabitems = fes(scoped_sid, "xpath", "//TabItem") 
            print(f"\n  TabItems: {len(tabitems)}")
            for eid in tabitems:
                name = at(scoped_sid, eid, "Name")
                print(f"    name='{name}'")

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
