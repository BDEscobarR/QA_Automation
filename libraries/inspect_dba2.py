"""
Login with DBA admin credentials, click each accordion section, find sub-items by name search.
"""
import json, time, subprocess
from urllib.request import Request, urlopen

REMOTE_URL = "http://127.0.0.1:4723"
APP = r"C:\Users\BrayanEscobar\AppData\Local\BnetEmpresarial\current\ERP.Empresarial.exe"
USER = "dba"
PASSWORD = "F]J8al7QEhklTCnne]oI"

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
        return val.get("ELEMENT") or list(val.values())[0] if val else None
    return val

def fes(sid, s, v):
    """Find multiple elements"""
    r = api("POST", f"/session/{sid}/elements", {"using": s, "value": v})
    val = r.get("value", [])
    if isinstance(val, list):
        els = []
        for e in val:
            if isinstance(e, dict):
                eid = e.get("ELEMENT") or list(e.values())[0]
                els.append(eid)
        return els
    return []

def at(sid, eid, n):
    r = api("GET", f"/session/{sid}/element/{eid}/attribute/{n}")
    return r.get("value", "")

def clk(sid, eid): api("POST", f"/session/{sid}/element/{eid}/click", {})
def ky(sid, eid, t): api("POST", f"/session/{sid}/element/{eid}/value", {"value": list(t)})
def cl(sid, eid): api("POST", f"/session/{sid}/element/{eid}/clear", {})
def ds(sid):
    try: api("DELETE", f"/session/{sid}")
    except: pass

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)
    
    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]

    try:
        for _ in range(30):
            if fe(sid, "accessibility id", "txtUser"): break
            time.sleep(1)
        
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, USER)
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, PASSWORD)
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        
        for i in range(30):
            if fe(sid, "accessibility id", "frmInicioComercial"): print(f"Ready after {i+1}s"); break
            time.sleep(1)
        time.sleep(5)
        
        # Get ERP window handle for scoped session
        frm = fe(sid, "accessibility id", "frmInicioComercial")
        nwh = int(at(sid, frm, "NativeWindowHandle"))
        print(f"ERP window handle: {nwh} / hex: {hex(nwh)}")
        
        # Create scoped session on the ERP window
        scoped = api("POST", "/session", {
            "desiredCapabilities": {
                "platformName": "Windows",
                "deviceName": "WindowsPC",
                "appTopLevelWindow": hex(nwh)
            }
        })
        scoped_sid = scoped.get("sessionId")
        print(f"Scoped session: {scoped_sid}")
        
        # Main accordion sections to explore
        sections = ["Movimientos", "Procesos", "Catálogos.", "Configurar", "Herramientas", "Informes", "Conectores"]
        
        # Terms to search for in each section
        search_terms = [
            "Pedido", "Remisi", "Factura", "Devoluci", "Venta", "Compra", "Cliente",
            "Producto", "Almac", "Inventar", "Cotiza", "Orden", "Pago", "Cobro",
            "Aproba", "Recepci", "Traspaso", "Ajuste", "Nota"
        ]
        
        for section in sections:
            print(f"\n{'='*50}")
            print(f"=== SECTION: {section} ===")
            print(f"{'='*50}")
            
            # Click the section in Root session
            elem = fe(sid, "name", section)
            if not elem:
                print(f"  Section '{section}' NOT FOUND")
                continue
            
            clk(sid, elem)
            time.sleep(3)
            
            # Now find ALL TreeItem elements via XPath in scoped session
            tree_items = fes(scoped_sid, "xpath", "//TreeItem")
            print(f"  TreeItem count: {len(tree_items)}")
            for ti in tree_items:
                name = at(scoped_sid, ti, "Name")
                aid = at(scoped_sid, ti, "AutomationId")
                if name and not any(x in name for x in ["Teams", "Edge", "Chrome", "Visual Studio", "Code"]):
                    print(f"    - '{name}' (id={aid})")
            
            # Also try finding ListItem elements
            list_items = fes(scoped_sid, "xpath", "//ListItem")
            if list_items:
                print(f"  ListItem count: {len(list_items)}")
                for li in list_items[:20]:
                    name = at(scoped_sid, li, "Name")
                    if name:
                        print(f"    - '{name}'")
        
        # Also try getting page source from scoped session (smaller than Root)
        print(f"\n{'='*50}")
        print("=== SCOPED SESSION PAGE SOURCE ===")
        src_r = api("GET", f"/session/{scoped_sid}/source")
        src = src_r.get("value", "")
        if src:
            with open("reports/dba_scoped.xml", "w", encoding="utf-8") as f:
                f.write(src)
            print(f"Saved scoped source: {len(src)} chars")
        else:
            print(f"Source error: {src_r}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        ds(sid)
        if 'scoped_sid' in dir():
            ds(scoped_sid)
        subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)

if __name__ == "__main__":
    main()
