import xml.etree.ElementTree as ET
tree = ET.parse('reports/output.xml')
msgs = tree.findall('.//msg')
for m in msgs[-50:]:
    lvl = m.get('level', '')
    txt = (m.text or '')[:250]
    print(f'[{lvl}] {txt}')
