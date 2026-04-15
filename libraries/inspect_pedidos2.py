"""
Focused inspection: After login, try to navigate Movimientos > Ventas > PE-Pedidos
Using both Root session name searches and keyboard/search approaches.
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

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)
    
    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]
    print(f"Root session: {sid}")
    scoped_sid = None
    
    try:
        # LOGIN
        wait_find(sid, "accessibility id", "txtUser")
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, "brayan")
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, "cafe123.")
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        
        frm = wait_find(sid, "accessibility id", "frmInicioComercial", 30)
        if not frm:
            print("ERROR: frmInicioComercial not found"); return
        print("Login OK")
        time.sleep(5)
        
        # Create scoped session
        nwh = int(at(sid, frm, "NativeWindowHandle"))
        scoped = api("POST", "/session", {
            "desiredCapabilities": {
                "platformName": "Windows", "deviceName": "WindowsPC",
                "appTopLevelWindow": hex(nwh)
            }
        })
        scoped_sid = scoped.get("sessionId")
        print(f"Scoped session: {scoped_sid}\n")
        
        # === STEP 1: Explore accordion structure ===
        print("="*60)
        print("STEP 1: Accordion elements BEFORE clicking anything")
        print("="*60)
        
        # Search using accessibility_id for accordion components
        for aid in ["accordionControl1", "ElementTree", "teSearch"]:
            e = fe(sid, "accessibility id", aid)
            status = "FOUND" if e else "NOT FOUND"
            if e:
                print(f"  {aid}: {status} name='{at(sid, e, 'Name')}' class='{at(sid, e, 'ClassName')}'")
            else:
                print(f"  {aid}: {status}")
        
        # Find all name matches for menu sections
        for name in ["Movimientos", "Ventas", "Compras", "PE-Pedidos", "Pedidos"]:
            e = fe(sid, "name", name)
            if e:
                cls = at(sid, e, "ClassName")
                aid = at(sid, e, "AutomationId")
                print(f"  name='{name}': FOUND class='{cls}' aid='{aid}'")
            else:
                print(f"  name='{name}': NOT FOUND")
        
        # === STEP 2: Click Movimientos ===
        print("\n" + "="*60)
        print("STEP 2: Click Movimientos and check children")
        print("="*60)
        mov = fe(sid, "name", "Movimientos")
        if not mov:
            print("ERROR: Movimientos not found"); return
        clk(sid, mov)
        time.sleep(3)
        print("Clicked Movimientos")
        
        # Now search for sub-items
        sub_names = ["Ventas", "Compras", "Inventarios", "Almacen", "Almacén",
                      "Bancos", "CxC", "CxP", "Cuentas", "Produccion", "Producción",
                      "Pedidos", "PE-Pedidos", "Remisiones", "Facturas", "Devoluciones"]
        
        print("\nSearching for sub-items by name:")
        for name in sub_names:
            e = fe(sid, "name", name)
            if e:
                cls = at(sid, e, "ClassName")
                aid = at(sid, e, "AutomationId")
                print(f"  FOUND: name='{name}' class='{cls}' aid='{aid}'")
        
        # === STEP 3: Try scoped session element dump ===
        print("\n" + "="*60)
        print("STEP 3: Scoped session page source (for ERP window only)")
        print("="*60)
        
        src_r = api("GET", f"/session/{scoped_sid}/source")
        src = src_r.get("value", "")
        if src and "error" not in src_r:
            with open("reports/brayan_scoped.xml", "w", encoding="utf-8") as f:
                f.write(src)
            print(f"Scoped source saved: {len(src)} chars")
            
            # Parse for interesting elements
            import xml.etree.ElementTree as ET
            xml_str = src.replace('encoding="utf-16"', 'encoding="utf-8"')
            root = ET.fromstring(xml_str.encode("utf-8"))
            
            print("\nAll elements with Name containing relevant words:")
            keywords = ["venta", "pedido", "remis", "factur", "movim", "compra", "alm", "invent", "PE"]
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                name = elem.attrib.get("Name", "")
                aid = elem.attrib.get("AutomationId", "")
                if name:
                    for kw in keywords:
                        if kw.lower() in name.lower():
                            print(f"  <{tag}> Name='{name}' AutomationId='{aid}'")
                            break
            
            print("\nAll unique element types with names (first 50):")
            count = 0
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                name = elem.attrib.get("Name", "")
                aid = elem.attrib.get("AutomationId", "")
                if name and count < 50:
                    print(f"  <{tag}> Name='{name}' aid='{aid}'")
                    count += 1
        else:
            print(f"Scoped source error: {src_r}")
        
        # === STEP 4: Try using the search/filter box ===
        print("\n" + "="*60)
        print("STEP 4: Try accordion search box")
        print("="*60)
        
        search = fe(sid, "accessibility id", "teSearch")
        if search:
            print(f"  teSearch found. Clicking and typing 'Pedido'...")
            clk(sid, search)
            time.sleep(1)
            cl(sid, search)
            ky(sid, search, "Pedido")
            time.sleep(3)
            
            # Check what appeared
            print("  After typing 'Pedido' - searching for results:")
            for name in ["PE-Pedidos", "Pedidos", "Pedido", "PE - Pedidos"]:
                e = fe(sid, "name", name)
                if e:
                    print(f"    FOUND: '{name}' class='{at(sid, e, 'ClassName')}' aid='{at(sid, e, 'AutomationId')}'")
            
            # Also get scoped source again to see filtered tree
            src2 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
            if src2:
                with open("reports/brayan_after_search.xml", "w", encoding="utf-8") as f:
                    f.write(src2)
                print(f"  Scoped source after search saved: {len(src2)} chars")
        else:
            print("  teSearch NOT FOUND in root session")
            # Try scoped
            search2 = fe(scoped_sid, "accessibility id", "teSearch")
            if search2:
                print("  teSearch found in SCOPED session")
            else:
                print("  teSearch NOT FOUND in scoped session either")
        
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
