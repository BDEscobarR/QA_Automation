"""
Launch ERP, login, get the ERP window handle, create a scoped session,
and then explore the accordion menu within that scoped session.
"""
import json
import time
import subprocess
from urllib.request import Request, urlopen

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

def clear(sid, eid):
    api("POST", f"/session/{sid}/element/{eid}/clear", {})

def delete_session(sid):
    try:
        api("DELETE", f"/session/{sid}")
    except:
        pass

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    
    print("Launching ERP...")
    proc = subprocess.Popen([APP])
    time.sleep(20)
    
    # Create Root session for login
    r = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })
    root_sid = r["sessionId"]
    print(f"Root session: {root_sid}")
    
    try:
        # Wait for login form 
        for i in range(30):
            try:
                find_elem(root_sid, "accessibility id", "txtUser")
                break
            except:
                time.sleep(1)
        
        # Login
        print("Logging in...")
        u = find_elem(root_sid, "accessibility id", "txtUser")
        clear(root_sid, u)
        keys(root_sid, u, USER)
        p = find_elem(root_sid, "accessibility id", "txtPassw")
        clear(root_sid, p)
        keys(root_sid, p, PASSWORD)
        click(root_sid, find_elem(root_sid, "accessibility id", "btnOK"))
        
        # Wait for main interface
        for i in range(30):
            try:
                find_elem(root_sid, "accessibility id", "frmInicioComercial")
                print(f"Main interface ready after {i+1}s")
                break
            except:
                time.sleep(1)
        time.sleep(3)
        
        # Get the window handle of frmInicioComercial
        frm_elem = find_elem(root_sid, "accessibility id", "frmInicioComercial")
        window_handle = hex(int(attr(root_sid, frm_elem, "NativeWindowHandle")))
        print(f"ERP window handle: {window_handle}")
        
        # Create a scoped session attached to this window
        r2 = api("POST", "/session", {
            "desiredCapabilities": {
                "platformName": "Windows",
                "deviceName": "WindowsPC",
                "appTopLevelWindow": window_handle
            }
        })
        erp_sid = r2["sessionId"]
        print(f"Scoped ERP session: {erp_sid}")
        
        # Now all searches are within the ERP window only!
        # Find ALL tree items in the accordion
        print("\n=== TREE ITEMS IN ERP ===")
        tree_items = find_elems(erp_sid, "xpath", "//TreeItem")
        print(f"Found {len(tree_items)} TreeItems")
        for ti in tree_items:
            name = attr(erp_sid, ti, "Name")
            auto_id = attr(erp_sid, ti, "AutomationId")
            print(f"  '{name}' (AutomationId='{auto_id}')")
        
        # Click on "Movimientos" to expand
        print("\n=== CLICK MOVIMIENTOS ===")
        mov = find_elem(erp_sid, "name", "Movimientos")
        click(erp_sid, mov)
        time.sleep(2)
        
        # Get tree items again after expanding
        print("\n=== TREE ITEMS AFTER EXPANDING MOVIMIENTOS ===")
        tree_items2 = find_elems(erp_sid, "xpath", "//TreeItem")
        print(f"Found {len(tree_items2)} TreeItems")
        for ti in tree_items2:
            name = attr(erp_sid, ti, "Name")
            auto_id = attr(erp_sid, ti, "AutomationId")
            print(f"  '{name}' (AutomationId='{auto_id}')")
        
        # If Movimientos didn't expand, maybe we need to expand it with double-click or special action
        if len(tree_items2) == len(tree_items):
            print("\n  Same count - trying double-click on Movimientos...")
            # Double-click
            click(erp_sid, mov)
            time.sleep(1)
            click(erp_sid, mov)
            time.sleep(2)
            
            tree_items3 = find_elems(erp_sid, "xpath", "//TreeItem")
            print(f"  Found {len(tree_items3)} TreeItems after double-click")
            for ti in tree_items3:
                name = attr(erp_sid, ti, "Name")
                print(f"    '{name}'")
        
        # Try using the search/filter  
        print("\n=== USING SEARCH BOX ===")
        try:
            search = find_elem(erp_sid, "accessibility id", "teSearch")
            click(erp_sid, search)
            time.sleep(0.5)
            
            for term in ["Pedido", "Remisi", "Factur", "Devolu", "Aprobar"]:
                try:
                    # Find the edit box
                    edit_boxes = find_elems(erp_sid, "xpath", "//Edit")
                    print(f"\n  Searching '{term}' (found {len(edit_boxes)} edit boxes)")
                    
                    if edit_boxes:
                        clear(erp_sid, edit_boxes[0])
                        keys(erp_sid, edit_boxes[0], term)
                        time.sleep(1.5)
                        
                        tree_items_filtered = find_elems(erp_sid, "xpath", "//TreeItem")
                        print(f"    TreeItems: {len(tree_items_filtered)}")
                        for ti in tree_items_filtered:
                            name = attr(erp_sid, ti, "Name")
                            print(f"      '{name}'")
                except Exception as e:
                    print(f"    Search '{term}' error: {e}")
        except Exception as e:
            print(f"  Search box error: {e}")
        
        # Clean up scoped session
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
