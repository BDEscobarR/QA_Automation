"""
Multiple strategies to open PE - PEDIDO:
1. Select + Enter key
2. Click via coordinates on Root session
3. Check for new windows/dialogs via Root
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
        
        # Focus the ERP window
        clk(sid, frm)
        time.sleep(1)
        
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
        print("\n=== Expanding Movimientos ===")
        mov = fe(sid, "name", "Movimientos")
        if not mov: print("Movimientos not found"); return
        clk(sid, mov)
        time.sleep(4)
        
        # Find PE - PEDIDO via XPath
        pe = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
        if not pe: print("PE - PEDIDO not found!"); return
        print(f"PE - PEDIDO found: {pe}")
        
        # Get element location
        loc = api("GET", f"/session/{scoped_sid}/element/{pe}/location")
        sz = api("GET", f"/session/{scoped_sid}/element/{pe}/size")
        print(f"Location: {loc}")
        print(f"Size: {sz}")
        
        # === STRATEGY 1: Click + Enter key ===
        print("\n=== Strategy 1: Click + Enter ===")
        clk(scoped_sid, pe)
        time.sleep(1)
        # Send Enter key
        # WinAppDriver uses \uE007 for Enter
        ky(scoped_sid, pe, ["\uE007"])
        time.sleep(5)
        
        # Check for new windows via ROOT
        src1 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        all1 = get_all_named(src1)
        wins1 = [e for e in all1 if e["tag"] == "Window"]
        print(f"Windows after Enter: {len(wins1)}")
        for w in wins1:
            print(f"  name='{w['name']}' aid='{w['aid']}'")
        
        tabs1 = [e for e in all1 if e["tag"] in ["TabItem"]]
        print(f"TabItems: {len(tabs1)}")
        for t in tabs1:
            print(f"  name='{t['name']}' aid='{t['aid']}'")
        
        grids1 = [e for e in all1 if e["tag"] in ["DataGrid", "Table", "Custom"]]
        print(f"Grids/Custom: {len(grids1)}")
        
        # Look for new edits
        edits1 = [e for e in all1 if e["tag"] in ["Edit", "ComboBox"]]
        print(f"Edits: {len(edits1)}")
        for ed in edits1:
            if ed["aid"] not in ["teSearch", ""]:
                print(f"  NEW: <{ed['tag']}> name='{ed['name']}' aid='{ed['aid']}'")
        
        if len(wins1) > 2 or len(tabs1) > 1 or len(grids1) > 0:
            print("\n*** FORM OPENED! ***")
            with open("reports/brayan_pe_form.xml", "w", encoding="utf-8") as f:
                f.write(src1)
            print(f"Saved: {len(src1)} chars")
            # Print all non-tree elements
            for el in all1:
                if el["tag"] not in ["TreeItem", "Tree", "Pane"] or el["aid"]:
                    if el["tag"] in ["Window", "Edit", "ComboBox", "Button", "DataGrid", "Table", 
                                     "DataItem", "Custom", "TabItem", "ToolBar", "MenuItem", "ListItem"]:
                        print(f"  <{el['tag']}> name='{el['name']}' aid='{el['aid']}' class='{el['class']}'")
        else:
            print("\nNo form change. Trying Strategy 2...")
            
            # === STRATEGY 2: Use the keyboard shortcut buttons ===
            # The ERP has buttons like Ctrl+N, Ctrl+E etc.
            # Maybe there's a keyboard shortcut for Pedido
            print("\n=== Strategy 2: Checking all shortcut buttons ===")
            btns = [e for e in all1 if e["tag"] == "Button" and e["aid"].startswith("simpleButton")]
            for b in btns:
                print(f"  Shortcut: name='{b['name']}' aid='{b['aid']}'")
            
            # === STRATEGY 3: Try clicking via absolute coordinates from root ===
            print("\n=== Strategy 3: Click coordinates via Root ===")
            locv = loc.get("value", {})
            szv = sz.get("value", {})
            if locv and szv:
                x = int(locv.get("x", 0)) + int(szv.get("width", 0)) // 2
                y = int(locv.get("y", 0)) + int(szv.get("height", 0)) // 2
                print(f"  Clicking at ({x}, {y}) via Root")
                # Click at absolute position
                api("POST", f"/session/{sid}/moveto", {"xoffset": x, "yoffset": y})
                api("POST", f"/session/{sid}/click", {"button": 0})
                time.sleep(1)
                api("POST", f"/session/{sid}/click", {"button": 0})
                time.sleep(5)
                
                # But wait -- that might not map correctly because scoped coords != desktop coords
                # Let me re-find in root session first
                pe_root = fe(sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
                if pe_root:
                    loc_r = api("GET", f"/session/{sid}/element/{pe_root}/location")
                    print(f"  Root location: {loc_r}")
                    # Double click via root
                    api("POST", f"/session/{sid}/moveto", {"element": pe_root})
                    api("POST", f"/session/{sid}/doubleclick", {})
                    time.sleep(8)
                    
                    src3 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
                    with open("reports/brayan_pe_strat3.xml", "w", encoding="utf-8") as f:
                        f.write(src3)
                    print(f"  Source after root dblclk: {len(src3)} chars")
                    all3 = get_all_named(src3)
                    wins3 = [e for e in all3 if e["tag"] == "Window"]
                    print(f"  Windows: {len(wins3)}")
                    for w in wins3:
                        print(f"    name='{w['name']}' aid='{w['aid']}'")
                    tabs3 = [e for e in all3 if e["tag"] == "TabItem"]
                    print(f"  TabItems: {len(tabs3)}")
                    for t in tabs3:
                        print(f"    name='{t['name']}' aid='{t['aid']}'")
                    
                    # Check if form opened via new scoped session
                    print("\n  Re-creating scoped session...")
                    ds(scoped_sid)
                    frm2 = fe(sid, "accessibility id", "frmInicioComercial")
                    if frm2:
                        nwh2 = int(at(sid, frm2, "NativeWindowHandle"))
                        scoped2 = api("POST", "/session", {
                            "desiredCapabilities": {
                                "platformName": "Windows", "deviceName": "WindowsPC",
                                "appTopLevelWindow": hex(nwh2)
                            }
                        })
                        scoped_sid = scoped2.get("sessionId")
                        src4 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
                        with open("reports/brayan_pe_rescoped.xml", "w", encoding="utf-8") as f:
                            f.write(src4)
                        print(f"  Re-scoped source: {len(src4)} chars")
                        all4 = get_all_named(src4)
                        wins4 = [e for e in all4 if e["tag"] == "Window"]
                        tabs4 = [e for e in all4 if e["tag"] == "TabItem"]
                        print(f"  Windows: {len(wins4)}")
                        for w in wins4:
                            print(f"    name='{w['name']}' aid='{w['aid']}'")
                        print(f"  TabItems: {len(tabs4)}")
                        for t in tabs4:
                            print(f"    name='{t['name']}' aid='{t['aid']}'")
                        
                        # Also check for all new window-level elements via root
                        print("\n  Looking for new windows via Root...")
                        for aid_search in ["frmDocumentos", "frmDocumento", "frmPedido", 
                                           "frmSeleccion", "frmMovimientos", "frmListaDocumentos"]:
                            e_root = fe(sid, "accessibility id", aid_search)
                            if e_root:
                                print(f"    ROOT found: {aid_search} = '{at(sid, e_root, 'Name')}'")
                else:
                    print("  PE - PEDIDO not found in root XPath")
    
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
