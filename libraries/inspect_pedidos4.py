"""
Step-by-step accordion navigation: Login → expand Movimientos → expand VENTAS → click PE - PEDIDO
Key insight: scoped session sees TreeItems. Must expand step by step.
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
def dblclk(sid, eid): 
    # WinAppDriver: double-click via actions
    loc = api("GET", f"/session/{sid}/element/{eid}/location")
    locv = loc.get("value", {})
    x, y = int(locv.get("x", 0)), int(locv.get("y", 0))
    sz = api("GET", f"/session/{sid}/element/{eid}/size").get("value", {})
    cx = x + int(sz.get("width", 0)) // 2
    cy = y + int(sz.get("height", 0)) // 2
    # Use moveto + doubleclick action
    api("POST", f"/session/{sid}/moveto", {"element": eid})
    api("POST", f"/session/{sid}/doubleclick", {})
    return {"x": cx, "y": cy}

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

def get_tree_names(xml_str):
    """Extract all TreeItem names from XML"""
    xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
    root = ET.fromstring(xml_str.encode("utf-8"))
    names = []
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "TreeItem":
            names.append(elem.attrib.get("Name", ""))
    return names

def get_all_named(xml_str):
    """Extract all named elements from XML"""
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
        print(f"Scoped: {scoped_sid}")
        
        # === A: Get initial tree state ===
        src0 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        tree0 = get_tree_names(src0)
        print(f"\nInitial tree: {tree0}")
        
        # === B: Click Movimientos in Root session ===
        print("\n=== CLICKING MOVIMIENTOS (Root) ===")
        mov = fe(sid, "name", "Movimientos")
        if not mov: print("ERROR: Movimientos not found"); return
        clk(sid, mov)
        time.sleep(4)
        
        # Check expanded tree
        src1 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        tree1 = get_tree_names(src1)
        print(f"Tree after Movimientos click: {tree1}")
        new_items = [t for t in tree1 if t not in tree0]
        print(f"New items: {new_items}")
        
        if not new_items:
            print("No new items. Trying double-click...")
            dblclk(sid, mov)
            time.sleep(4)
            src1b = api("GET", f"/session/{scoped_sid}/source").get("value", "")
            tree1b = get_tree_names(src1b)
            new_items = [t for t in tree1b if t not in tree0]
            print(f"After double-click: {new_items}")
        
        if not new_items:
            # Try clicking Movimientos in scoped session
            print("Trying scoped session click...")
            mov_s = fe(scoped_sid, "name", "Movimientos")
            if mov_s:
                clk(scoped_sid, mov_s)
                time.sleep(4)
                src1c = api("GET", f"/session/{scoped_sid}/source").get("value", "")
                tree1c = get_tree_names(src1c)
                new_items = [t for t in tree1c if t not in tree0]
                print(f"After scoped click: {new_items}")
            else:
                print("Movimientos not found in scoped either")
        
        # === C: Find and click VENTAS ===
        print("\n=== LOOKING FOR VENTAS ===")
        ventas = None
        for session_id in [scoped_sid, sid]:
            for name in ["VENTAS", "Ventas", "ventas"]:
                ventas = fe(session_id, "name", name)
                if ventas:
                    print(f"  Found '{name}' in {'scoped' if session_id == scoped_sid else 'root'}")
                    clk(session_id, ventas)
                    time.sleep(3)
                    break
            if ventas: break
        
        if not ventas:
            print("  VENTAS not found. Current tree state:")
            src_now = api("GET", f"/session/{scoped_sid}/source").get("value", "")
            tree_now = get_tree_names(src_now)
            print(f"  {tree_now}")
        
        # === D: Find and double-click PE - PEDIDO ===
        print("\n=== LOOKING FOR PE - PEDIDO ===")
        pe = None
        for session_id in [scoped_sid, sid]:
            for name in ["PE - PEDIDO", "PE-PEDIDO", "PE - Pedido", "Pedido", "PE-Pedidos"]:
                pe = fe(session_id, "name", name)
                if pe:
                    sess_name = 'scoped' if session_id == scoped_sid else 'root'
                    print(f"  Found '{name}' in {sess_name}")
                    print(f"  class='{at(session_id, pe, 'ClassName')}' aid='{at(session_id, pe, 'AutomationId')}'")
                    # Double-click to open
                    print("  Double-clicking...")
                    dblclk(session_id, pe)
                    time.sleep(5)
                    break
            if pe: break
        
        if not pe:
            print("  PE - PEDIDO not found anywhere")
            # Last resort: list ALL named elements from scoped XML
            src_final = api("GET", f"/session/{scoped_sid}/source").get("value", "")
            all_elems = get_all_named(src_final)
            with open("reports/brayan_nav_final.xml", "w", encoding="utf-8") as f:
                f.write(src_final)
            print(f"  Saved source ({len(src_final)} chars). All elements:")
            for el in all_elems:
                if el["tag"] in ["TreeItem", "Button", "Edit", "Window"]:
                    print(f"    <{el['tag']}> name='{el['name']}' aid='{el['aid']}'")
            return
        
        # === E: Inspect what opened (document list or form) ===
        print("\n=== AFTER PE - PEDIDO CLICK - INSPECTING ===")
        time.sleep(3)
        
        # Check for new windows
        for wname in ["Documentos", "Pedido", "Movimiento", "Seleccionar"]:
            w = fe(sid, "name", wname)
            if w:
                print(f"  New window found: '{wname}' aid='{at(sid, w, 'AutomationId')}' class='{at(sid, w, 'ClassName')}'")
        
        # Get updated scoped source
        src_after = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        with open("reports/brayan_after_pe.xml", "w", encoding="utf-8") as f:
            f.write(src_after)
        print(f"Saved after-PE source: {len(src_after)} chars")
        
        all_after = get_all_named(src_after)
        print(f"\nNew/interesting elements after PE-PEDIDO click:")
        for el in all_after:
            # Show new forms, grids, edits, buttons
            if el["tag"] in ["Window", "DataGrid", "Table", "Edit", "ComboBox", "Button", "Custom", "DataItem", "ListItem"]:
                if el["name"] or el["aid"]:
                    print(f"  <{el['tag']}> name='{el['name']}' aid='{el['aid']}' class='{el['class']}'")
        
        # Also search for PE02 
        print("\n=== Searching for PE02 ===")
        for name in ["PE02", "PE-02", "PE 02"]:
            for s in [scoped_sid, sid]:
                e = fe(s, "name", name)
                if e:
                    sess = 'scoped' if s == scoped_sid else 'root'
                    print(f"  FOUND '{name}' in {sess}: aid='{at(s, e, 'AutomationId')}' class='{at(s, e, 'ClassName')}'")

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
