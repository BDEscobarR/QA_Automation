"""
Expand PE - PEDIDO TreeItem to reveal PE02 child.
Use ExpandCollapse pattern approach and keyboard arrows.
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

def get_tree_names(xml_str):
    xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
    root = ET.fromstring(xml_str.encode("utf-8"))
    names = []
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "TreeItem":
            name = elem.attrib.get("Name", "")
            expand = elem.attrib.get("ExpandCollapseState", "?")
            names.append(f"{name} [expand={expand}]")
    return names

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
        r = api("POST", "/session", {
            "desiredCapabilities": {
                "platformName": "Windows", "deviceName": "WindowsPC",
                "appTopLevelWindow": hex(nwh)
            }
        })
        scoped_sid = r.get("sessionId")
        
        # Expand Movimientos
        mov = fe(sid, "name", "Movimientos")
        clk(sid, mov)
        time.sleep(4)
        
        # Get tree state
        src = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        tree = get_tree_names(src)
        print(f"\nTree after Movimientos: {len(tree)} items")
        for t in tree:
            print(f"  {t}")
        
        # Find PE - PEDIDO
        pe = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
        if not pe: print("\nPE - PEDIDO not found!"); return
        
        # Check its expand/collapse state
        expand_state = at(scoped_sid, pe, "ExpandCollapseState")
        is_expanded = at(scoped_sid, pe, "IsExpanded")
        print(f"\nPE - PEDIDO: ExpandCollapseState='{expand_state}' IsExpanded='{is_expanded}'")
        
        # === Attempt 1: Click to select, then keyboard Right arrow to expand ===
        print("\n=== Attempt 1: Click + Right arrow ===")
        clk(scoped_sid, pe)
        time.sleep(1)
        # Send Right arrow key to expand
        ky(scoped_sid, pe, ["\uE014"])  # Right arrow
        time.sleep(3)
        
        src1 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        tree1 = get_tree_names(src1)
        new_items = [t for t in tree1 if t not in tree]
        print(f"New items after Right arrow: {new_items}")
        
        if not new_items:
            # === Attempt 2: Double-click to expand ===
            print("\n=== Attempt 2: Double-click ===")
            pe2 = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
            api("POST", f"/session/{scoped_sid}/moveto", {"element": pe2})
            api("POST", f"/session/{scoped_sid}/doubleclick", {})
            time.sleep(5)
            
            src2 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
            tree2 = get_tree_names(src2)
            new_items2 = [t for t in tree2 if t not in tree]
            print(f"New items after double-click: {new_items2}")
            
            # Also check for new UI elements (not just tree items)
            with open("reports/brayan_pe_expand.xml", "w", encoding="utf-8") as f:
                f.write(src2)
            print(f"Source saved: {len(src2)} chars")
            
            # Parse for ALL Window/TabItem/DataGrid elements
            xml_str = src2.replace('encoding="utf-16"', 'encoding="utf-8"')
            root = ET.fromstring(xml_str.encode("utf-8"))
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if tag in ["Window", "TabItem", "DataGrid", "Table"]:
                    name = elem.attrib.get("Name", "")
                    aid = elem.attrib.get("AutomationId", "")
                    print(f"  <{tag}> name='{name}' aid='{aid}'")
        
        if not new_items and not new_items2 if 'new_items2' in dir() else True:
            # === Attempt 3: Click PE-PEDIDO and check for completely new tabs/windows ===
            print("\n=== Attempt 3: Check for MDI child changes ===")
            
            # Maybe the form opened as a Tab inside XtraTabControl1
            tabs_before = fes(scoped_sid, "xpath", "//TabItem")
            print(f"TabItems: {len(tabs_before)}")
            for t in tabs_before:
                print(f"  '{at(scoped_sid, t, 'Name')}'")
            
            # Re-find and click PE-PEDIDO, wait longer
            pe3 = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
            if pe3:
                clk(scoped_sid, pe3)
                time.sleep(2)
                clk(scoped_sid, pe3)
                time.sleep(12)  # Wait longer
                
                # Re-create scoped session to get fresh state
                ds(scoped_sid)
                frm3 = fe(sid, "accessibility id", "frmInicioComercial")
                nwh3 = int(at(sid, frm3, "NativeWindowHandle"))
                r3 = api("POST", "/session", {
                    "desiredCapabilities": {
                        "platformName": "Windows", "deviceName": "WindowsPC",
                        "appTopLevelWindow": hex(nwh3)
                    }
                })
                scoped_sid = r3.get("sessionId")
                
                src3 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
                with open("reports/brayan_pe_fresh.xml", "w", encoding="utf-8") as f:
                    f.write(src3)
                print(f"\nFresh scoped source: {len(src3)} chars")
                
                tree3 = get_tree_names(src3)
                print(f"Tree items: {len(tree3)}")
                
                tabs_after = fes(scoped_sid, "xpath", "//TabItem")
                print(f"TabItems: {len(tabs_after)}")
                for t in tabs_after:
                    name = at(scoped_sid, t, "Name")
                    print(f"  '{name}'")
                
                # Check for ANY new Window elements
                wins = fes(scoped_sid, "xpath", "//Window")
                print(f"Window elements: {len(wins)}")
                for w in wins:
                    print(f"  '{at(scoped_sid, w, 'Name')}' aid='{at(scoped_sid, w, 'AutomationId')}'")
                
                edits = fes(scoped_sid, "xpath", "//Edit")
                print(f"Edit fields: {len(edits)}")
                for e in edits:
                    name = at(scoped_sid, e, "Name")
                    aid = at(scoped_sid, e, "AutomationId")
                    print(f"  name='{name}' aid='{aid}'")
        
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
