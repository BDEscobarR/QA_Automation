"""Inspecciona los sub-items de Movimientos para pruebarol."""
import time, subprocess
from appium import webdriver

APP = r"C:\Users\BrayanEscobar\AppData\Local\BnetEmpresarial\current\ERP.Empresarial.exe"
subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
time.sleep(2)
subprocess.Popen([APP])
time.sleep(15)

caps = {"platformName": "Windows", "deviceName": "WindowsPC", "app": "Root"}
root = webdriver.Remote("http://127.0.0.1:4723", desired_capabilities=caps)

# Esperar login
for i in range(20):
    try:
        user_field = root.find_element("accessibility id", "txtUser")
        break
    except:
        time.sleep(2)

user_field.clear(); user_field.send_keys("pruebarol")
root.find_element("accessibility id", "txtPassw").clear()
root.find_element("accessibility id", "txtPassw").send_keys("prueba123.")
root.find_element("accessibility id", "btnOK").click()
time.sleep(10)

frm = root.find_element("accessibility id", "frmInicioComercial")
handle = hex(int(frm.get_attribute("NativeWindowHandle")))
caps2 = {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": handle}
scoped = webdriver.Remote("http://127.0.0.1:4723", desired_capabilities=caps2)

# Click Movimientos
root.find_element("name", "Movimientos").click()
time.sleep(3)

# Buscar TreeItems en scoped  
print("=== TREE ITEMS (scoped) ===")
items = scoped.find_elements("class name", "TreeItem")
for item in items:
    print(f"  '{item.get_attribute('Name')}' enabled={item.get_attribute('IsEnabled')}")

# Buscar todo por xpath en scoped
print("\n=== TODOS los TreeItem por xpath ===")
items2 = scoped.find_elements("xpath", "//TreeItem")
for item in items2:
    print(f"  '{item.get_attribute('Name')}'")

# Intentar buscar PE - PEDIDO específicamente
print("\n=== BUSCANDO 'PE - PEDIDO' ===")
try:
    pe = scoped.find_element("xpath", "//TreeItem[@Name='PE - PEDIDO']")
    print(f"  ENCONTRADO: '{pe.get_attribute('Name')}'")
except:
    print("  NO ENCONTRADO")

# Ahora comparar: login con usuario brayan
print("\n\n========= COMPARANDO CON USUARIO BRAYAN =========")
scoped.quit()
root.quit()
subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
time.sleep(3)
subprocess.Popen([APP])
time.sleep(15)

root = webdriver.Remote("http://127.0.0.1:4723", desired_capabilities=caps)
for i in range(20):
    try:
        user_field = root.find_element("accessibility id", "txtUser")
        break
    except:
        time.sleep(2)

user_field.clear(); user_field.send_keys("brayan")
root.find_element("accessibility id", "txtPassw").clear()
root.find_element("accessibility id", "txtPassw").send_keys("cafe123.")
root.find_element("accessibility id", "btnOK").click()
time.sleep(10)

frm = root.find_element("accessibility id", "frmInicioComercial")
handle = hex(int(frm.get_attribute("NativeWindowHandle")))
caps2 = {"platformName": "Windows", "deviceName": "WindowsPC", "appTopLevelWindow": handle}
scoped = webdriver.Remote("http://127.0.0.1:4723", desired_capabilities=caps2)

# Listar secciones del accordion para brayan
print("\n=== SECCIONES ACCORDION (scoped brayan) ===")
items = scoped.find_elements("xpath", "//TreeItem")
for item in items:
    print(f"  '{item.get_attribute('Name')}'")

# Click Movimientos
root.find_element("name", "Movimientos").click()
time.sleep(3)

print("\n=== TREE ITEMS DENTRO DE MOVIMIENTOS (brayan) ===")
items = scoped.find_elements("xpath", "//TreeItem")
for item in items:
    print(f"  '{item.get_attribute('Name')}'")

scoped.quit()
root.quit()
subprocess.run(["taskkill", "/F", "/IM", "ERP.Empresarial.exe"], capture_output=True)
print("\nDONE")
