*** Settings ***
Library    Process
Library    OperatingSystem
Library    AppiumLibrary
Library    libraries.ui_inspector.UIInspector
Resource    ../variables.robot

*** Keywords ***
# ══════════════════════════════════════════════
#  Setup / Teardown
# ══════════════════════════════════════════════
Asegurar WinAppDriver
    [Documentation]    Verifica si WinAppDriver ya está corriendo; si no, lo inicia.
    ${result}=    Run Process    tasklist    /FI    IMAGENAME eq WinAppDriver.exe    /NH
    ${running}=    Evaluate    "WinAppDriver" in """${result.stdout}"""
    Run Keyword If    not ${running}    Start Process    ${WINAPPDRIVER}    alias=winappdriver
    Run Keyword If    not ${running}    Sleep    3s

Abrir ERP
    [Documentation]    Asegura WinAppDriver, lanza la app y conecta via Root.
    Asegurar WinAppDriver
    # Matar instancias huérfanas de la app
    Run Process    taskkill    /F    /IM    ERP.Empresarial.exe    stderr=STDOUT
    Sleep    2s
    Start Process    ${APP}    alias=erp
    Sleep    ${APP_LOAD_TIME}
    Open Application    ${REMOTE_URL}
    ...    platformName=Windows
    ...    deviceName=WindowsPC
    ...    app=Root
    ...    alias=root
    Wait Until Element Is Visible    ${LOGIN_TXT_USER}    ${TIMEOUT}

Cerrar ERP
    [Documentation]    Cierra la sesión de Appium y la app.
    Run Keyword And Ignore Error    Cerrar Sesion Scoped
    Run Keyword And Ignore Error    Switch Application    root
    Run Keyword And Ignore Error    Close Application
    Run Keyword And Ignore Error    Terminate Process    erp    kill=True
    Run Keyword And Ignore Error    Run Process    taskkill    /F    /IM    ERP.Empresarial.exe    stderr=STDOUT

# ══════════════════════════════════════════════
#  Login Page
# ══════════════════════════════════════════════
Ingresar Credenciales
    [Documentation]    Escribe usuario y contraseña en el formulario de login.
    [Arguments]    ${user}    ${password}
    Wait Until Element Is Visible    ${LOGIN_TXT_USER}    ${TIMEOUT}
    Clear Text    ${LOGIN_TXT_USER}
    Input Text    ${LOGIN_TXT_USER}    ${user}
    Clear Text    ${LOGIN_TXT_PASSWORD}
    Input Text    ${LOGIN_TXT_PASSWORD}    ${password}

Click Boton Login
    [Documentation]    Hace clic en el botón "Iniciar sesión".
    Wait Until Element Is Visible    ${LOGIN_BTN_INGRESAR}    ${TIMEOUT}
    Click Element    ${LOGIN_BTN_INGRESAR}

Validar Login Exitoso
    [Documentation]    Valida que el login fue exitoso verificando que la interfaz
    ...    principal del ERP es visible después de iniciar sesión.
    Wait Until Element Is Visible    accessibility_id=frmInicioComercial    30s
    Log    Login exitoso - interfaz principal del ERP visible.

Validar Mensaje De Error Login
    [Documentation]    Valida que el sistema muestra un mensaje de error al intentar
    ...    iniciar sesión con credenciales inválidas.
    # Intentar cerrar el mensaje de error con Enter o buscar botón Aceptar
    ${aceptar_visible}=    Run Keyword And Return Status
    ...    Wait Until Element Is Visible    name=Aceptar    10s
    Run Keyword If    ${aceptar_visible}    Run Keywords
    ...    Log    Mensaje de error detectado - botón Aceptar encontrado
    ...    AND    Click Element    name=Aceptar
    ...    AND    Return From Keyword
    # Alternativa: botón OK en MessageBox estándar de Windows
    ${ok_visible}=    Run Keyword And Return Status
    ...    Wait Until Element Is Visible    name=OK    5s
    Run Keyword If    ${ok_visible}    Run Keywords
    ...    Log    Mensaje de error detectado - botón OK encontrado
    ...    AND    Click Element    name=OK
    ...    AND    Return From Keyword
    # Si el form de login sigue visible, el login fue rechazado
    Wait Until Element Is Visible    ${LOGIN_BTN_INGRESAR}    5s
    Log    Login rechazado - formulario de login sigue visible.

# ══════════════════════════════════════════════
#  Utilidades
# ══════════════════════════════════════════════
Inspeccionar Elementos
    [Documentation]    Escanea la UI actual y genera reporte en reports/ui_elements.txt
    [Arguments]    ${filtro}=${EMPTY}
    Run Keyword If    '${filtro}' != ''    inspeccionar_ui   filtro=${filtro}
    ...    ELSE    inspeccionar_ui

# ══════════════════════════════════════════════
#  Sesión Scoped (para controles DevExpress)
# ══════════════════════════════════════════════
Crear Sesion Scoped
    [Documentation]    Crea una sesión de Appium anclada a la ventana principal del ERP
    ...    para poder interactuar con TreeItems del accordion DevExpress.
    Switch Application    root
    ${frm}=    Get Element Attribute    ${NAV_MAIN_FORM}    NativeWindowHandle
    ${handle}=    Evaluate    hex(int($frm))
    Open Application    ${REMOTE_URL}
    ...    platformName=Windows
    ...    deviceName=WindowsPC
    ...    appTopLevelWindow=${handle}
    ...    alias=scoped

Cambiar A Root
    [Documentation]    Cambia a la sesión Root.
    Switch Application    root

Cambiar A Scoped
    [Documentation]    Cambia a la sesión scoped del ERP.
    Switch Application    scoped

Cerrar Sesion Scoped
    [Documentation]    Cierra la sesión scoped si existe.
    Run Keyword And Ignore Error    Switch Application    scoped
    Run Keyword And Ignore Error    Close Application

# ══════════════════════════════════════════════
#  Navegación Accordion
# ══════════════════════════════════════════════
Validar Restriccion De Rol En Movimientos
    [Documentation]    Valida que un usuario con rol restringido no puede ver
    ...    las opciones dentro de Movimientos (PE - PEDIDO, FV - FACTURA, etc.).
    Cambiar A Root
    Wait Until Element Is Visible    ${NAV_MAIN_FORM}    30s
    Sleep    1s
    Crear Sesion Scoped
    # Expandir Movimientos
    Cambiar A Root
    Click Element    ${NAV_MOVIMIENTOS}
    Sleep    2s
    # Verificar que PE - PEDIDO NO aparece (rol restringido)
    Cambiar A Scoped
    ${pe_visible}=    Run Keyword And Return Status
    ...    Wait Until Element Is Visible    ${NAV_PE_PEDIDO}    5s
    Should Be Equal    ${pe_visible}    ${FALSE}
    ...    El usuario con rol restringido NO debería ver PE - PEDIDO en Movimientos.
    Log    Restricción de rol validada: PE - PEDIDO no visible para este usuario.

Navegar A PE02 Pedido
    [Documentation]    Navega el accordion: Movimientos → PE - PEDIDO → PE02 - PEDIDO
    Cambiar A Root
    Wait Until Element Is Visible    ${NAV_MAIN_FORM}    30s
    Sleep    1s
    Crear Sesion Scoped
    # Expandir Movimientos
    Cambiar A Root
    Click Element    ${NAV_MOVIMIENTOS}
    Sleep    2s
    # Expandir PE - PEDIDO
    Cambiar A Scoped
    Wait Until Element Is Visible    ${NAV_PE_PEDIDO}    10s
    Click Element    ${NAV_PE_PEDIDO}
    Sleep    2s
    # Click en PE02 - PEDIDO para abrir el formulario
    Wait Until Element Is Visible    ${NAV_PE02_PEDIDO}    10s
    Click Element    ${NAV_PE02_PEDIDO}
    # Esperar a que el formulario cargue en lugar de Sleep fijo
    Cambiar A Root
    Wait Until Element Is Visible    ${PED_FORM}    15s
    Sleep    1s

Validar Formulario Pedido Visible
    [Documentation]    Valida que el formulario de pedido (frmFaVentaR) se abrió correctamente.
    Wait Until Element Is Visible    ${PED_FORM}    20s
    Log    Formulario de pedido PE02 visible.

# ══════════════════════════════════════════════
#  Formulario de Pedido
# ══════════════════════════════════════════════
Ingresar Cliente En Pedido
    [Documentation]    Ingresa el código de cliente en el campo Cliente del pedido.
    [Arguments]    ${cliente}
    Wait Until Element Is Visible    ${PED_TXT_CLIENTE}    10s
    Clear Text    ${PED_TXT_CLIENTE}
    Input Text    ${PED_TXT_CLIENTE}    ${cliente}
    # Enter para confirmar selección del cliente
    Input Text    ${PED_TXT_CLIENTE}    \ue007
    Sleep    3s

Ingresar Articulo En Grid
    [Documentation]    Ingresa un artículo en la fila indicada de la grilla.
    [Arguments]    ${codigo}    ${fila}    ${cantidad}=1
    ${art_cell}=    Set Variable    name=Artículo Fila ${fila}
    Wait Until Element Is Visible    ${art_cell}    10s
    Click Element    ${art_cell}
    # Escribir código de artículo y ENTER para confirmar
    Input Text    ${art_cell}    ${codigo}
    Input Text    ${art_cell}    \ue007
    Sleep    2s
    # Hacer clic en la celda Cant. de la fila y escribir cantidad
    ${cant_cell}=    Set Variable    name=Cant. Fila ${fila}, Sin orden.
    Wait Until Element Is Visible    ${cant_cell}    10s
    Click Element    ${cant_cell}
    Input Text    ${cant_cell}    ${cantidad}
    Input Text    ${cant_cell}    \ue007
    Sleep    2s

Ingresar Articulos En Pedido
    [Documentation]    Ingresa una lista de artículos en la grilla del pedido.
    [Arguments]    @{articulos}
    ${fila}=    Set Variable    ${0}
    FOR    ${codigo}    IN    @{articulos}
        Ingresar Articulo En Grid    ${codigo}    ${fila}    ${CANTIDAD_PEDIDO}
        ${fila}=    Evaluate    ${fila} + 1
    END

Grabar Pedido
    [Documentation]    Hace clic en Grabar y confirma el diálogo de validación.
    Click Element    ${PED_BTN_GRABAR}
    # Confirmar diálogo "¿Está seguro de grabar?"
    ${si_visible}=    Run Keyword And Return Status
    ...    Wait Until Element Is Visible    name=Sí    10s
    Run Keyword If    ${si_visible}    Click Element    name=Sí
    ...    ELSE    Run Keywords
    ...    ${yes_visible}=    Run Keyword And Return Status
    ...    Wait Until Element Is Visible    name=Yes    5s
    ...    AND    Run Keyword If    ${yes_visible}    Click Element    name=Yes
    Sleep    2s

Validar Pedido Grabado
    [Documentation]    Valida que el pedido se grabó: el formulario vuelve al estado
    ...    inicial (nuevo pedido) con el campo cliente vacío.
    Sleep    3s
    # Verificar que el formulario sigue visible (se reinició para nuevo pedido)
    Wait Until Element Is Visible    ${PED_FORM}    10s
    # Verificar que el campo cliente está vacío (formulario reseteado)
    ${cliente_val}=    Get Text    ${PED_TXT_CLIENTE}
    Should Be Empty    ${cliente_val}    El campo cliente no se limpió después de grabar.
    Log    Pedido grabado correctamente - formulario reseteado para nuevo pedido.

