"""
Login with DBA admin credentials, expand Movimientos, discover sub-items.
"""
import json, time, subprocess, xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

REMOTE_URL = "http://127.0.0.1:4723"
APP = r"C:\Users\BrayanEscobar\AppData\Local\BnetEmpresarial\current\ERP.Empresarial.exe"
USER = "dba"
PASSWORD = "F]J8al7QEhklTCnne]oI"

def api(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body else None
    h = {"Content-Type": "application/json"} if data else {}
    req = Request(f"{REMOTE_URL}{path}", data=data, headers=h, method=method)
    return json.loads(urlopen(req, timeout=120).read().decode("utf-8"))

def fe(sid, s, v):
    r = api("POST", f"/session/{sid}/element", {"using": s, "value": v})
    val = r.get("value", {})
    return val.get("ELEMENT") or list(val.values())[0] if isinstance(val, dict) else val

def at(sid, eid, n):
    return api("GET", f"/session/{sid}/element/{eid}/attribute/{n}").get("value", "")

def clk(sid, eid): api("POST", f"/session/{sid}/element/{eid}/click", {})
def ky(sid, eid, t): api("POST", f"/session/{sid}/element/{eid}/value", {"value": list(t)})
def cl(sid, eid): api("POST", f"/session/{sid}/element/{eid}/clear", {})
def ds(sid):
    try: api("DELETE", f"/session/{sid}")
    except: pass

def get_tree_items(xml_str):
    xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
    root = ET.fromstring(xml_str.encode("utf-8"))
    items = []
    for e in root.iter():
        tag = e.tag.split("}")[-1] if "}" in e.tag else e.tag
        if tag == "TreeItem":
            name = e.attrib.get("Name", "")
            aid = e.attrib.get("AutomationId", "")
            items.append({"name": name, "id": aid})
    return items

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)
    
    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]

    try:
        for _ in range(30):
            try: fe(sid, "accessibility id", "txtUser"); break
            except: time.sleep(1)
        
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, USER)
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, PASSWORD)
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        
        for i in range(30):
            try: fe(sid, "accessibility id", "frmInicioComercial"); print(f"Ready {i+1}s"); break
            except: time.sleep(1)
        time.sleep(5)
        
        # Get scoped session for the ERP window
        frm = fe(sid, "accessibility id", "frmInicioComercial")
        nwh = int(at(sid, frm, "NativeWindowHandle"))
        clk(sid, frm)
        time.sleep(1)
        
        # First, check the initial tree items in the accordion
        print("\n=== INITIAL STATE ===")
        xml0 = api("GET", f"/session/{sid}/source").get("value", "")
        with open("reports/dba_initial.xml", "w", encoding="utf-8") as f:
            f.write(xml0)
        items0 = get_tree_items(xml0)
        erp_items = [i for i in items0 if not i["name"].startswith(".") and 
                     not i["name"].startswith("Chat") and
                     not i["name"].startswith("Equipo") and
                     not i["name"].startswith("Canal") and
                     "Edge" not in i["name"] and
                     len(i["name"]) < 40]
        print(f"ERP tree items: {len(erp_items)}")
        for it in erp_items:
            print(f"  '{it['name']}'")
        
        # Click on Movimientos to expand
        print("\n=== CLICKING MOVIMIENTOS ===")
        mov = fe(sid, "name", "Movimientos")
        clk(sid, mov)
        time.sleep(3)
        
        # Get page source again (using Root session since it captured the accordion before)
        # The element might need to be re-found after state change
        xml1 = api("GET", f"/session/{sid}/source").get("value", "")
        with open("reports/dba_after_mov.xml", "w", encoding="utf-8") as f:
            f.write(xml1)
        items1 = get_tree_items(xml1)
        erp_items1 = [i for i in items1 if not i["name"].startswith(".") and 
                      not i["name"].startswith("Chat") and
                      not i["name"].startswith("Equipo") and
                      not i["name"].startswith("Canal") and
                      "Edge" not in i["name"] and
                      len(i["name"]) < 40]
        print(f"ERP tree items after Movimientos click: {len(erp_items1)}")
        for it in erp_items1:
            print(f"  '{it['name']}'")
        
        # Check if there are NEW items
        old_names = set(i["name"] for i in erp_items)
        new_items = [i for i in erp_items1 if i["name"] not in old_names]
        print(f"\nNEW items after click: {len(new_items)}")
        for it in new_items:
            print(f"  '{it['name']}'")
        
        # Also try Procesos
        print("\n=== CLICKING PROCESOS ===")
        try:
            proc = fe(sid, "name", "Procesos")
            clk(sid, proc)
            time.sleep(3)
            
            xml2 = api("GET", f"/session/{sid}/source").get("value", "")
            items2 = get_tree_items(xml2)
            erp_items2 = [i for i in items2 if not i["name"].startswith(".") and 
                          not i["name"].startswith("Chat") and
                          not i["name"].startswith("Equipo") and
                          not i["name"].startswith("Canal") and
                          "Edge" not in i["name"] and
                          len(i["name"]) < 40]
            new_items2 = [i for i in erp_items2 if i["name"] not in old_names]
            print(f"NEW items after Procesos: {len(new_items2)}")
            for it in new_items2:
                print(f"  '{it['name']}'")
        except Exception as e:
            print(f"  Error: {e}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        ds(sid)
        subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)

if __name__ == "__main__":
    main()
