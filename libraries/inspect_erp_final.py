"""
Launch ERP, login, create scoped session, dump AND parse the page source.
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

def click(sid, eid):
    api("POST", f"/session/{sid}/element/{eid}/click", {})

def keys(sid, eid, text):
    api("POST", f"/session/{sid}/element/{eid}/value", {"value": list(text)})

def clear(sid, eid):
    api("POST", f"/session/{sid}/element/{eid}/clear", {})

def attr(sid, eid, name):
    r = api("GET", f"/session/{sid}/element/{eid}/attribute/{name}")
    return r.get("value", "")

def delete_session(sid):
    try: api("DELETE", f"/session/{sid}")
    except: pass

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
        
        # Get window handle - try NativeWindowHandle
        frm = find_elem(root_sid, "accessibility id", "frmInicioComercial")
        nwh = attr(root_sid, frm, "NativeWindowHandle")
        print(f"NativeWindowHandle raw: {nwh}")
        
        # Convert to hex string for appTopLevelWindow
        handle_hex = hex(int(nwh))
        print(f"Hex handle: {handle_hex}")
        
        # Create scoped session
        r2 = api("POST", "/session", {
            "desiredCapabilities": {
                "platformName": "Windows",
                "deviceName": "WindowsPC",
                "appTopLevelWindow": handle_hex
            }
        })
        erp_sid = r2["sessionId"]
        print(f"Scoped session: {erp_sid}")
        
        # Get page source from scoped session
        print("Getting page source from scoped session...")
        source_resp = api("GET", f"/session/{erp_sid}/source")
        xml_str = source_resp.get("value", "")
        
        # Save raw
        with open("reports/erp_scoped_source.xml", "w", encoding="utf-8") as f:
            f.write(xml_str)
        print(f"Saved to reports/erp_scoped_source.xml ({len(xml_str)} chars)")
        
        # Parse and list all elements
        xml_str2 = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
        root = ET.fromstring(xml_str2.encode("utf-8"))
        
        print("\n=== ALL ELEMENTS IN ERP WINDOW ===")
        count = 0
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            auto_id = elem.attrib.get("AutomationId", "")
            name = elem.attrib.get("Name", "")
            cls = elem.attrib.get("ClassName", "")
            ctrl = elem.attrib.get("LocalizedControlType", "")
            if auto_id or name:
                count += 1
                print(f"  [{ctrl}|{tag}] AutomationId='{auto_id}' Name='{name[:60]}' Class='{cls}'")
        
        print(f"\nTotal elements: {count}")
        
        # Now try clicking Movimientos using the Root session
        # (since scoped session may not have the tree items)
        print("\n=== CLICKING MOVIMIENTOS VIA ROOT SESSION ===")
        mov = find_elem(root_sid, "name", "Movimientos")
        print(f"  Found Movimientos element")
        click(root_sid, mov)
        time.sleep(3)
        
        # Get page source again from scoped session
        print("Getting updated page source...")
        source_resp2 = api("GET", f"/session/{erp_sid}/source")
        xml_str3 = source_resp2.get("value", "")
        
        with open("reports/erp_after_movimientos.xml", "w", encoding="utf-8") as f:
            f.write(xml_str3)
        print(f"Saved after Movimientos ({len(xml_str3)} chars)")
        
        # Parse and show new elements
        xml_str4 = xml_str3.replace('encoding="utf-16"', 'encoding="utf-8"')
        root2 = ET.fromstring(xml_str4.encode("utf-8"))
        
        print("\n=== ELEMENTS AFTER CLICKING MOVIMIENTOS ===")
        for elem in root2.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            auto_id = elem.attrib.get("AutomationId", "")
            name = elem.attrib.get("Name", "")
            ctrl = elem.attrib.get("LocalizedControlType", "")
            if auto_id or name:
                print(f"  [{ctrl}|{tag}] AutomationId='{auto_id}' Name='{name[:80]}'")
        
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
