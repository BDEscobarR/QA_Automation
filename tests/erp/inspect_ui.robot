*** Settings ***
Library    Process
Library    libraries.ui_inspector.UIInspector
Resource    ../../resources/keywords/erp_keywords.robot

Suite Setup    Preparar Inspeccion
Suite Teardown    Finalizar Inspeccion

*** Test Cases ***
Inspeccionar Todos Los Elementos
    [Documentation]    Escanea toda la UI y genera un reporte completo en reports/ui_elements.txt
    [Tags]    inspector    utility
    Inspeccionar UI

Inspeccionar Campos De Texto
    [Documentation]    Busca elementos que contengan "txt" en sus propiedades.
    [Tags]    inspector    utility
    Inspeccionar UI    filtro=txt

Inspeccionar Botones
    [Documentation]    Busca botones de la app (Iniciar, Cancelar, etc.)
    [Tags]    inspector    utility
    Inspeccionar UI    filtro=Button

Inspeccionar Por Nombre Especifico
    [Documentation]    Busca elementos relacionados a "Iniciar sesión"
    [Tags]    inspector    utility
    Inspeccionar UI    filtro=Iniciar

*** Keywords ***
Preparar Inspeccion
    Asegurar WinAppDriver
    Start Process    ${APP}    alias=erp
    Sleep    ${APP_LOAD_TIME}
    Open Application    ${REMOTE_URL}
    ...    platformName=Windows
    ...    deviceName=WindowsPC
    ...    app=Root
    Log    App y WinAppDriver listos para inspección

Finalizar Inspeccion
    Run Keyword And Ignore Error    Close Application
    Run Keyword And Ignore Error    Terminate Process    erp    kill=True
