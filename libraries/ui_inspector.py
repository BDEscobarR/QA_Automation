"""
UI Inspector — Inspecciona el árbol de elementos de una app Windows via WinAppDriver.

Uso standalone:
    1. Asegúrate de que WinAppDriver esté corriendo
    2. Abre la app BnetEmpresarial manualmente
    3. Ejecuta: python libraries/ui_inspector.py

Uso como Robot Framework Library:
    Library    ../libraries/ui_inspector.py
    Inspeccionar UI
"""

import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.error import URLError
import json
import os

REMOTE_URL = "http://127.0.0.1:4723"
REPORT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "ui_elements.txt")

USEFUL_ATTRS = ["AutomationId", "Name", "ClassName", "LocalizedControlType"]


def _create_root_session(remote_url=REMOTE_URL):
    """Crea una sesión Root de WinAppDriver para inspeccionar el escritorio."""
    body = json.dumps({
        "desiredCapabilities": {
            "platformName": "Windows",
            "deviceName": "WindowsPC",
            "app": "Root"
        }
    }).encode("utf-8")
    for attempt in range(3):
        try:
            req = Request(f"{remote_url}/session", data=body, headers={"Content-Type": "application/json"})
            resp = urlopen(req, timeout=15)
            data = json.loads(resp.read().decode("utf-8"))
            return data["sessionId"]
        except Exception as e:
            if attempt < 2:
                import time
                print(f"  Reintentando conexión ({attempt + 1}/3)... Error: {e}")
                time.sleep(3)
            else:
                raise


def _get_page_source(session_id, remote_url=REMOTE_URL):
    """Obtiene el XML del árbol de UI de la sesión."""
    req = Request(f"{remote_url}/session/{session_id}/source")
    resp = urlopen(req, timeout=60)
    return resp.read().decode("utf-8")


def _delete_session(session_id, remote_url=REMOTE_URL):
    """Cierra la sesión de WinAppDriver."""
    req = Request(f"{remote_url}/session/{session_id}", method="DELETE")
    try:
        urlopen(req, timeout=5)
    except Exception:
        pass


def _parse_elements(xml_source, filter_name=None):
    """Parsea el XML y extrae los elementos con atributos útiles."""
    root = ET.fromstring(xml_source)
    elements = []

    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        attrs = {k: v for k, v in elem.attrib.items() if k in USEFUL_ATTRS and v.strip()}

        if not attrs:
            continue

        if filter_name and not any(
            filter_name.lower() in str(v).lower() for v in attrs.values()
        ):
            continue

        elements.append({"type": tag, **attrs})

    return elements


def _format_element(elem):
    """Formatea un elemento para mostrar en consola."""
    parts = []
    auto_id = elem.get("AutomationId", "")
    name = elem.get("Name", "")
    class_name = elem.get("ClassName", "")
    ctrl_type = elem.get("LocalizedControlType", elem.get("type", ""))

    line = f"  [{ctrl_type}]"
    if auto_id:
        parts.append(f'AutomationId="{auto_id}"')
    if name:
        display_name = name[:60] + "..." if len(name) > 60 else name
        parts.append(f'Name="{display_name}"')
    if class_name:
        parts.append(f'ClassName="{class_name}"')

    line += "  " + "  |  ".join(parts)

    # Suggest best locator
    if auto_id:
        line += f'\n    -> Locator: xpath=//*[@AutomationId="{auto_id}"]'
    elif name:
        line += f'\n    -> Locator: name={name}'

    return line


def inspect_app(filter_name=None, remote_url=REMOTE_URL, session_id=None):
    """
    Inspecciona todos los elementos visibles de la UI.

    Args:
        filter_name: Filtrar elementos que contengan este texto (opcional)
        remote_url: URL de WinAppDriver
        session_id: ID de sesión existente (si None, crea una Root session)
    Returns:
        Lista de diccionarios con los elementos encontrados
    """
    own_session = session_id is None
    if own_session:
        session_id = _create_root_session(remote_url)
    try:
        xml_source = _get_page_source(session_id, remote_url)
        elements = _parse_elements(xml_source, filter_name)
        return elements, xml_source
    finally:
        if own_session:
            _delete_session(session_id, remote_url)


def save_report(elements, xml_source=None):
    """Guarda el reporte en reports/ui_elements.txt"""
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"UI INSPECTOR - Elementos encontrados: {len(elements)}\n")
        f.write("=" * 80 + "\n\n")
        for elem in elements:
            f.write(_format_element(elem) + "\n\n")

    if xml_source:
        xml_path = REPORT_FILE.replace(".txt", "_raw.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_source)

    return REPORT_FILE


# ══════════════════════════════════════════════
#  Robot Framework Keywords
# ══════════════════════════════════════════════

class UIInspector:
    """Robot Framework Library para inspeccionar UI."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def _get_active_session_id(self, remote_url=REMOTE_URL):
        """Intenta obtener el session ID activo de WinAppDriver."""
        try:
            req = Request(f"{remote_url}/sessions")
            resp = urlopen(req, timeout=5)
            data = json.loads(resp.read().decode("utf-8"))
            sessions = data.get("value", [])
            if sessions:
                return sessions[0].get("id")
        except Exception:
            pass
        return None

    def inspeccionar_ui(self, filtro=None, remote_url=REMOTE_URL):
        """
        Inspecciona la UI y genera un reporte con todos los elementos.
        Usa la sesión activa si existe, si no crea una Root session.

        Ejemplo en Robot:
            Inspeccionar UI
            Inspeccionar UI    filtro=txt
            Inspeccionar UI    filtro=login
        """
        session_id = self._get_active_session_id(remote_url)
        if session_id:
            print(f"  Usando sesión activa: {session_id}")
        else:
            print("  No hay sesión activa, creando Root session...")
        elements, xml_source = inspect_app(
            filter_name=filtro, remote_url=remote_url, session_id=session_id
        )
        report_path = save_report(elements, xml_source)
        print(f"\n{'=' * 60}")
        print(f" ELEMENTOS ENCONTRADOS: {len(elements)}")
        print(f" Reporte guardado en: {report_path}")
        print(f"{'=' * 60}\n")
        for elem in elements:
            print(_format_element(elem))
            print()
        return elements


# ══════════════════════════════════════════════
#  Ejecución standalone
# ══════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    filtro = sys.argv[1] if len(sys.argv) > 1 else None

    print("\n" + "=" * 60)
    print(" UI INSPECTOR - BnetEmpresarial")
    print("=" * 60)

    if filtro:
        print(f" Filtro: '{filtro}'")

    print(" Conectando a WinAppDriver...\n")

    try:
        elements, xml_source = inspect_app(filter_name=filtro)
    except Exception as e:
        print(f" ERROR: No se pudo conectar a WinAppDriver: {e}")
        print(" Asegúrate de que WinAppDriver esté corriendo en http://127.0.0.1:4723")
        print(" Ejecuta: C:\\Program Files (x86)\\Windows Application Driver\\WinAppDriver.exe")
        sys.exit(1)

    if not elements:
        print(" No se encontraron elementos" + (f" con filtro '{filtro}'" if filtro else ""))
        sys.exit(0)

    print(f" Elementos encontrados: {len(elements)}\n")
    print("-" * 60)

    for elem in elements:
        print(_format_element(elem))
        print()

    report_path = save_report(elements, xml_source)
    print("-" * 60)
    print(f" Reporte guardado: {report_path}")
    print(f" XML crudo guardado: {report_path.replace('.txt', '_raw.xml')}")
    print(f"\n Tip: Usa filtro para buscar elementos específicos:")
    print(f"   python libraries/ui_inspector.py txt")
    print(f"   python libraries/ui_inspector.py login")
    print(f"   python libraries/ui_inspector.py password")
