"""Parse clean XML and extract only ERP elements inside frmInicioComercial."""
import json
import xml.etree.ElementTree as ET

with open("reports/post_login_ui.xml", "r", encoding="utf-8") as f:
    data = json.load(f)

xml_str = data["value"]
xml_str = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
root = ET.fromstring(xml_str.encode("utf-8"))

# Find frmInicioComercial and list ALL its children
ns = ""
for elem in root.iter():
    if "}" in elem.tag:
        ns = elem.tag.split("}")[0] + "}"
        break

def find_by_automationid(parent, auto_id):
    for elem in parent.iter():
        if elem.attrib.get("AutomationId") == auto_id:
            return elem
    return None

frm = find_by_automationid(root, "frmInicioComercial")
if not frm:
    print("ERROR: frmInicioComercial no encontrado")
    exit(1)

print(f"=== ELEMENTOS DENTRO DE frmInicioComercial ===\n")

# Collect all children elements
elements = []
for elem in frm.iter():
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    auto_id = elem.attrib.get("AutomationId", "")
    name = elem.attrib.get("Name", "")
    cls = elem.attrib.get("ClassName", "")
    ctrl = elem.attrib.get("LocalizedControlType", "")
    if auto_id or name:
        elements.append({
            "tag": tag, "AutomationId": auto_id, "Name": name,
            "ClassName": cls, "ControlType": ctrl
        })

print(f"Total elements in ERP window: {len(elements)}\n")

# Print all with AutomationId
print("=== ELEMENTS WITH AutomationId ===")
for e in elements:
    if e["AutomationId"]:
        name_short = e["Name"][:60] if e["Name"] else ""
        print(f"  [{e['ControlType']}] AutomationId='{e['AutomationId']}' Name='{name_short}' Class='{e['ClassName']}'")

# Find the accordion menu and its children
print("\n=== ACCORDION MENU STRUCTURE ===")
accordion = find_by_automationid(frm, "accordionControl1")
if accordion:
    for elem in accordion.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        auto_id = elem.attrib.get("AutomationId", "")
        name = elem.attrib.get("Name", "")
        cls = elem.attrib.get("ClassName", "")
        ctrl = elem.attrib.get("LocalizedControlType", "")
        if auto_id or name:
            print(f"  [{ctrl}] AutomationId='{auto_id}' Name='{name[:60]}' Class='{cls}'")
else:
    print("  Accordion no encontrado!")

# Find toolbar/toolstrip
print("\n=== TOOLBAR tsMenu ===")
tsmenu = find_by_automationid(frm, "tsMenu")
if tsmenu:
    for elem in tsmenu.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        auto_id = elem.attrib.get("AutomationId", "")
        name = elem.attrib.get("Name", "")
        ctrl = elem.attrib.get("LocalizedControlType", "")
        if auto_id or name:
            print(f"  [{ctrl}] AutomationId='{auto_id}' Name='{name[:80]}'")
else:
    print("  tsMenu no encontrado!")

# Save element report
with open("reports/erp_elements.txt", "w", encoding="utf-8") as f:
    f.write(f"ERP Elements inside frmInicioComercial: {len(elements)}\n\n")
    for e in elements:
        f.write(f"[{e['ControlType']}] AutomationId='{e['AutomationId']}' Name='{e['Name']}' Class='{e['ClassName']}'\n")
print("\nFull report saved to reports/erp_elements.txt")
