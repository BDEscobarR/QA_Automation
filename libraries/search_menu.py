"""
Minimal script: Login, activate ERP window, use search box to find menu items.
Uses the scoped session approach that already worked.
"""
import json
import time
import subprocess
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

REMOTE_URL = "http://127.0.0.1:4723"
APP = r"C:\Users\BrayanEscobar\AppData\Local\BnetEmpresarial\current\ERP.Empresarial.exe"

def api(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = Request(f"{REMOTE_URL}{path}", data=data, headers=headers, method=method)
    resp = urlopen(req, timeout=120)
    return json.loads(resp.read().decode("utf-8"))

def fe(sid, strat, val):
    r = api("POST", f"/session/{sid}/element", {"using": strat, "value": val})
    v = r.get("value", {})
    return v.get("ELEMENT") or list(v.values())[0] if isinstance(v, dict) else v

def at(sid, eid, name):
    return api("GET", f"/session/{sid}/element/{eid}/attribute/{name}").get("value", "")

def clk(sid, eid): api("POST", f"/session/{sid}/element/{eid}/click", {})
def ky(sid, eid, t): api("POST", f"/session/{sid}/element/{eid}/value", {"value": list(t)})
def cl(sid, eid): api("POST", f"/session/{sid}/element/{eid}/clear", {})
def ds(sid):
    try: api("DELETE", f"/session/{sid}")
    except: pass

def parse_source(sid):
    xml_str = api("GET", f"/session/{sid}/source").get("value", "")
    xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
    root = ET.fromstring(xml_str.encode("utf-8"))
    items = []
    for e in root.iter():
        tag = e.tag.split("}")[-1] if "}" in e.tag else e.tag
        items.append({
            "tag": tag, "id": e.attrib.get("AutomationId", ""),
            "name": e.attrib.get("Name", ""), "type": e.attrib.get("LocalizedControlType", ""),
            "cls": e.attrib.get("ClassName", "")
        })
    return items

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)
    
    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]

    try:
        # Login
        for _ in range(30):
            try: fe(sid, "accessibility id", "txtUser"); break
            except: time.sleep(1)
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, "brayan")
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, "cafe123.")
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        for i in range(30):
            try: fe(sid, "accessibility id", "frmInicioComercial"); print(f"Ready {i+1}s"); break
            except: time.sleep(1)
        time.sleep(5)
        
        # Activate the ERP window first by clicking inside it
        frm = fe(sid, "accessibility id", "frmInicioComercial")
        clk(sid, frm)
        time.sleep(1)
        
        # Get window handle and create scoped session
        nwh = int(at(sid, frm, "NativeWindowHandle"))
        erp = api("POST", "/session", {
            "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": hex(nwh)}
        })["sessionId"]
        print(f"Scoped: {erp}")
        
        # Use teSearch from SCOPED session
        print("\n=== SEARCH BOX TESTS ===")
        for term in ["Pedido", "Remision", "Factura", "Devolucion", "Aprobar", "Cotizacion", "Nota credito", "Compras", "Ventas"]:
            try:
                search = fe(erp, "accessibility id", "teSearch")
                cl(erp, search)
                ky(erp, search, term)
                time.sleep(2)
                
                # Parse page source to find tree items
                items = parse_source(erp)
                tree = [i for i in items if "TreeItem" in i["tag"] and i["name"]]
                
                print(f"\n  '{term}' -> {len(tree)} tree items:")
                for t in tree:
                    print(f"    [{t['type']}] '{t['name']}'")
                
                if not tree:
                    # Check for any new elements with names
                    named = [i for i in items if i["name"] and i["name"] not in [
                        "ERP.Empresarial", "MiStatusStrip1", "Inicio", "Live chat",
                        "MiLoadControl1", "Emision Documentos Elec.", "Se encontraron", 
                        "Sistema", "Minimizar", "Restaurar", "Cerrar", "MiLinea1",
                        "filtre aquí", ""
                    ]]
                    print(f"    Other named elements: {len(named)}")
                    for n in named[:10]:
                        print(f"      [{n['type']}] '{n['name']}' id='{n['id']}'")
                        
            except Exception as e:
                print(f"  '{term}' ERROR: {e}")
        
        ds(erp)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        ds(sid)
        subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)

if __name__ == "__main__":
    main()
