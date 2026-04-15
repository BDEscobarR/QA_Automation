"""
Launch ERP, login, then inspect submenu items under 'Movimientos' and 'Procesos'.
"""
import json
import time
import subprocess
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

REMOTE_URL = "http://127.0.0.1:4723"
APP = r"C:\Users\BrayanEscobar\AppData\Local\BnetEmpresarial\current\ERP.Empresarial.exe"
USER = "brayan"
PASSWORD = "cafe123."

def api_call(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = Request(f"{REMOTE_URL}{path}", data=data, headers=headers, method=method)
    resp = urlopen(req, timeout=60)
    return json.loads(resp.read().decode("utf-8"))

def find_element(sid, strategy, value):
    r = api_call("POST", f"/session/{sid}/element", {"using": strategy, "value": value})
    val = r.get("value", {})
    return val.get("ELEMENT") or list(val.values())[0] if isinstance(val, dict) else val

def find_elements(sid, strategy, value):
    r = api_call("POST", f"/session/{sid}/elements", {"using": strategy, "value": value})
    results = []
    for item in r.get("value", []):
        if isinstance(item, dict):
            eid = item.get("ELEMENT") or list(item.values())[0]
            results.append(eid)
    return results

def get_element_attr(sid, eid, attr):
    r = api_call("GET", f"/session/{sid}/element/{eid}/attribute/{attr}")
    return r.get("value", "")

def click(sid, eid):
    api_call("POST", f"/session/{sid}/element/{eid}/click", {})

def get_page_source(sid):
    r = api_call("GET", f"/session/{sid}/source")
    return r.get("value", "")

def get_sessions():
    r = api_call("GET", "/sessions")
    sessions = r.get("value", [])
    return [s.get("id") for s in sessions] if sessions else []

def parse_tree_items(xml_str, parent_name=None):
    """Extract tree items from XML."""
    xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
    root = ET.fromstring(xml_str.encode("utf-8"))
    
    items = []
    for elem in root.iter():
        ctrl = elem.attrib.get("LocalizedControlType", "")
        name = elem.attrib.get("Name", "")
        auto_id = elem.attrib.get("AutomationId", "")
        if name and ("árbol" in ctrl.lower() or "tree" in ctrl.lower() or 
                     "elemento del" in ctrl.lower() or "treeitem" in ctrl.lower()):
            items.append({"name": name, "AutomationId": auto_id, "type": ctrl})
    return items

def main():
    # Kill existing ERP
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    
    # Launch ERP
    print("Launching ERP...")
    proc = subprocess.Popen([APP])
    print(f"  PID: {proc.pid}, waiting 20s...")
    time.sleep(20)
    
    # Create Root session
    r = api_call("POST", "/session", {
        "desiredCapabilities": {
            "platformName": "Windows",
            "deviceName": "WindowsPC",
            "app": "Root"
        }
    })
    sid = r["sessionId"]
    print(f"Root session: {sid}")

    try:
        # Wait for login form
        print("Waiting for login form...")
        for i in range(30):
            try:
                find_element(sid, "accessibility id", "txtUser")
                print(f"  Login form ready after {i+1}s")
                break
            except:
                time.sleep(1)
        
        # Login
        print("Logging in...")
        txt_user = find_element(sid, "accessibility id", "txtUser")
        api_call("POST", f"/session/{sid}/element/{txt_user}/clear", {})
        api_call("POST", f"/session/{sid}/element/{txt_user}/value", {"value": list(USER)})
        
        txt_pass = find_element(sid, "accessibility id", "txtPassw")
        api_call("POST", f"/session/{sid}/element/{txt_pass}/clear", {})
        api_call("POST", f"/session/{sid}/element/{txt_pass}/value", {"value": list(PASSWORD)})
        
        btn_ok = find_element(sid, "accessibility id", "btnOK")
        click(sid, btn_ok)
        
        # Wait for main interface
        print("Waiting for main interface...")
        for i in range(30):
            try:
                find_element(sid, "accessibility id", "frmInicioComercial")
                print(f"  Main interface ready after {i+1}s")
                break
            except:
                time.sleep(1)
        time.sleep(3)
        # Find the tree items in the accordion menu
        print("\n=== ACCORDION TREE ITEMS ===")
        tree_items = find_elements(sid, "xpath", "//TreeItem")
        print(f"Found {len(tree_items)} tree items")
        
        for ti in tree_items:
            name = get_element_attr(sid, ti, "Name")
            print(f"  TreeItem: '{name}'")
        
        # Click on "Movimientos" to expand it
        print("\n=== EXPANDING 'Movimientos' ===")
        movimientos = None
        for ti in tree_items:
            name = get_element_attr(sid, ti, "Name")
            if "Movimientos" in name:
                movimientos = ti
                break
        
        if movimientos:
            click(sid, movimientos)
            time.sleep(2)
            
            # Get updated tree items
            new_tree_items = find_elements(sid, "xpath", "//TreeItem")
            print(f"Tree items after expanding Movimientos: {len(new_tree_items)}")
            for ti in new_tree_items:
                name = get_element_attr(sid, ti, "Name")
                print(f"  TreeItem: '{name}'")
        else:
            print("  'Movimientos' not found!")
        
        # Also get page source to see the full structure
        print("\n=== SAVING EXPANDED STATE ===")
        xml = get_page_source(sid)
        with open("reports/expanded_movimientos.json", "w", encoding="utf-8") as f:
            json.dump({"source": xml}, f)
        
        # Click on "Procesos" to see its items too
        print("\n=== EXPANDING 'Procesos' ===")
        # First collapse Movimientos by clicking somewhere else, then click Procesos
        tree_items2 = find_elements(sid, "xpath", "//TreeItem")
        procesos = None
        for ti in tree_items2:
            name = get_element_attr(sid, ti, "Name")
            if "Procesos" in name:
                procesos = ti
                break
        
        if procesos:
            click(sid, procesos)
            time.sleep(2)
            
            tree_items3 = find_elements(sid, "xpath", "//TreeItem")
            print(f"Tree items after expanding Procesos: {len(tree_items3)}")
            for ti in tree_items3:
                name = get_element_attr(sid, ti, "Name")
                print(f"  TreeItem: '{name}'")
            
            # Save this state too
            xml2 = get_page_source(sid)
            with open("reports/expanded_procesos.json", "w", encoding="utf-8") as f:
                json.dump({"source": xml2}, f)
        else:
            print("  'Procesos' not found!")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            api_call("DELETE", f"/session/{sid}")
        except:
            pass
        subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)

if __name__ == "__main__":
    main()
