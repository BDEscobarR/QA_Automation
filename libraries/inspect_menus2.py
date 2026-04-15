"""
Launch ERP, login, navigate accordion menu using name-based locators.
Expand 'Movimientos' and 'Procesos' to discover sub-items.
"""
import json
import time
import subprocess
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

def get_attr(sid, eid, attr):
    r = api_call("GET", f"/session/{sid}/element/{eid}/attribute/{attr}")
    return r.get("value", "")

def get_text(sid, eid):
    r = api_call("GET", f"/session/{sid}/element/{eid}/text")
    return r.get("value", "")

def click(sid, eid):
    api_call("POST", f"/session/{sid}/element/{eid}/click", {})

def send_keys(sid, eid, text):
    api_call("POST", f"/session/{sid}/element/{eid}/value", {"value": list(text)})

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    
    print("Launching ERP...")
    proc = subprocess.Popen([APP])
    time.sleep(20)
    
    r = api_call("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })
    sid = r["sessionId"]
    print(f"Session: {sid}")

    try:
        # Wait for login
        for i in range(30):
            try:
                find_element(sid, "accessibility id", "txtUser")
                break
            except:
                time.sleep(1)
        
        # Login
        print("Logging in...")
        u = find_element(sid, "accessibility id", "txtUser")
        api_call("POST", f"/session/{sid}/element/{u}/clear", {})
        send_keys(sid, u, USER)
        p = find_element(sid, "accessibility id", "txtPassw")
        api_call("POST", f"/session/{sid}/element/{p}/clear", {})
        send_keys(sid, p, PASSWORD)
        click(sid, find_element(sid, "accessibility id", "btnOK"))
        
        # Wait for main interface
        for i in range(30):
            try:
                find_element(sid, "accessibility id", "frmInicioComercial")
                print(f"Main interface ready after {i+1}s")
                break
            except:
                time.sleep(1)
        time.sleep(3)
        
        # ==========================================
        # EXPLORE ACCORDION MENU BY NAME
        # ==========================================
        
        # The accordion menu has items: Configurar, Catálogos., Procesos, Herramientas, Movimientos, Informes, Conectores
        # These are accessible by name= locator
        
        menu_sections = ["Configurar", "Catálogos.", "Procesos", "Herramientas", "Movimientos", "Informes", "Conectores"]
        
        print("\n=== ACCORDION MENU SECTIONS ===")
        for section in menu_sections:
            try:
                elem = find_element(sid, "name", section)
                print(f"  FOUND: name='{section}'")
            except:
                print(f"  NOT FOUND: name='{section}'")
        
        # Click on "Movimientos" to expand
        print("\n=== EXPANDING MOVIMIENTOS ===")
        try:
            mov = find_element(sid, "name", "Movimientos")
            click(sid, mov)
            time.sleep(2)
            
            # After expanding, the sub-items should appear as new tree items
            # Let's try to find common sub-items by name
            sub_items_to_try = [
                "Pedidos", "Pedido", "Pedidos de Venta", "Crear Pedido",
                "Remisiones", "Remisión", "Crear Remisión",
                "Facturas", "Facturación", "Factura", "Crear Factura",
                "Devoluciones", "Devolución", "Crear Devolución",
                "Cotizaciones", "Cotización",
                "Notas Crédito", "Nota Crédito",
                "Compras", "Orden de Compra",
                "Entradas", "Salidas", "Traspasos",
                "Ventas", "Cuentas por Cobrar", "Cuentas por Pagar"
            ]
            
            print("  Searching for sub-items...")
            found_items = []
            for item_name in sub_items_to_try:
                try:
                    elem = find_element(sid, "name", item_name)
                    auto_id = get_attr(sid, elem, "AutomationId")
                    ctrl_type = get_attr(sid, elem, "LocalizedControlType")
                    cls = get_attr(sid, elem, "ClassName")
                    found_items.append(item_name)
                    print(f"    FOUND: name='{item_name}' AutomationId='{auto_id}' type='{ctrl_type}' class='{cls}'")
                except:
                    pass
            
            if not found_items:
                print("    No known sub-items found. Let's use the search box instead...")
            
            # Alternative: use the AccordionSearchControl to filter
            print("\n  Using search to find pedido-related items...")
            search_box = find_element(sid, "accessibility id", "teSearch")
            click(sid, search_box)
            time.sleep(0.5)
            
            # Find the edit box inside the search control
            try:
                edit = find_element(sid, "name", "filtre aquí")
                api_call("POST", f"/session/{sid}/element/{edit}/clear", {})
                send_keys(sid, edit, "pedido")
                time.sleep(2)
                
                # Now check what tree items are visible
                tree_items = find_elements(sid, "xpath", 
                    "//*[contains(@ClassName,'WindowsForms10')]//TreeItem")
                print(f"  TreeItems after search 'pedido': {len(tree_items)}")
                for ti in tree_items:
                    name = get_attr(sid, ti, "Name")
                    auto_id = get_attr(sid, ti, "AutomationId")
                    if name:
                        print(f"    '{name}' (AutomationId='{auto_id}')")
            except Exception as e:
                print(f"    Search box error: {e}")
            
            # Clear search and try other terms
            for search_term in ["remisi", "factur", "devolu"]:
                try:
                    edit = find_element(sid, "name", "filtre aquí")
                except:
                    edit = find_element(sid, "accessibility id", "teSearch")
                try:
                    # Clear by selecting all and deleting
                    api_call("POST", f"/session/{sid}/element/{edit}/clear", {})
                    send_keys(sid, edit, search_term)
                    time.sleep(2)
                    
                    tree_items = find_elements(sid, "xpath", 
                        "//*[contains(@ClassName,'WindowsForms10')]//TreeItem")
                    print(f"\n  TreeItems after search '{search_term}': {len(tree_items)}")
                    for ti in tree_items:
                        name = get_attr(sid, ti, "Name")
                        auto_id = get_attr(sid, ti, "AutomationId")
                        if name:
                            print(f"    '{name}' (AutomationId='{auto_id}')")
                except Exception as e:
                    print(f"    Search '{search_term}' error: {e}")
                    
        except Exception as e:
            print(f"ERROR expanding Movimientos: {e}")
            import traceback
            traceback.print_exc()

        # Also explore Procesos
        print("\n=== EXPLORING PROCESOS ===")
        try:
            # Clear search first
            try:
                edit = find_element(sid, "name", "filtre aquí")
                api_call("POST", f"/session/{sid}/element/{edit}/clear", {})
            except:
                pass
            time.sleep(1)
            
            # Search for "aprobar" 
            try:
                edit = find_element(sid, "name", "filtre aquí")
            except:
                edit = find_element(sid, "accessibility id", "teSearch")
            api_call("POST", f"/session/{sid}/element/{edit}/clear", {})
            send_keys(sid, edit, "aprobar")
            time.sleep(2)
            
            tree_items = find_elements(sid, "xpath", 
                "//*[contains(@ClassName,'WindowsForms10')]//TreeItem")
            print(f"  TreeItems after search 'aprobar': {len(tree_items)}")
            for ti in tree_items:
                name = get_attr(sid, ti, "Name")
                auto_id = get_attr(sid, ti, "AutomationId")
                if name:
                    print(f"    '{name}' (AutomationId='{auto_id}')")
        except Exception as e:
            print(f"ERROR exploring Procesos: {e}")

    except Exception as e:
        print(f"FATAL ERROR: {e}")
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
