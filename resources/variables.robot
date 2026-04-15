*** Variables ***
# ── Conexión ──
${REMOTE_URL}           http://127.0.0.1:4723
${WINAPPDRIVER}         C:\\Program Files (x86)\\Windows Application Driver\\WinAppDriver.exe

# ── Aplicación ──
${APP}                  C:\\Users\\BrayanEscobar\\AppData\\Local\\BnetEmpresarial\\current\\ERP.Empresarial.exe
${TIMEOUT}              20s
${APP_LOAD_TIME}        10s

# ── Credenciales ──
${USER}                 brayan
${PASSWORD}             cafe123.

# ── Credenciales Inválidas (prueba negativa) ──
${USER_INVALIDO}        usuario_falso
${PASSWORD_INVALIDA}    contraseña_incorrecta

# ── Credenciales Rol Restringido ──
${USER_ROL}             pruebarol
${PASSWORD_ROL}         prueba123.

# ── Locators Login Page ──
${LOGIN_WINDOW}         name=ERP.Empresarial
${LOGIN_TXT_USER}       accessibility_id=txtUser
${LOGIN_TXT_PASSWORD}   accessibility_id=txtPassw
${LOGIN_BTN_INGRESAR}   accessibility_id=btnOK
${LOGIN_MAIN_RIBBON}    accessibility_id=mainRibbon

# ── Locators Navegación Accordion ──
${NAV_MAIN_FORM}        accessibility_id=frmInicioComercial
${NAV_MOVIMIENTOS}      name=Movimientos
${NAV_PE_PEDIDO}        xpath=//TreeItem[@Name='PE - PEDIDO']
${NAV_PE02_PEDIDO}      name=PE02 - PEDIDO

# ── Locators Formulario Pedido ──
${PED_FORM}             accessibility_id=frmFaVentaR
${PED_TITULO}           accessibility_id=pnlTitulo
${PED_TXT_CLIENTE}      accessibility_id=txtCliente
${PED_CBO_VENDEDOR}     accessibility_id=cboVendedor
${PED_CBO_LISTA_PRECIO}    accessibility_id=cboListprecio
${PED_GRID}             accessibility_id=GridVent
${PED_TXT_SUBTOTAL}     accessibility_id=txtVrSubtotal
${PED_TXT_TOTAL}        accessibility_id=txtVrTotal
${PED_MEMO_DETALLE}     accessibility_id=memoObservac
${PED_BTN_GRABAR}       name=Grabar
${PED_TXT_FILAS}        accessibility_id=txtFilas

# ── Datos de Prueba Pedido ──
${CLIENTE_PEDIDO}       100723
@{ARTICULOS_PEDIDO}     000001    000002    000003
${CANTIDAD_PEDIDO}      1