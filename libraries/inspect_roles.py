"""Inspecciona qué opciones del accordion son visibles para el usuario pruebarol."""
import time, subprocess, json
from appium import webdriver

APP = r"C:\Users\BrayanEscobar\AppData\Local\BnetEmpresarial\current\ERP.Empresarial.exe"
subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
time.sleep(2)
subprocess.Popen([APP])
time.sleep(15)

# Root session
caps = {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
root = webdriver.Remote("http://127.0.0.1:4723", desired_capabilities=caps)

# Esperar a que el login sea visible
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
print("Esperando txtUser...")
for i in range(20):
    try:
        user_field = root.find_element("accessibility id", "txtUser")
        print(f"  txtUser encontrado en intento {i+1}")
        break
    except:
        time.sleep(2)
else:
    # Listar lo que hay visible
    print("  txtUser NO encontrado. Elementos visibles:")
    all_e = root.find_elements("xpath", "//*[@Name!='']")
    for e in all_e[:30]:
        print(f"    [{e.tag_name}] '{e.get_attribute('Name')}'")
    root.quit()
    exit(1)
# Login con pruebarol
user_field.clear()
user_field.send_keys("pruebarol")
pass_field = root.find_element("accessibility id", "txtPassw")
pass_field.clear()
pass_field.send_keys("prueba123.")
btn = root.find_element("accessibility id", "btnOK")
btn.click()
time.sleep(10)

# Verificar si el login fue exitoso
try:
    frm = root.find_element("accessibility id", "frmInicioComercial")
    print("LOGIN EXITOSO - frmInicioComercial encontrado")
    handle = hex(int(frm.get_attribute("NativeWindowHandle")))
    
    # Scoped session
    caps2 = {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": handle}
    scoped = webdriver.Remote("http://127.0.0.1:4723", desired_capabilities=caps2)
    
    # Listar TODOS los elementos del accordion (grupos)
    print("\n=== GRUPOS DEL ACCORDION (root) ===")
    groups = root.find_elements("class name", "GroupBox")
    for g in groups:
        print(f"  GroupBox: '{g.get_attribute('Name')}' enabled={g.get_attribute('IsEnabled')}")
    
    # Buscar botones/items de navegación
    print("\n=== BOTONES (root) ===")
    buttons = root.find_elements("class name", "Button")
    for b in buttons:
        name = b.get_attribute("Name")
        if name and len(name) > 1:
            print(f"  Button: '{name}' enabled={b.get_attribute('IsEnabled')}")
    
    # Intentar hacer click en Movimientos
    print("\n=== INTENTANDO CLICK EN MOVIMIENTOS ===")
    try:
        mov = root.find_element("name", "Movimientos")
        print(f"  Movimientos encontrado! enabled={mov.get_attribute('IsEnabled')}")
        mov.click()
        time.sleep(3)
        
        # Ver qué TreeItems aparecen en scoped
        print("\n=== TREE ITEMS (scoped) después de click Movimientos ===")
        items = scoped.find_elements("class name", "TreeItem")
        for item in items:
            print(f"  TreeItem: '{item.get_attribute('Name')}' enabled={item.get_attribute('IsEnabled')}")
        
        if not items:
            print("  (ningún TreeItem encontrado)")
            
        # Buscar todos los elementos con texto
        print("\n=== TODOS LOS ELEMENTOS CON NOMBRE (scoped) ===")
        all_elems = scoped.find_elements("xpath", "//*[@Name!='']")
        for e in all_elems[:50]:
            ctrl = e.get_attribute("LocalizedControlType") or e.tag_name
            name = e.get_attribute("Name")
            if name and len(name.strip()) > 0:
                print(f"  [{ctrl}] '{name}'")
                
    except Exception as ex:
        print(f"  Movimientos NO encontrado: {ex}")
    
    # Intentar otras secciones
    for section in ["Catálogos", "Procesos", "Informes", "Inventario", "Contabilidad"]:
        print(f"\n=== BUSCANDO '{section}' ===")
        try:
            elem = root.find_element("name", section)
            print(f"  {section} encontrado! enabled={elem.get_attribute('IsEnabled')}")
        except:
            print(f"  {section} NO encontrado")
    
    scoped.quit()
except Exception as ex:
    print(f"LOGIN FALLÓ o frmInicioComercial no encontrado: {ex}")
    # Revisar si hay mensaje de error
    try:
        for cls in ["Text", "Static"]:
            elems = root.find_elements("class name", cls)
            for e in elems:
                n = e.get_attribute("Name")
                if n: print(f"  [{cls}] '{n}'")
    except:
        pass

root.quit()
subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
print("\nDONE")
