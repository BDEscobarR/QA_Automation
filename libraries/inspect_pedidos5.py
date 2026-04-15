"""
Use XPath to find TreeItems in scoped session and navigate to PE-PEDIDO form.
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

def get_all_named(xml_str):
    xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
    root = ET.fromstring(xml_str.encode("utf-8"))
    elements = []
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        name = elem.attrib.get("Name", "")
        aid = elem.attrib.get("AutomationId", "")
        cls = elem.attrib.get("ClassName", "")
        if name or aid:
            elements.append({"tag": tag, "name": name, "aid": aid, "class": cls})
    return elements

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
        
        # CLICK MOVIMIENTOS 
        print("\n=== Clicking Movimientos ===")
        mov = fe(sid, "name", "Movimientos")
        if not mov: print("Movimientos not found"); return
        clk(sid, mov)
        time.sleep(4)
        
        # Try XPath to find TreeItem[@Name='PE - PEDIDO'] in scoped session
        print("\n=== Finding PE - PEDIDO via XPath (scoped) ===")
        pe_xpath = "//TreeItem[@Name='PE - PEDIDO']"
        pe = fe(scoped_sid, "xpath", pe_xpath)
        if pe:
            print(f"  FOUND via XPath! Element: {pe}")
            print(f"  Name: {at(scoped_sid, pe, 'Name')}")
            print(f"  Clicking via scoped session...")
            clk(scoped_sid, pe)
            time.sleep(5)
        else:
            print(f"  Not found via XPath in scoped. Trying root...")
            pe = fe(sid, "xpath", pe_xpath)
            if pe:
                print(f"  FOUND in root via XPath!")
                clk(sid, pe)
                time.sleep(5)
            else:
                print("  Not found in root either.")
                
                # Try all TreeItems via XPath
                print("\n  Trying //TreeItem in scoped...")
                items = fes(scoped_sid, "xpath", "//TreeItem")
                print(f"  Found {len(items)} TreeItems in scoped")
                for i, eid in enumerate(items):
                    n = at(scoped_sid, eid, "Name")
                    print(f"    [{i}] '{n}'")
                    if "PEDIDO" in n.upper():
                        print(f"      >>> Clicking this one!")
                        clk(scoped_sid, eid)
                        time.sleep(5)
                        pe = eid
                        break
                
                if not pe:
                    print("\n  Trying //TreeItem in root...")
                    items_r = fes(sid, "xpath", "//TreeItem")
                    print(f"  Found {len(items_r)} TreeItems in root")
                    for i, eid in enumerate(items_r[:30]):
                        n = at(sid, eid, "Name")
                        print(f"    [{i}] '{n}'")
                        if "PEDIDO" in n.upper():
                            print(f"      >>> Clicking this one!")
                            clk(sid, eid)
                            time.sleep(5)
                            pe = eid
                            break
        
        if not pe:
            print("\nERROR: Could not find/click PE - PEDIDO")
            return
        
        # === Check what opened ===
        print("\n=== CHECKING WHAT OPENED ===")
        src = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        with open("reports/brayan_pe_opened.xml", "w", encoding="utf-8") as f:
            f.write(src)
        print(f"Source size: {len(src)} chars")
        
        all_elems = get_all_named(src)
        
        # Look for new windows/forms
        print("\nWindows:")
        for el in all_elems:
            if el["tag"] == "Window":
                print(f"  name='{el['name']}' aid='{el['aid']}'")
        
        # Look for DataGrid/Table/Grid 
        print("\nGrids/Tables:")
        for el in all_elems:
            if el["tag"] in ["DataGrid", "Table", "DataItem", "Custom"]:
                print(f"  <{el['tag']}> name='{el['name']}' aid='{el['aid']}' class='{el['class']}'")
        
        # Look for Edit/ComboBox fields
        print("\nEdit fields:")
        for el in all_elems:
            if el["tag"] in ["Edit", "ComboBox"]:
                print(f"  <{el['tag']}> name='{el['name']}' aid='{el['aid']}' class='{el['class']}'")
        
        # Look for Buttons
        print("\nButtons (excluding system):")
        system_buttons = {"Minimizar", "Restaurar", "Cerrar", "Columna a la izquierda", 
                          "Columna a la derecha", "Página a la derecha", "Página a la izquierda"}
        for el in all_elems:
            if el["tag"] == "Button" and el["name"] not in system_buttons:
                print(f"  name='{el['name']}' aid='{el['aid']}'")
        
        # Look for Tabs
        print("\nTabs:")
        for el in all_elems:
            if el["tag"] in ["Tab", "TabItem"]:
                print(f"  <{el['tag']}> name='{el['name']}' aid='{el['aid']}'")
        
        # Search for PE02 
        print("\n=== Searching PE02 ===")
        for name in ["PE02", "PE-02", "PE 02"]:
            e = fe(scoped_sid, "name", name)
            if e: print(f"  Scoped: FOUND '{name}'")
            e2 = fe(sid, "name", name)
            if e2: print(f"  Root: FOUND '{name}'")

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
