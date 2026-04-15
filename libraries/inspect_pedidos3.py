"""
Step 2: After login, navigate to PE - PEDIDO and inspect the document list + PE02 form.
Scoped session sees TreeItems. Click PE - PEDIDO via scoped session, then inspect form.
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

def dump_xml_elements(xml_str, label=""):
    """Parse XML source and print all named elements"""
    xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
    root = ET.fromstring(xml_str.encode("utf-8"))
    print(f"\n--- {label} ({len(xml_str)} chars) ---")
    count = 0
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        name = elem.attrib.get("Name", "")
        aid = elem.attrib.get("AutomationId", "")
        cls = elem.attrib.get("ClassName", "")
        if name or aid:
            print(f"  <{tag}> Name='{name}' aid='{aid}' class='{cls}'")
            count += 1
    print(f"  Total named elements: {count}")

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)
    
    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]
    print(f"Root session: {sid}")
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
        print(f"Scoped session: {scoped_sid}")
        
        # CLICK MOVIMIENTOS (from root session since it found it before)
        print("\n=== Clicking Movimientos ===")
        mov = fe(sid, "name", "Movimientos")
        if not mov: print("Movimientos not found"); return
        clk(sid, mov)
        time.sleep(3)
        
        # VERIFY PE - PEDIDO IS VISIBLE IN SCOPED SESSION
        pe = fe(scoped_sid, "name", "PE - PEDIDO")
        if pe:
            print(f"PE - PEDIDO found in scoped session!")
            print(f"  class='{at(scoped_sid, pe, 'ClassName')}' aid='{at(scoped_sid, pe, 'AutomationId')}'")
        else:
            print("PE - PEDIDO not found in scoped")
            # Try root
            pe = fe(sid, "name", "PE - PEDIDO")
            if pe: print("PE - PEDIDO found in ROOT session")
        
        if not pe:
            print("ERROR: PE - PEDIDO not found anywhere"); return
        
        # CLICK PE - PEDIDO  
        print("\n=== Clicking PE - PEDIDO ===")
        # Use whichever session found it
        pe_sid = scoped_sid if fe(scoped_sid, "name", "PE - PEDIDO") else sid
        pe = fe(pe_sid, "name", "PE - PEDIDO")
        clk(pe_sid, pe)
        time.sleep(5)
        
        # CHECK WHAT APPEARED - new window/form?
        print("\n=== After clicking PE - PEDIDO ===")
        
        # Check for new forms
        form_ids = ["frmDocumentos", "frmPedido", "frmPedidos", "frmMovimiento",
                     "frmSeleccion", "frmBuscar", "frmDocumento", "frmSeleccionDocumento",
                     "gridControl", "GridControl"]
        for fid in form_ids:
            e = fe(sid, "accessibility id", fid)
            if e:
                print(f"  ROOT - Found form: '{fid}' name='{at(sid, e, 'Name')}' class='{at(sid, e, 'ClassName')}'")
            e2 = fe(scoped_sid, "accessibility id", fid)
            if e2:
                print(f"  SCOPED - Found form: '{fid}' name='{at(scoped_sid, e2, 'Name')}' class='{at(scoped_sid, e2, 'ClassName')}'")
        
        # Get scoped source to see everything
        src = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        if src:
            with open("reports/brayan_after_pe_click.xml", "w", encoding="utf-8") as f:
                f.write(src)
            dump_xml_elements(src, "After PE-PEDIDO click")
        
        # Search for PE02 or document-related items
        print("\n=== Searching for PE02 and document elements ===")
        for name in ["PE02", "PE-02", "PE 02", "pe02", "Documento", "Tipo Documento"]:
            e = fe(scoped_sid, "name", name)
            if e:
                print(f"  SCOPED FOUND: '{name}' aid='{at(scoped_sid, e, 'AutomationId')}' class='{at(scoped_sid, e, 'ClassName')}'")
            e2 = fe(sid, "name", name)
            if e2:
                print(f"  ROOT FOUND: '{name}' aid='{at(sid, e2, 'AutomationId')}' class='{at(sid, e2, 'ClassName')}'")
        
        # Check for grids/tables/datagrid that might show document list
        print("\n=== Grid/Table elements ===")
        for xpath in ["//DataGrid", "//Table", "//Custom[@ClassName='GridControl']",
                       "//Pane[contains(@AutomationId,'grid')]", "//Pane[contains(@AutomationId,'Grid')]"]:
            els = fes(scoped_sid, "xpath", xpath)
            if els:
                print(f"  {xpath}: {len(els)} found")
                for i, eid in enumerate(els[:5]):
                    print(f"    [{i}] name='{at(scoped_sid, eid, 'Name')}' aid='{at(scoped_sid, eid, 'AutomationId')}' class='{at(scoped_sid, eid, 'ClassName')}'")

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
