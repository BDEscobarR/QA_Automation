"""
1. Enter client 100723 properly
2. Check if Agregar button becomes enabled
3. Use Agregar to add rows and enter 3 articles
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

def list_art_filas(sid):
    arts = fes(sid, "xpath", "//DataItem[starts-with(@Name,'Artículo Fila')]")
    names = [at(sid, a, "Name") for a in arts]
    print(f"  Artículo rows ({len(names)}): {names}")
    return len(names)

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

        # === CHECK AGREGAR BEFORE CLIENT ===
        print("\n=== BEFORE CLIENT ===")
        agregar = fe(sid, "name", "Agregar")
        if agregar:
            print(f"Agregar enabled: {at(sid, agregar, 'IsEnabled')}")
            print(f"Agregar bbox: {at(sid, agregar, 'BoundingRectangle')}")
            print(f"Agregar aid: {at(sid, agregar, 'AutomationId')}")
            print(f"Agregar class: {at(sid, agregar, 'ClassName')}")

        # === ENTER CLIENT 100723 ===
        print("\n=== ENTERING CLIENT ===")
        txt_cl = fe(sid, "accessibility id", "txtCliente")
        cl(sid, txt_cl)
        ky(sid, txt_cl, "100723")
        print("Typed 100723, pressing Tab...")
        ky(sid, txt_cl, ["\ue004"])
        time.sleep(5)
        
        vend = fe(sid, "accessibility id", "cboVendedor")
        vname = at(sid, vend, "Name") if vend else "N/A"
        print(f"Vendedor: '{vname}'")
        
        # === CHECK AGREGAR AFTER CLIENT ===
        print("\n=== AFTER CLIENT ===")
        agregar2 = fe(sid, "name", "Agregar")
        if agregar2:
            enabled = at(sid, agregar2, "IsEnabled")
            print(f"Agregar enabled: {enabled}")
        
        list_art_filas(sid)

        # === TRY ENTERING ARTICLE 1 IN EXISTING ROW ===
        print("\n=== ARTICLE 1: 000001 ===")
        art0 = fe(sid, "name", "Artículo Fila 0")
        if art0:
            clk(sid, art0); time.sleep(1)
            ky(sid, art0, "000001")
            ky(sid, art0, ["\ue004"])
            time.sleep(4)
            
            cant0 = fe(sid, "name", "Cant. Fila 0, Sin orden.")
            if cant0:
                clk(sid, cant0); time.sleep(1)
                ky(sid, cant0, "1")
                ky(sid, cant0, ["\ue004"])
                time.sleep(3)
            
            print("After article 1:")
            list_art_filas(sid)
            
            # Check Agregar again
            agregar3 = fe(sid, "name", "Agregar")
            if agregar3:
                print(f"Agregar enabled: {at(sid, agregar3, 'IsEnabled')}")

        # === CLICK AGREGAR TO ADD ROW 2 ===
        print("\n=== CLICKING AGREGAR FOR ROW 2 ===")
        agregar4 = fe(sid, "name", "Agregar")
        if agregar4:
            clk(sid, agregar4)
            time.sleep(3)
            print("After Agregar click:")
            list_art_filas(sid)
            
            # Enter article 2
            art1 = fe(sid, "name", "Artículo Fila 1")
            if not art1:
                # Maybe it added a new empty row at a different index
                # Check all rows
                for i in range(5):
                    a = fe(sid, "name", f"Artículo Fila {i}")
                    if a:
                        print(f"  Found Artículo Fila {i}")
                # Try the last available empty row
                art_last = None
                for i in range(10, -1, -1):
                    art_last = fe(sid, "name", f"Artículo Fila {i}")
                    if art_last:
                        print(f"  Using last row: Artículo Fila {i}")
                        break
                art1 = art_last
            
            if art1:
                print("\n=== ARTICLE 2: 000002 ===")
                clk(sid, art1); time.sleep(1)
                ky(sid, art1, "000002")
                ky(sid, art1, ["\ue004"])
                time.sleep(4)
                
                # Find Cant cell for this row
                # Get the Name to know which fila
                art1_name = at(sid, art1, "Name")
                fila_num = art1_name.replace("Artículo Fila ", "")
                cant1 = fe(sid, "name", f"Cant. Fila {fila_num}, Sin orden.")
                if cant1:
                    clk(sid, cant1); time.sleep(1)
                    ky(sid, cant1, "1")
                    ky(sid, cant1, ["\ue004"])
                    time.sleep(3)
                
                print("After article 2:")
                list_art_filas(sid)

        # === CLICK AGREGAR FOR ROW 3 ===
        print("\n=== CLICKING AGREGAR FOR ROW 3 ===")
        agregar5 = fe(sid, "name", "Agregar")
        if agregar5:
            clk(sid, agregar5)
            time.sleep(3)
            print("After Agregar click:")
            n = list_art_filas(sid)
            
            # Enter article 3 in last available row
            art2 = None
            for i in range(n-1, -1, -1):
                art2 = fe(sid, "name", f"Artículo Fila {i}")
                if art2:
                    # Check if it's empty
                    print(f"\n=== ARTICLE 3: 000003 in Fila {i} ===")
                    clk(sid, art2); time.sleep(1)
                    ky(sid, art2, "000003")
                    ky(sid, art2, ["\ue004"])
                    time.sleep(4)
                    
                    cant2 = fe(sid, "name", f"Cant. Fila {i}, Sin orden.")
                    if cant2:
                        clk(sid, cant2); time.sleep(1)
                        ky(sid, cant2, "1")
                        ky(sid, cant2, ["\ue004"])
                        time.sleep(3)
                    break
            
            print("\nAfter article 3:")
            list_art_filas(sid)

        # === FINAL STATE ===
        print("\n=== FINAL STATE ===")
        for aid in ["txtFilas", "txtVrSubtotal", "txtVrTotal"]:
            e = fe(sid, "accessibility id", aid)
            if e:
                print(f"  {aid}: '{at(sid, e, 'Name')}'")

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
