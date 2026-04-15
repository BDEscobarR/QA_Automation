*** Settings ***
Resource    ../../resources/keywords/erp_keywords.robot

Test Setup       Abrir ERP
Test Teardown    Cerrar ERP

*** Test Cases ***
Explorar Menu Accordion
    [Documentation]    Inicia sesión y explora el menú del ERP.
    [Tags]    exploracion
    # Login
    Ingresar Credenciales    ${USER}    ${PASSWORD}
    Click Boton Login
    Validar Login Exitoso
    # Esperar que cargue completamente
    Sleep    3s
    # Hacer click en Movimientos
    Log    === Buscando secciones del menú ===
    ${mov_visible}=    Run Keyword And Return Status
    ...    Wait Until Element Is Visible    name=Movimientos    10s
    Log    Movimientos visible: ${mov_visible}
    Run Keyword If    ${mov_visible}    Click Element    name=Movimientos
    Sleep    2s
    # Capturar screenshot
    Capture Page Screenshot    reports/menu_movimientos.png
    # Intentar expandir con doble click
    Run Keyword If    ${mov_visible}    Click Element    name=Movimientos
    Sleep    1s
    Run Keyword If    ${mov_visible}    Click Element    name=Movimientos
    Sleep    2s
    Capture Page Screenshot    reports/menu_movimientos_expanded.png
    # Usar caja de búsqueda del accordion
    Log    === Usando caja de búsqueda ===
    ${search_visible}=    Run Keyword And Return Status
    ...    Wait Until Element Is Visible    accessibility_id=teSearch    5s
    Run Keyword If    ${search_visible}    Buscar En Accordion    Pedido
    Run Keyword If    ${search_visible}    Buscar En Accordion    Remisi
    Run Keyword If    ${search_visible}    Buscar En Accordion    Factur
    Run Keyword If    ${search_visible}    Buscar En Accordion    Devolu
    Run Keyword If    ${search_visible}    Buscar En Accordion    Aprobar
    Run Keyword If    ${search_visible}    Buscar En Accordion    Cotiz
    Run Keyword If    ${search_visible}    Buscar En Accordion    Nota

*** Keywords ***
Buscar En Accordion
    [Arguments]    ${term}
    Log    Buscando: ${term}
    Click Element    accessibility_id=teSearch
    Sleep    0.3s
    # Limpiar y escribir
    Press Keycode    17    # Ctrl
    Sleep    0.1s
    Clear Text    accessibility_id=teSearch
    Input Text    accessibility_id=teSearch    ${term}
    Sleep    2s
    Capture Page Screenshot    reports/search_${term}.png
    # Inspeccionar lo que aparece
    Inspeccionar Elementos    ${term}
