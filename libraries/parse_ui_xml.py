"""Parse the JSON-wrapped XML from WinAppDriver page source and extract ERP elements."""
import json
import xml.etree.ElementTree as ET

with open("reports/post_login_ui.xml", "r", encoding="utf-8") as f:
    data = json.load(f)

xml_str = data["value"]

# Save clean XML
with open("reports/post_login_clean.xml", "w", encoding="utf-8") as f:
    f.write(xml_str)

# Parse - fix encoding declaration
xml_str2 = xml_str.replace('encoding="utf-16"', 'encoding="utf-8"')
root = ET.fromstring(xml_str2.encode("utf-8"))

# Collect ALL elements with AutomationId or Name
elements = []
for elem in root.iter():
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

print(f"Total elements with ID/Name: {len(elements)}")

# Filter for elements with non-empty AutomationId
with_autoid = [e for e in elements if e["AutomationId"].strip()]
print(f"Elements with AutomationId: {len(with_autoid)}")

# Show all elements with AutomationId
print("\n=== ALL ELEMENTS WITH AutomationId ===")
for e in with_autoid:
    name_display = e["Name"][:60] if e["Name"] else ""
    print(f"  [{e['ControlType']}] AutomationId='{e['AutomationId']}' Name='{name_display}' Class='{e['ClassName']}'")

# Filter for sales-flow-relevant keywords
keywords = ["pedido", "remisi", "factur", "devolu", "venta", "movimiento",
            "menu", "ribbon", "tab", "btn", "grid", "catalogo", "articulo",
            "cliente", "almacen", "inventario", "proceso", "aprobar",
            "frm", "panel", "comercial", "inicio", "nav", "tool", "strip",
            "tree", "node", "item"]

print("\n=== RELEVANT ELEMENTS FOR SALES FLOW ===")
relevant = []
for e in elements:
    text = (e["AutomationId"] + " " + e["Name"] + " " + e["ClassName"]).lower()
    if any(kw in text for kw in keywords):
        relevant.append(e)
        name_display = e["Name"][:60] if e["Name"] else ""
        print(f"  [{e['ControlType']}] AutomationId='{e['AutomationId']}' Name='{name_display}' Class='{e['ClassName']}'")

print(f"\nTotal relevant: {len(relevant)}")

# Save full report
with open("reports/post_login_elements.txt", "w", encoding="utf-8") as f:
    f.write(f"Total elements: {len(elements)}\n")
    f.write(f"With AutomationId: {len(with_autoid)}\n")
    f.write(f"Relevant for sales: {len(relevant)}\n\n")
    f.write("=== ALL ELEMENTS WITH AutomationId ===\n")
    for e in with_autoid:
        f.write(f"  [{e['ControlType']}] AutomationId='{e['AutomationId']}' Name='{e['Name']}' Class='{e['ClassName']}'\n")
    f.write(f"\n=== ALL ELEMENTS WITH Name (no AutomationId) ===\n")
    named_only = [e for e in elements if not e["AutomationId"].strip() and e["Name"].strip()]
    for e in named_only:
        f.write(f"  [{e['ControlType']}] Name='{e['Name'][:80]}' Class='{e['ClassName']}'\n")

print("\nReport saved to reports/post_login_elements.txt")
