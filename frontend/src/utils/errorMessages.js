const FIELD_NAMES = {
  nombre: 'Nombre',
  nit: 'NIT/Cédula',
  email: 'Correo electrónico',
  telefono: 'Teléfono',
  direccion: 'Dirección',
  ciudad: 'Ciudad',
  tipo: 'Tipo',
  fecha: 'Fecha',
  fecha_vencimiento: 'Fecha de vencimiento',
  tercero: 'Tercero',
  producto: 'Producto',
  cantidad: 'Cantidad',
  precio_unitario: 'Precio unitario',
  codigo: 'Código',
  stock_actual: 'Stock actual',
  precio_venta: 'Precio de venta',
  salario_base: 'Salario base',
  valor: 'Valor',
  cuenta_debito: 'Cuenta débito',
  cuenta_credito: 'Cuenta crédito',
  descripcion: 'Descripción',
  periodo: 'Período',
  resolucion: 'Resolución',
  numero_desde: 'Número desde',
  numero_hasta: 'Número hasta',
}

const KNOWN_ERRORS = {
  'already exists': 'ya existe en el sistema',
  'This field is required': 'es obligatorio',
  'This field may not be blank': 'no puede estar vacío',
  'This field may not be null': 'es obligatorio',
  'Enter a valid email address': 'debe ser un correo válido',
  'A valid integer is required': 'debe ser un número entero válido',
  'A valid number is required': 'debe ser un número válido',
  'Ensure this value is greater than or equal to 0': 'debe ser mayor o igual a 0',
  'Ensure this field has no more than': 'supera el máximo permitido',
  'unique constraint': 'ya está registrado',
  'does not exist': 'no existe en el sistema',
  'No active account found': 'Usuario o contraseña incorrectos',
  'Token is invalid': 'Su sesión ha expirado. Inicie sesión nuevamente',
  'Permission denied': 'No tiene permisos para realizar esta acción',
  'This password is too short': 'La contraseña es muy corta (mínimo 8 caracteres)',
  'This password is too common': 'La contraseña es muy común. Use una más segura',
}

function translateField(field) {
  return FIELD_NAMES[field] || field.replace(/_/g, ' ')
}

function translateError(msg) {
  for (const [key, val] of Object.entries(KNOWN_ERRORS)) {
    if (msg.toLowerCase().includes(key.toLowerCase())) return val
  }
  return msg
}

export function parseApiError(err) {
  const data = err?.response?.data

  if (!data) {
    if (err?.message?.includes('Network Error') || err?.message?.includes('net::ERR')) {
      return 'Sin conexión al servidor. Verifique su internet e intente de nuevo.'
    }
    return 'Error inesperado. Intente de nuevo.'
  }

  if (typeof data === 'string') return data

  if (data.detail) return translateError(String(data.detail))
  if (data.error) return String(data.error)
  if (data.non_field_errors) return data.non_field_errors.join('. ')

  if (typeof data === 'object') {
    const msgs = []
    for (const [field, errors] of Object.entries(data)) {
      if (field === 'non_field_errors') continue
      const errList = Array.isArray(errors) ? errors : [errors]
      const fieldName = translateField(field)
      errList.forEach((e) => {
        const translated = translateError(String(e))
        msgs.push(`${fieldName}: ${translated}`)
      })
    }
    if (msgs.length > 0) return msgs.join('\n')
  }

  return 'Error al procesar la solicitud. Revise los datos e intente de nuevo.'
}

export function successMessage(action, entity, identifier = '') {
  const msgs = {
    crear: `${entity}${identifier ? ` "${identifier}"` : ''} creado/a correctamente.`,
    editar: `${entity}${identifier ? ` "${identifier}"` : ''} actualizado/a correctamente.`,
    eliminar: `${entity}${identifier ? ` "${identifier}"` : ''} eliminado/a correctamente.`,
    guardar: `${entity}${identifier ? ` "${identifier}"` : ''} guardado/a correctamente.`,
    emitir: `${entity}${identifier ? ` ${identifier}` : ''} emitida correctamente.`,
    anular: `${entity}${identifier ? ` ${identifier}` : ''} anulada correctamente.`,
    aprobar: `${entity}${identifier ? ` ${identifier}` : ''} aprobada correctamente.`,
    pagar: `Pago registrado correctamente para ${entity}${identifier ? ` ${identifier}` : ''}.`,
    exportar: `${entity} exportado/a a Excel correctamente.`,
    importar: `Datos importados correctamente.`,
    cerrar: `${entity}${identifier ? ` "${identifier}"` : ''} cerrado/a correctamente.`,
  }
  return msgs[action] || `${entity} procesado/a correctamente.`
}
