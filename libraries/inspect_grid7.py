"""
Find the + button specifically within the ERP form frmFaVentaR.
Use scoped session to the form window.
"""
import json, time, subprocess
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
        if "error" in val: return None
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

def src(sid):
    return api("GET", f"/session/{sid}/source").get("value", "")

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)

    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]
    scoped_sid = None
    form_sid = None

    try:
        # LOGIN + NAVIGATE
        wait_find(sid, "accessibility id", "txtUser")
        u = fe(sid, "accessibility id", "txtUser"); cl(sid, u); ky(sid, u, "brayan")
        p = fe(sid, "accessibility id", "txtPassw"); cl(sid, p); ky(sid, p, "cafe123.")
        clk(sid, fe(sid, "accessibility id", "btnOK"))
        frm = wait_find(sid, "accessibility id", "frmInicioComercial", 30)
        print("Login OK"); time.sleep(5)
        nwh = int(at(sid, frm, "NativeWindowHandle"))
        scoped_sid = api("POST", "/session", {
            "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": hex(nwh)}
        }).get("sessionId")
        mov = fe(sid, "name", "Movimientos"); clk(sid, mov); time.sleep(4)
        pe = fe(scoped_sid, "xpath", "//TreeItem[@Name='PE - PEDIDO']"); clk(scoped_sid, pe); time.sleep(3)
        pe02 = fe(scoped_sid, "name", "PE02 - PEDIDO"); clk(scoped_sid, pe02); time.sleep(8)
        print("Formulario PE02 abierto")

        # Create scoped session to the form window frmFaVentaR
        form_el = fe(sid, "accessibility id", "frmFaVentaR")
        form_nwh = int(at(sid, form_el, "NativeWindowHandle"))
        form_sid = api("POST", "/session", {
            "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": hex(form_nwh)}
        }).get("sessionId")
        print(f"Form session created: {form_sid}")

        # Get page source of the form to find the + button
        page = src(form_sid)
        print(f"Form page source length: {len(page)}")
        
        # Save to file for analysis
        with open("reports/form_source.xml", "w", encoding="utf-8") as f:
            f.write(page)
        print("Saved form source to reports/form_source.xml")
        
        # Search for the + button area in the XML
        # Look for keywords: Agregar, +, Add, green, plus
        import re
        # Find all elements with Name containing Agregar, +, Quitar, Limpiar, etc
        for pattern in ["Agregar", "Quitar", "Limpiar", "Excel", "\\+", "Add"]:
            matches = re.findall(rf'Name="[^"]*{pattern}[^"]*"', page, re.IGNORECASE)
            for m in matches:
                print(f"  Found: {m}")
        
        # Also find buttons in form
        print("\n=== Buttons in form session ===")
        btns = fes(form_sid, "xpath", "//Button")
        for b in btns:
            name = at(form_sid, b, "Name")
            aid = at(form_sid, b, "AutomationId")
            bbox = at(form_sid, b, "BoundingRectangle")
            enabled = at(form_sid, b, "IsEnabled")
            cls = at(form_sid, b, "ClassName")
            print(f"  name='{name}' aid='{aid}' class='{cls}' enabled='{enabled}' bbox='{bbox}'")
        
        # ToolBar items
        print("\n=== ToolBar items in form ===")
        tbs = fes(form_sid, "xpath", "//ToolBar")
        for tb in tbs:
            name = at(form_sid, tb, "Name")
            aid = at(form_sid, tb, "AutomationId")
            print(f"  ToolBar: name='{name}' aid='{aid}'")
            # Children of ToolBar
            children = fes(form_sid, "xpath", f"//ToolBar[@Name='{name}']/*")
            for ch in children:
                cname = at(form_sid, ch, "Name")
                caid = at(form_sid, ch, "AutomationId")
                ctype = at(form_sid, ch, "LocalizedControlType")
                print(f"    child: name='{cname}' aid='{caid}' type='{ctype}'")

        # Pane elements (the bottom panel with +, -, etc)
        print("\n=== Pane elements near grid ===")
        panes = fes(form_sid, "xpath", "//Pane")
        for p in panes[:20]:
            name = at(form_sid, p, "Name")
            aid = at(form_sid, p, "AutomationId")
            cls = at(form_sid, p, "ClassName")
            if aid:
                print(f"  Pane: name='{name}' aid='{aid}' class='{cls}'")

        # Images
        print("\n=== Images in form ===")
        imgs = fes(form_sid, "xpath", "//Image")
        for img in imgs:
            name = at(form_sid, img, "Name")
            aid = at(form_sid, img, "AutomationId")
            bbox = at(form_sid, img, "BoundingRectangle")
            print(f"  Image: name='{name}' aid='{aid}' bbox='{bbox}'")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        if form_sid: ds(form_sid)
        ds(sid)
        if scoped_sid: ds(scoped_sid)
        subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
        print("\nDone.")

if __name__ == "__main__":
    main()
