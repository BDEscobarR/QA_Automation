"""
Double-click PE - PEDIDO TreeItem using WinAppDriver actions API.
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

def at(sid, eid, n):
    r = api("GET", f"/session/{sid}/element/{eid}/attribute/{n}")
    return r.get("value", "")

def clk(sid, eid): return api("POST", f"/session/{sid}/element/{eid}/click", {})

def double_click(sid, eid):
    """Double click using WinAppDriver moveto + doubleclick"""
    r1 = api("POST", f"/session/{sid}/moveto", {"element": eid})
    print(f"  moveto result: {r1}")
    r2 = api("POST", f"/session/{sid}/doubleclick", {})
    print(f"  doubleclick result: {r2}")
    return r2

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
        
        # CLICK MOVIMIENTOS via root
        print("\n=== Clicking Movimientos ===")
        mov = fe(sid, "name", "Movimientos")
        if not mov: print("Movimientos not found"); return
        clk(sid, mov)
        time.sleep(4)
        
        # FIND PE - PEDIDO via XPath in scoped 
        print("\n=== Finding PE - PEDIDO ===")
        pe = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
        if not pe:
            print("Not found in scoped. Trying root...")
            pe = fe(sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
            if pe:
                print(f"Found in root: {pe}")
                # Try double-click via root
                print("\n=== Double-clicking PE - PEDIDO (root) ===")
                double_click(sid, pe)
            else:
                print("Not found anywhere!"); return
        else:
            print(f"Found in scoped: {pe}")
            
            # Method 1: Double-click via actions
            print("\n=== Method 1: Double-click via actions (scoped) ===")
            double_click(scoped_sid, pe)
        
        time.sleep(8)
        
        # Check what opened
        print("\n=== CHECKING RESULT ===")
        src = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        with open("reports/brayan_pe_dblclk.xml", "w", encoding="utf-8") as f:
            f.write(src)
        print(f"Source: {len(src)} chars")
        
        all_elems = get_all_named(src)
        
        # Look specifically for new forms/windows
        windows = [e for e in all_elems if e["tag"] == "Window"]
        print(f"\nWindows ({len(windows)}):")
        for w in windows:
            print(f"  name='{w['name']}' aid='{w['aid']}'")
        
        # Tabs - check if a new tab opened
        tabs = [e for e in all_elems if e["tag"] in ["Tab", "TabItem"]]
        print(f"\nTabs ({len(tabs)}):")
        for t in tabs:
            print(f"  <{t['tag']}> name='{t['name']}' aid='{t['aid']}'")
        
        # DataGrid / Table for document list
        grids = [e for e in all_elems if e["tag"] in ["DataGrid", "Table", "Custom", "DataItem"]]
        print(f"\nGrids/Custom ({len(grids)}):")
        for g in grids[:20]:
            print(f"  <{g['tag']}> name='{g['name']}' aid='{g['aid']}' class='{g['class']}'")
        
        # Edit fields (might be the search/document fields)
        edits = [e for e in all_elems if e["tag"] in ["Edit", "ComboBox"]]
        print(f"\nEdits ({len(edits)}):")
        for ed in edits:
            print(f"  <{ed['tag']}> name='{ed['name']}' aid='{ed['aid']}'")
        
        # All buttons
        buttons = [e for e in all_elems if e["tag"] == "Button"]
        print(f"\nButtons ({len(buttons)}):")
        skip = {"Minimizar", "Restaurar", "Cerrar", "Columna a la izquierda", 
                "Columna a la derecha", "Página a la derecha", "Página a la izquierda"}
        for b in buttons:
            if b["name"] not in skip:
                print(f"  name='{b['name']}' aid='{b['aid']}'")
        
        # ToolBars
        toolbars = [e for e in all_elems if e["tag"] in ["ToolBar", "MenuBar"]]
        print(f"\nToolbars ({len(toolbars)}):")
        for tb in toolbars:
            print(f"  name='{tb['name']}' aid='{tb['aid']}'")
        
        # If nothing new opened, try Method 2: click twice quickly via scoped
        if len(windows) <= 2:
            print("\n=== Method 2: Two quick clicks ===")
            pe2 = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
            if pe2:
                clk(scoped_sid, pe2)
                time.sleep(0.3)
                clk(scoped_sid, pe2)
                time.sleep(8)
                
                src2 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
                with open("reports/brayan_pe_twoclicks.xml", "w", encoding="utf-8") as f:
                    f.write(src2)
                print(f"Source after 2 clicks: {len(src2)} chars")
                
                all2 = get_all_named(src2)
                windows2 = [e for e in all2 if e["tag"] == "Window"]
                print(f"Windows: {len(windows2)}")
                for w in windows2:
                    print(f"  name='{w['name']}' aid='{w['aid']}'")
                
                tabs2 = [e for e in all2 if e["tag"] in ["Tab", "TabItem"]]
                print(f"Tabs: {len(tabs2)}")
                for t in tabs2:
                    print(f"  <{t['tag']}> name='{t['name']}' aid='{t['aid']}'")
                
                # New elements check
                old_names = set((e["name"], e["aid"]) for e in all_elems)
                new_elems = [e for e in all2 if (e["name"], e["aid"]) not in old_names]
                print(f"\nNEW elements after 2 clicks: {len(new_elems)}")
                for ne in new_elems[:30]:
                    print(f"  <{ne['tag']}> name='{ne['name']}' aid='{ne['aid']}' class='{ne['class']}'")
        
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
