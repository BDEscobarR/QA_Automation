"""
Login → Movimientos → PE-PEDIDO (expand) → PE02-PEDIDO (click to open form) → Inspect form.
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
    return [e.get("ELEMENT") or list(e.values())[0] for e in val if isinstance(e, dict)]

def at(sid, eid, n):
    return api("GET", f"/session/{sid}/element/{eid}/attribute/{n}").get("value", "")

def clk(sid, eid): api("POST", f"/session/{sid}/element/{eid}/click", {})
def ky(sid, eid, t): api("POST", f"/session/{sid}/element/{eid}/value", {"value": list(t)})
def cl(sid, eid): api("POST", f"/session/{sid}/element/{eid}/clear", {})
def ds(sid):
    try: api("DELETE", f"/session/{sid}")
    except: pass

def wait_find(sid, s, v, t=30):
    for _ in range(t):
        e = fe(sid, s, v)
        if e: return e
        time.sleep(1)
    return None

def get_tree_names(xml_str):
    xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
    root = ET.fromstring(xml_str.encode("utf-8"))
    items = []
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "TreeItem":
            items.append(elem.attrib.get("Name", ""))
    return items

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
        scoped_sid = api("POST", "/session", {
            "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": hex(nwh)}
        }).get("sessionId")

        # 1) Expand Movimientos
        print("\n=== 1. Click Movimientos ===")
        mov = fe(sid, "name", "Movimientos")
        clk(sid, mov); time.sleep(4)
        tree1 = get_tree_names(api("GET", f"/session/{scoped_sid}/source").get("value", ""))
        print(f"Tree ({len(tree1)}): {tree1}")

        # 2) Click PE - PEDIDO to expand it
        print("\n=== 2. Click PE - PEDIDO (expand) ===")
        pe = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']")
        if not pe: print("PE - PEDIDO not found!"); return
        clk(scoped_sid, pe); time.sleep(4)

        src2 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        tree2 = get_tree_names(src2)
        new_in_tree = [t for t in tree2 if t not in tree1]
        print(f"Tree ({len(tree2)}): new items = {new_in_tree}")
        print(f"Full tree: {tree2}")

        # 3) Search for PE02 child
        print("\n=== 3. Looking for PE02 ===")
        pe02_names = ["PE02-PEDIDO", "PE02 - PEDIDO", "PE02", "PE-02", "PE02-Pedido",
                       "PE02 PEDIDO", "PE02- PEDIDO", "PE02 -PEDIDO"]
        pe02 = None
        for name in pe02_names:
            pe02 = fe(scoped_sid, "name", name)
            if pe02:
                print(f"  FOUND by name: '{name}'")
                break
        
        if not pe02:
            # Search by xpath partial match
            pe02 = fe(scoped_sid, "xpath", "//TreeItem[contains(@Name,'PE02')]")
            if pe02:
                print(f"  FOUND by xpath contains PE02: '{at(scoped_sid, pe02, 'Name')}'")
        
        if not pe02:
            # List all TreeItems to find it
            print("  Not found. All TreeItems:")
            items = fes(scoped_sid, "xpath", "//TreeItem")
            for eid in items:
                n = at(scoped_sid, eid, "Name")
                print(f"    '{n}'")
                if "PE02" in n.upper() or "PEDIDO" in n.upper() and n != "PE - PEDIDO":
                    pe02 = eid
                    print(f"    >>> Match!")
        
        if not pe02:
            print("  PE02 not found as TreeItem. Checking ListItems...")
            for xpath in ["//ListItem", "//DataItem", "//Custom", "//Button"]:
                items = fes(scoped_sid, "xpath", xpath)
                if items:
                    print(f"  {xpath}: {len(items)} found")
                    for eid in items[:15]:
                        n = at(scoped_sid, eid, "Name")
                        a = at(scoped_sid, eid, "AutomationId")
                        if n: print(f"    name='{n}' aid='{a}'")
            
            # Save full XML for analysis
            with open("reports/brayan_pe_expanded.xml", "w", encoding="utf-8") as f:
                f.write(src2)
            print(f"\n  Saved XML: {len(src2)} chars")
            return

        # 4) Click PE02 to open the document form
        print(f"\n=== 4. Clicking PE02: '{at(scoped_sid, pe02, 'Name')}' ===")
        clk(scoped_sid, pe02)
        time.sleep(8)

        # 5) Inspect the form
        print("\n=== 5. INSPECTING DOCUMENT FORM ===")
        # Re-create scoped session for fresh state
        ds(scoped_sid)
        frm2 = fe(sid, "accessibility id", "frmInicioComercial")
        nwh2 = int(at(sid, frm2, "NativeWindowHandle"))
        scoped_sid = api("POST", "/session", {
            "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": hex(nwh2)}
        }).get("sessionId")

        src3 = api("GET", f"/session/{scoped_sid}/source").get("value", "")
        with open("reports/brayan_pe02_form.xml", "w", encoding="utf-8") as f:
            f.write(src3)
        print(f"Form source: {len(src3)} chars")

        all_elems = get_all_named(src3)

        print("\nWindows:")
        for el in all_elems:
            if el["tag"] == "Window":
                print(f"  name='{el['name']}' aid='{el['aid']}'")

        print("\nTabItems:")
        for el in all_elems:
            if el["tag"] == "TabItem":
                print(f"  name='{el['name']}' aid='{el['aid']}'")

        print("\nEdit fields:")
        for el in all_elems:
            if el["tag"] == "Edit":
                print(f"  name='{el['name']}' aid='{el['aid']}' class='{el['class']}'")

        print("\nComboBoxes:")
        for el in all_elems:
            if el["tag"] == "ComboBox":
                print(f"  name='{el['name']}' aid='{el['aid']}'")

        print("\nButtons:")
        skip = {"Minimizar", "Restaurar", "Cerrar", "Columna a la izquierda",
                "Columna a la derecha", "Página a la derecha", "Página a la izquierda"}
        for el in all_elems:
            if el["tag"] == "Button" and el["name"] not in skip:
                print(f"  name='{el['name']}' aid='{el['aid']}'")

        print("\nDataGrids/Tables:")
        for el in all_elems:
            if el["tag"] in ["DataGrid", "Table", "DataItem"]:
                print(f"  <{el['tag']}> name='{el['name']}' aid='{el['aid']}' class='{el['class']}'")

        print("\nToolBars:")
        for el in all_elems:
            if el["tag"] == "ToolBar":
                print(f"  name='{el['name']}' aid='{el['aid']}'")

        print("\nCustom controls:")
        for el in all_elems:
            if el["tag"] == "Custom":
                print(f"  name='{el['name']}' aid='{el['aid']}' class='{el['class']}'")

        print("\nPanes with AutomationId:")
        for el in all_elems:
            if el["tag"] == "Pane" and el["aid"]:
                print(f"  name='{el['name']}' aid='{el['aid']}'")

        print("\nTexts with AutomationId:")
        for el in all_elems:
            if el["tag"] == "Text" and el["aid"]:
                print(f"  name='{el['name']}' aid='{el['aid']}'")

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
