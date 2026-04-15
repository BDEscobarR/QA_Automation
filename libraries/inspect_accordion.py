"""
Use the accordion search box to find menu items, click on them to open forms,
and inspect the form elements.
"""
import json
import time
import subprocess
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

REMOTE_URL = "http://127.0.0.1:4723"
APP = r"C:\Users\BrayanEscobar\AppData\Local\BnetEmpresarial\current\ERP.Empresarial.exe"
USER = "brayan"
PASSWORD = "cafe123."

def api(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = Request(f"{REMOTE_URL}{path}", data=data, headers=headers, method=method)
    resp = urlopen(req, timeout=120)
    return json.loads(resp.read().decode("utf-8"))

def find_elem(sid, strategy, value):
    r = api("POST", f"/session/{sid}/element", {"using": strategy, "value": value})
    val = r.get("value", {})
    return val.get("ELEMENT") or list(val.values())[0] if isinstance(val, dict) else val

def find_elems(sid, strategy, value):
    r = api("POST", f"/session/{sid}/elements", {"using": strategy, "value": value})
    results = []
    for item in r.get("value", []):
        if isinstance(item, dict):
            eid = item.get("ELEMENT") or list(item.values())[0]
            results.append(eid)
    return results

def attr(sid, eid, name):
    r = api("GET", f"/session/{sid}/element/{eid}/attribute/{name}")
    return r.get("value", "")

def click(sid, eid):
    api("POST", f"/session/{sid}/element/{eid}/click", {})

def keys(sid, eid, text):
    api("POST", f"/session/{sid}/element/{eid}/value", {"value": list(text)})

def send_keyboard(sid, eid, special_keys):
    """Send special keys like arrows, enter, etc."""
    api("POST", f"/session/{sid}/element/{eid}/value", {"value": special_keys})

def clear(sid, eid):
    api("POST", f"/session/{sid}/element/{eid}/clear", {})

def delete_session(sid):
    try: api("DELETE", f"/session/{sid}")
    except: pass

def get_source_and_parse(sid):
    r = api("GET", f"/session/{sid}/source")
    xml_str = r.get("value", "")
    xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
    root = ET.fromstring(xml_str.encode("utf-8"))
    elements = []
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        auto_id = elem.attrib.get("AutomationId", "")
        name = elem.attrib.get("Name", "")
        cls = elem.attrib.get("ClassName", "")
        ctrl = elem.attrib.get("LocalizedControlType", "")
        elements.append({"tag": tag, "AutomationId": auto_id, "Name": name, "ClassName": cls, "ControlType": ctrl})
    return elements, xml_str

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    
    print("Launching ERP...")
    subprocess.Popen([APP])
    time.sleep(20)
    
    r = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })
    root_sid = r["sessionId"]
    
    try:
        # Login
        for i in range(30):
            try: find_elem(root_sid, "accessibility id", "txtUser"); break
            except: time.sleep(1)

        u = find_elem(root_sid, "accessibility id", "txtUser")
        clear(root_sid, u); keys(root_sid, u, USER)
        p = find_elem(root_sid, "accessibility id", "txtPassw")
        clear(root_sid, p); keys(root_sid, p, PASSWORD)
        click(root_sid, find_elem(root_sid, "accessibility id", "btnOK"))
        
        for i in range(30):
            try: find_elem(root_sid, "accessibility id", "frmInicioComercial"); print(f"Ready {i+1}s"); break
            except: time.sleep(1)
        time.sleep(3)

        # Create scoped session
        frm = find_elem(root_sid, "accessibility id", "frmInicioComercial")
        nwh = int(attr(root_sid, frm, "NativeWindowHandle"))
        r2 = api("POST", "/session", {
            "desiredCapabilities": {
                "platformName": "Windows", "deviceName": "WindowsPC",
                "appTopLevelWindow": hex(nwh)
            }
        })
        erp_sid = r2["sessionId"]
        print(f"Scoped session: {erp_sid}")
        
        # METHOD 1: Try to expand "Movimientos" using keyboard arrows
        print("\n=== METHOD 1: EXPAND MOVIMIENTOS WITH KEYBOARD ===")
        mov = find_elem(root_sid, "name", "Movimientos")
        click(root_sid, mov)
        time.sleep(1)
        # Send Right arrow to expand, using the Unicode for Right Arrow
        send_keyboard(root_sid, mov, ["\ue014"])  # Right arrow
        time.sleep(2)
        
        # Check for new items in scoped session 
        elems, xml = get_source_and_parse(erp_sid)
        tree_items = [e for e in elems if "árbol" in e["ControlType"] or "tree" in e["ControlType"].lower() or "TreeItem" in e["tag"]]
        print(f"Tree items after Right arrow: {len(tree_items)}")
        for ti in tree_items:
            print(f"  '{ti['Name']}' (AutomationId='{ti['AutomationId']}')")
        
        # METHOD 2: Use search/filter box
        print("\n=== METHOD 2: SEARCH BOX ===")
        search_terms = ["Pedido", "Remisi", "Factur", "Devolu", "Aprobar", "Venta", "Compras"]
        
        all_found = {}
        for term in search_terms:
            try:
                # Find and clear the search edit box
                search_edit = find_elem(root_sid, "accessibility id", "teSearch")
                click(root_sid, search_edit)
                time.sleep(0.5)
                
                # Use Ctrl+A to select all, then type new text
                send_keyboard(root_sid, search_edit, ["\ue009", "a", "\ue009"])  # Ctrl+A
                time.sleep(0.3)
                keys(root_sid, search_edit, term)
                time.sleep(2)
                
                # Now parse updated tree from scoped session
                elems2, _ = get_source_and_parse(erp_sid)
                tree_items2 = [e for e in elems2 if ("árbol" in e["ControlType"] or "tree" in e["ControlType"].lower() or "TreeItem" in e["tag"]) and e["Name"]]
                
                print(f"\n  Search '{term}': {len(tree_items2)} tree items")
                for ti in tree_items2:
                    print(f"    '{ti['Name']}'")
                    all_found[ti['Name']] = True
                    
            except Exception as e:
                print(f"  Search '{term}' error: {e}")
        
        # METHOD 3: Double-click to expand 
        print("\n=== METHOD 3: DOUBLE-CLICK EXPAND ===")
        try:
            # Clear search first
            search_edit = find_elem(root_sid, "accessibility id", "teSearch")
            click(root_sid, search_edit)
            time.sleep(0.3)
            send_keyboard(root_sid, search_edit, ["\ue009", "a", "\ue009"])  # Ctrl+A
            time.sleep(0.2)
            send_keyboard(root_sid, search_edit, ["\ue017"])  # Delete
            time.sleep(1)
            
            # Double-click Movimientos
            mov = find_elem(root_sid, "name", "Movimientos")
            click(root_sid, mov)
            time.sleep(0.3)
            click(root_sid, mov)
            time.sleep(2)
            
            # Check tree
            elems3, _ = get_source_and_parse(erp_sid)
            tree_items3 = [e for e in elems3 if ("árbol" in e["ControlType"] or "tree" in e["ControlType"].lower() or "TreeItem" in e["tag"]) and e["Name"]]
            
            print(f"Tree items after double-click: {len(tree_items3)}")
            for ti in tree_items3:
                print(f"  '{ti['Name']}'")
        except Exception as e:
            print(f"Error: {e}")
        
        # Save summary
        print(f"\n=== SUMMARY ===")
        print(f"All unique menu items found:")
        for name in sorted(all_found.keys()):
            print(f"  - {name}")
        
        delete_session(erp_sid)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        delete_session(root_sid)
        subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)

if __name__ == "__main__":
    main()
