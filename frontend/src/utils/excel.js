export async function descargarExcel(path, filename) {
  const token = localStorage.getItem('access_token')
  const baseURL = import.meta.env.VITE_API_URL || ''
  const url = `${baseURL}/api${path}`
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || 'Error al exportar')
  }
  const blob = await response.blob()
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(link.href)
}
