*** Settings ***
Resource    ../../resources/keywords/erp_keywords.robot

Test Setup    Abrir ERP
Test Teardown    Cerrar ERP

*** Test Cases ***
Login Exitoso Con Credenciales Validas
    [Documentation]    BNET-GEN-001: Verifica que el usuario puede iniciar sesión
    ...    en el ERP con usuario y contraseña válidos.
    [Tags]    login    smoke    GEN-001
    Ingresar Credenciales    ${USER}    ${PASSWORD}
    Click Boton Login
    Validar Login Exitoso

Login Fallido Con Contraseña Invalida
    [Documentation]    BNET-GEN-002: Verifica que el sistema muestra un mensaje de
    ...    error al intentar iniciar sesión con una contraseña incorrecta.
    [Tags]    login    negativa    GEN-002
    Ingresar Credenciales    ${USER_INVALIDO}    ${PASSWORD_INVALIDA}
    Click Boton Login
    Validar Mensaje De Error Login

Restriccion De Acceso Por Rol
    [Documentation]    BNET-GEN-003: Verifica que un usuario con rol restringido
    ...    no puede acceder a las opciones de Movimientos (PE - PEDIDO).
    [Tags]    seguridad    roles    GEN-003
    Ingresar Credenciales    ${USER_ROL}    ${PASSWORD_ROL}
    Click Boton Login
    Validar Login Exitoso
    Validar Restriccion De Rol En Movimientos

Crear Pedido De Venta
    [Documentation]    BNET-GEN-009: Verifica que el usuario puede crear un pedido
    ...    de venta navegando por Movimientos → PE-PEDIDO → PE02 - PEDIDO,
    ...    ingresando cliente, artículo y grabando el documento.
    [Tags]    ventas    pedido    smoke    GEN-009
    Ingresar Credenciales    ${USER}    ${PASSWORD}
    Click Boton Login
    Validar Login Exitoso
    Navegar A PE02 Pedido
    Validar Formulario Pedido Visible
    Ingresar Cliente En Pedido    ${CLIENTE_PEDIDO}
    Ingresar Articulos En Pedido    @{ARTICULOS_PEDIDO}
    Grabar Pedido
    Validar Pedido Grabado