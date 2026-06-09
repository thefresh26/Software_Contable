import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/client'

export default function EmpresaNueva() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    nombre: '',
    nit: '',
    razon_social: '',
    direccion: '',
    ciudad: '',
    telefono: '',
    email: '',
    representante_legal: '',
    regimen: 'comun',
  })
  const [guardando, setGuardando] = useState(false)
  const [errores, setErrores] = useState({})

  function handleChange(e) {
    const { name, value } = e.target
    setForm(f => ({ ...f, [name]: value }))
    if (errores[name]) setErrores(e => ({ ...e, [name]: null }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setGuardando(true)
    setErrores({})
    try {
      const { data } = await api.post('/empresas/', form)
      // Opcional: correr setup para cargar PUC
      try {
        await api.post(`/empresas/${data.id}/setup/`)
      } catch { /* silenciar si el importador no está disponible */ }
      navigate('/empresas')
    } catch (err) {
      if (err.response?.data) setErrores(err.response.data)
    } finally {
      setGuardando(false)
    }
  }

  const campo = (name, label, type = 'text', required = false) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input
        type={type}
        name={name}
        value={form[name]}
        onChange={handleChange}
        required={required}
        className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          errores[name] ? 'border-red-400' : 'border-gray-300'
        }`}
      />
      {errores[name] && <p className="text-xs text-red-500 mt-1">{errores[name]}</p>}
    </div>
  )

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Nueva Empresa</h1>
        <p className="text-sm text-gray-500 mt-1">
          Al crear la empresa se cargará el Plan Único de Cuentas (PUC) automáticamente.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {campo('nombre', 'Nombre Comercial', 'text', true)}
          {campo('nit', 'NIT', 'text', true)}
        </div>
        {campo('razon_social', 'Razón Social', 'text', true)}
        <div className="grid grid-cols-2 gap-4">
          {campo('ciudad', 'Ciudad')}
          {campo('telefono', 'Teléfono')}
        </div>
        {campo('email', 'Correo electrónico', 'email')}
        {campo('representante_legal', 'Representante Legal')}
        {campo('direccion', 'Dirección')}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Régimen</label>
          <select
            name="regimen"
            value={form.regimen}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="comun">Régimen Común</option>
            <option value="simplificado">Régimen Simplificado</option>
          </select>
        </div>

        {errores.non_field_errors && (
          <p className="text-sm text-red-600">{errores.non_field_errors}</p>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate('/empresas')}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={guardando}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {guardando ? 'Creando...' : 'Crear Empresa'}
          </button>
        </div>
      </form>
    </div>
  )
}
