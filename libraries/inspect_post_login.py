"""
Script para inspeccionar la UI del ERP después del login.
Descubre menús, ribbons, y elementos de navegación para automatizar el flujo de ventas.
"""
import json
import time
import subprocess
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui_inspector import _create_root_session, _get_page_source, _delete_session, _parse_elements

REMOTE_URL = "http://127.0.0.1:4723"
APP = r"C:\Users\BrayanEscobar\AppData\Local\BnetEmpresarial\current\ERP.Empresarial.exe"
USER = "brayan"
PASSWORD = "cafe123."

def send_keys(session_id, element_id, text):
    body = json.dumps({"value": list(text)}).encode("utf-8")
    from urllib.request import Request, urlopen
    req = Request(
        f"{REMOTE_URL}/session/{session_id}/element/{element_id}/value",
        data=body, headers={"Content-Type": "application/json"}
    )
    urlopen(req, timeout=10)

def find_element(session_id, strategy, value):
    from urllib.request import Request, urlopen
    body = json.dumps({"using": strategy, "value": value}).encode("utf-8")
    req = Request(
        f"{REMOTE_URL}/session/{session_id}/element",
        data=body, headers={"Content-Type": "application/json"}
    )
    resp = urlopen(req, timeout=10)
    data = json.loads(resp.read().decode("utf-8"))
    element_id = data.get("value", {})
    if isinstance(element_id, dict):
        return element_id.get("ELEMENT") or list(element_id.values())[0]
    return element_id

def click_element(session_id, element_id):
    from urllib.request import Request, urlopen
    body = json.dumps({}).encode("utf-8")
    req = Request(
        f"{REMOTE_URL}/session/{session_id}/element/{element_id}/click",
        data=body, headers={"Content-Type": "application/json"}
    )
    urlopen(req, timeout=10)

def clear_element(session_id, element_id):
    from urllib.request import Request, urlopen
    body = json.dumps({}).encode("utf-8")
    req = Request(
        f"{REMOTE_URL}/session/{session_id}/element/{element_id}/clear",
        data=body, headers={"Content-Type": "application/json"}
    )
    urlopen(req, timeout=10)

def main():
    # Kill any existing ERP instances
    subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], 
                   capture_output=True)
    time.sleep(2)
    
    # Launch ERP
    print("Lanzando ERP...")
    proc = subprocess.Popen([APP])
    print(f"  PID: {proc.pid}, esperando {20}s para carga...")
    time.sleep(20)
    
    # Create Root session
    print("Conectando a WinAppDriver (Root)...")
    session_id = _create_root_session()
    print(f"  Session ID: {session_id}")
    
    try:
        # Login - esperar a que aparezca txtUser
        print("Esperando formulario de login...")
        txt_user = None
        for i in range(30):
            try:
                txt_user = find_element(session_id, "accessibility id", "txtUser")
                print(f"  txtUser encontrado después de {i+1}s")
                break
            except:
                time.sleep(1)
        if not txt_user:
            print("ERROR: No se encontró txtUser después de 30s")
            return
        
        print("Haciendo login...")
        clear_element(session_id, txt_user)
        send_keys(session_id, txt_user, USER)
        
        txt_pass = find_element(session_id, "accessibility id", "txtPassw")
        clear_element(session_id, txt_pass)
        send_keys(session_id, txt_pass, PASSWORD)
        
        btn_ok = find_element(session_id, "accessibility id", "btnOK")
        click_element(session_id, btn_ok)
        
        print("Esperando interfaz principal (30s)...")
        for i in range(30):
            time.sleep(1)
            try:
                find_element(session_id, "accessibility id", "frmInicioComercial")
                print(f"  frmInicioComercial visible después de {i+1}s")
                break
            except:
                pass
        else:
            print("  ADVERTENCIA: frmInicioComercial no encontrado después de 30s")
        
        # Extra wait for UI to stabilize
        time.sleep(3)
        
        # Inspect the main interface
        print("\n" + "="*80)
        print("INSPECCIONANDO INTERFAZ PRINCIPAL DEL ERP")
        print("="*80)
        
        xml_source = _get_page_source(session_id)
        
        # Save full XML
        os.makedirs("reports", exist_ok=True)
        xml_path = os.path.join("reports", "post_login_ui.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_source)
        print(f"\nXML completo guardado en: {xml_path}")
        
        # Parse and filter for interesting elements
        all_elements = _parse_elements(xml_source)
        print(f"Total de elementos: {len(all_elements)}")
        
        # Filter for elements with AutomationId (most useful for automation)
        with_id = [e for e in all_elements if e.get("AutomationId")]
        print(f"Elementos con AutomationId: {len(with_id)}")
        
        # Save filtered report
        report_path = os.path.join("reports", "post_login_elements.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"ELEMENTOS POST-LOGIN - Total: {len(all_elements)}, Con AutomationId: {len(with_id)}\n")
            f.write("="*80 + "\n\n")
            
            # Group by keywords related to sales flow
            keywords = ["pedido", "remisi", "factur", "devolu", "venta", "movimiento", 
                        "menu", "ribbon", "tab", "btn", "grid", "catalogo", "articulo",
                        "cliente", "almacen", "inventario", "proceso", "aprobar"]
            
            f.write(">> ELEMENTOS RELEVANTES PARA FLUJO DE VENTAS:\n")
            f.write("-"*60 + "\n")
            relevant = []
            for elem in all_elements:
                text = " ".join(str(v).lower() for v in elem.values())
                if any(kw in text for kw in keywords):
                    relevant.append(elem)
                    auto_id = elem.get("AutomationId", "")
                    name = elem.get("Name", "")
                    ctrl = elem.get("LocalizedControlType", elem.get("type", ""))
                    cls = elem.get("ClassName", "")
                    f.write(f"  [{ctrl}] AutomationId=\"{auto_id}\" Name=\"{name}\" Class=\"{cls}\"\n")
            
            f.write(f"\nTotal relevantes: {len(relevant)}\n\n")
            
            f.write(">> TODOS LOS ELEMENTOS CON AutomationId:\n")
            f.write("-"*60 + "\n")
            for elem in with_id:
                auto_id = elem.get("AutomationId", "")
                name = elem.get("Name", "")
                ctrl = elem.get("LocalizedControlType", elem.get("type", ""))
                cls = elem.get("ClassName", "")
                f.write(f"  [{ctrl}] AutomationId=\"{auto_id}\" Name=\"{name}\" Class=\"{cls}\"\n")
        
        print(f"Reporte filtrado guardado en: {report_path}")
        
        # Print relevant elements to console
        print(f"\n>> ELEMENTOS RELEVANTES PARA FLUJO DE VENTAS ({len(relevant)}):")
        for elem in relevant[:50]:
            auto_id = elem.get("AutomationId", "")
            name = elem.get("Name", "")
            ctrl = elem.get("LocalizedControlType", elem.get("type", ""))
            print(f"  [{ctrl}] AutomationId=\"{auto_id}\" Name=\"{name}\"")
        if len(relevant) > 50:
            print(f"  ... y {len(relevant)-50} más (ver reporte)")
            
    finally:
        _delete_session(session_id)
        subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)

if __name__ == "__main__":
    main()
