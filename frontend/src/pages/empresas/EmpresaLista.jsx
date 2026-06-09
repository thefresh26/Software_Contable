import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import api from '../../api/client'

export default function EmpresaLista() {
  const { user, cambiarEmpresa } = useAuth()
  const [empresas, setEmpresas] = useState([])
  const [loading, setLoading] = useState(true)
  const [cambiando, setCambiando] = useState(null)
  const [modalUsuarios, setModalUsuarios] = useState(null)
  const [usuariosEmpresa, setUsuariosEmpresa] = useState([])

  useEffect(() => {
    api.get('/empresas/').then(({ data }) => {
      setEmpresas(Array.isArray(data) ? data : (data.results || []))
    }).finally(() => setLoading(false))
  }, [])

  async function handleCambiar(empresaId) {
    setCambiando(empresaId)
    try {
      await cambiarEmpresa(empresaId)
      window.location.reload()
    } catch (e) {
      alert('Error al cambiar de empresa')
      setCambiando(null)
    }
  }

  async function abrirUsuarios(empresa) {
    setModalUsuarios(empresa)
    const { data } = await api.get(`/empresas/${empresa.id}/usuarios/`)
    setUsuariosEmpresa(Array.isArray(data) ? data : (data.results || []))
  }

  if (loading) return <div className="p-6 text-gray-500">Cargando...</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Mis Empresas</h1>
        <Link
          to="/empresas/nueva"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          + Nueva Empresa
        </Link>
      </div>

      {empresas.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">No tienes empresas configuradas.</p>
          <Link to="/empresas/nueva" className="text-blue-600 hover:underline">
            Crea tu primera empresa
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {empresas.map(empresa => {
            const esActiva = user?.empresa_activa?.id === empresa.id
            return (
              <div
                key={empresa.id}
                className={`bg-white rounded-xl border-2 p-5 flex items-center justify-between ${
                  esActiva ? 'border-blue-500' : 'border-gray-200'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-semibold text-gray-900">{empresa.nombre}</h2>
                    {esActiva && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                        Activa
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500">NIT: {empresa.nit}</p>
                  <p className="text-sm text-gray-500">
                    {empresa.ciudad} · {empresa.regimen === 'comun' ? 'Régimen Común' : 'Régimen Simplificado'}
                  </p>
                  {empresa.rol && (
                    <span className="inline-block mt-1 text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                      Rol: {empresa.rol}
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => abrirUsuarios(empresa)}
                    className="text-sm border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50"
                  >
                    Usuarios
                  </button>
                  {!esActiva && (
                    <button
                      onClick={() => handleCambiar(empresa.id)}
                      disabled={cambiando === empresa.id}
                      className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      {cambiando === empresa.id ? 'Cambiando...' : 'Cambiar a esta'}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Modal Usuarios */}
      {modalUsuarios && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Usuarios — {modalUsuarios.nombre}</h3>
              <button onClick={() => setModalUsuarios(null)} className="text-gray-400 hover:text-gray-600 text-xl">
                ×
              </button>
            </div>
            {usuariosEmpresa.length === 0 ? (
              <p className="text-gray-500 text-sm">Sin usuarios registrados.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-2">Usuario</th>
                    <th className="pb-2">Rol</th>
                    <th className="pb-2">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {usuariosEmpresa.map(ue => (
                    <tr key={ue.id} className="border-b last:border-0">
                      <td className="py-2">{ue.usuario_nombre || ue.usuario_username}</td>
                      <td className="py-2 capitalize">{ue.rol}</td>
                      <td className="py-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${ue.activo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                          {ue.activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <button
              onClick={() => setModalUsuarios(null)}
              className="mt-4 w-full text-center text-sm text-gray-500 hover:text-gray-700"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
