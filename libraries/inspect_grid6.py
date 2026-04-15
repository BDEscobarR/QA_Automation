"""
Find the green "+" button to add rows, then enter 3 articles.
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

def main():
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([APP]); time.sleep(20)

    sid = api("POST", "/session", {
        "desiredCapabilities": {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
    })["sessionId"]
    scoped_sid = None

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

        # Enter client
        txt_cl = fe(sid, "accessibility id", "txtCliente")
        cl(sid, txt_cl); ky(sid, txt_cl, "100723"); ky(sid, txt_cl, ["\ue004"]); time.sleep(5)
        print(f"Vendedor: '{at(sid, fe(sid, 'accessibility id', 'cboVendedor'), 'Name')}'")

        # === FIND THE GREEN + BUTTON ===
        print("\n=== SEARCHING FOR + BUTTON ===")
        
        # Search by name patterns
        for name in ["Agregar", "+", "Añadir", "Add", "Nuevo", "New"]:
            e = fe(sid, "name", name)
            if e:
                print(f"  Found name='{name}': aid='{at(sid, e, 'AutomationId')}' class='{at(sid, e, 'ClassName')}' enabled='{at(sid, e, 'IsEnabled')}' bbox='{at(sid, e, 'BoundingRectangle')}'")
        
        # Search all buttons
        print("\n  All Buttons in form:")
        buttons = fes(sid, "xpath", "//Button")
        for b in buttons:
            name = at(sid, b, "Name")
            aid = at(sid, b, "AutomationId")
            bbox = at(sid, b, "BoundingRectangle")
            enabled = at(sid, b, "IsEnabled")
            print(f"    name='{name}' aid='{aid}' enabled='{enabled}' bbox='{bbox}'")
        
        # Search ToolBar buttons (common in WinForms grids)
        print("\n  ToolBar items:")
        tbs = fes(sid, "xpath", "//ToolBar//Button")
        for tb in tbs:
            name = at(sid, tb, "Name")
            aid = at(sid, tb, "AutomationId")
            print(f"    name='{name}' aid='{aid}'")
        
        # Search all elements near the grid bottom area
        # The grid navigator often has buttons
        print("\n  Looking for navigator/panel near grid:")
        for pattern in ["pnl", "nav", "bar", "tool", "btn"]:
            elements = fes(sid, "xpath", f"//*[contains(@AutomationId,'{pattern}')]")
            for el in elements:
                name = at(sid, el, "Name")
                aid = at(sid, el, "AutomationId")
                cls = at(sid, el, "ClassName")
                if aid and name:
                    print(f"    name='{name}' aid='{aid}' class='{cls}'")

        # Search Images/Icons (the + might be an image button)
        print("\n  Image elements:")
        imgs = fes(sid, "xpath", "//Image")
        for img in imgs[:15]:
            name = at(sid, img, "Name")
            aid = at(sid, img, "AutomationId")
            bbox = at(sid, img, "BoundingRectangle")
            print(f"    name='{name}' aid='{aid}' bbox='{bbox}'")

        # Check all clickable elements near the grid
        print("\n  All elements with 'Agregar' or '+' text:")
        plus_els = fes(sid, "xpath", "//*[contains(@Name,'Agregar') or contains(@Name,'+') or contains(@Name,'gregar')]")
        for p in plus_els:
            name = at(sid, p, "Name")
            aid = at(sid, p, "AutomationId")
            cls = at(sid, p, "ClassName")
            ctype = at(sid, p, "LocalizedControlType")
            bbox = at(sid, p, "BoundingRectangle")
            print(f"    name='{name}' aid='{aid}' class='{cls}' type='{ctype}' bbox='{bbox}'")

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
