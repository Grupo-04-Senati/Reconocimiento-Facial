import axios from 'axios'
import type {
  Persona,
  RecognitionResponse,
  HistorialEntry,
  PredictionResponse,
} from '../types/facial.ts'

// Backend en Railway (produccion) o localhost (desarrollo)
// Las rutas ya incluyen /api/, asi que baseURL NO lleva /api
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem('bd_session')
    if (raw) {
      const session = JSON.parse(raw)
      if (session?.token) {
        config.headers.Authorization = `Bearer ${session.token}`
      }
    }
  } catch {}
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('bd_session')
      window.location.href = '/login'
    }
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      console.warn('Request timeout, retrying...')
      return api.request(error.config)
    }
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const healthCheck = async () => {
  const { data } = await api.get('/api/health')
  return data
}

export const registrarPersona = async (formData: FormData) => {
  const { data } = await api.post('/api/personas', formData)
  return data as { success: boolean; persona_id: string; message: string }
}

export const guardarRostro = async (personaId: string, formData: FormData) => {
  const { data } = await api.post(`/api/personas/${personaId}/rostro`, formData)
  return data as { success: boolean; message: string; embedding_model: string }
}

export const listarPersonas = async (): Promise<{ success: boolean; personas: Persona[] }> => {
  const { data } = await api.get('/api/personas')
  return data
}

export const listarPersonasConEmbedding = async (): Promise<{ success: boolean; personas: Persona[] }> => {
  const { data } = await api.get('/api/personas/con-embedding')
  return data
}

export const eliminarPersona = async (personaId: string) => {
  const { data } = await api.delete(`/api/personas/${personaId}`)
  return data
}

export const reconocerRostro = async (formData: FormData): Promise<RecognitionResponse> => {
  const { data } = await api.post('/api/reconocimiento', formData)
  return data
}

export const obtenerHistorial = async (): Promise<{
  success: boolean
  historial: HistorialEntry[]
}> => {
  const { data } = await api.get('/api/reconocimiento/historial')
  return data
}

export const predecirProbabilidad = async (features: {
  similitud: number
  distancia: number
  calidad_imagen: number
  iluminacion: number
}): Promise<PredictionResponse> => {
  const { data } = await api.post('/api/probabilidades/prediccion', features)
  return data
}

export const obtenerEstadisticas = async () => {
  const { data } = await api.get('/api/probabilidades/estadisticas')
  return data
}

export const obtenerEstadoModelos = async () => {
  const { data } = await api.get('/api/modelos/status')
  return data
}

export const entrenarModelo = async () => {
  const { data } = await api.post('/api/modelos/entrenar')
  return data
}

export const obtenerMetricas = async () => {
  const { data } = await api.get('/api/modelos/metricas')
  return data
}

export const authLogin = async (email: string, password: string) => {
  const { data } = await api.post('/api/auth/login', { email, password })
  return data as { success: boolean; token?: string; user: { id: string; name: string; email: string; role: string } }
}

export const authRegister = async (name: string, email: string, password: string, role: string = 'operador') => {
  const { data } = await api.post('/api/auth/register', { name, email, password, role })
  return data as { success: boolean; user: { id: string; name: string; email: string; role: string } }
}

export const authListUsers = async () => {
  const { data } = await api.get('/api/auth/users')
  return data
}

export const authDeleteUser = async (userId: string) => {
  const { data } = await api.delete(`/api/auth/users/${userId}`)
  return data
}

export const authChangeRole = async (userId: string, role: string) => {
  const { data } = await api.patch(`/api/auth/users/${userId}/role`, { role })
  return data
}

export const confirmarResultado = async (logId: string, clasificacion: string) => {
  const { data } = await api.patch(`/api/reconocimiento/historial/${logId}/confirmar`, {
    clasificacion,
  })
  return data
}

export const autoConfirmarPendientes = async () => {
  const { data } = await api.post('/api/reconocimiento/auto-confirmar')
  return data
}

export const personasCount = async (): Promise<{ success: boolean; total: number }> => {
  const { data } = await api.get('/api/reconocimiento/personas-count')
  return data
}

export const obtenerHistorialReciente = async (limit = 20) => {
  const { data } = await api.get('/api/reconocimiento/historial', { params: { limit } })
  return data
}

export const borrarHistorial = async () => {
  const { data } = await api.delete('/api/reconocimiento/historial')
  return data
}

export const exportarHistorialCSV = async () => {
  const { data } = await api.get('/api/reconocimiento/historial/csv', { responseType: 'blob' as any })
  return data
}

export const ejecutarPrueba = async (formData: FormData) => {
  const { data } = await api.post('/api/probabilidades/prueba', formData, {
    timeout: 120000,
  })
  return data
}

export const comparar1N = async (personaId: string) => {
  const { data } = await api.post('/api/probabilidades/comparar-1n', {
    persona_id: personaId,
  }, { timeout: 30000 })
  return data
}

export const comparar1A1 = async (personaAId: string, personaBId: string) => {
  const { data } = await api.post('/api/probabilidades/comparar-1a1', {
    persona_a_id: personaAId,
    persona_b_id: personaBId,
  }, { timeout: 30000 })
  return data
}

export const datasetCount = async () => {
  const { data } = await api.get('/api/probabilidades/dataset-count')
  return data
}

export const predecirManual = async (similitud: number, calidad: number = 1.0, iluminacion: number = 1.0) => {
  const { data } = await api.post('/api/probabilidades/predecir-manual', {
    similitud,
    calidad_imagen: calidad,
    iluminacion,
  })
  return data
}

export const curvaSensibilidad = async () => {
  const { data } = await api.get('/api/probabilidades/curva-sensibilidad')
  return data
}

export const compararEscenarios = async () => {
  const { data } = await api.get('/api/probabilidades/comparar-escenarios')
  return data
}

export const modeloInfo = async () => {
  const { data } = await api.get('/api/probabilidades/modelo-info')
  return data
}

export const historialPruebas = async () => {
  const { data } = await api.get('/api/probabilidades/historial-pruebas')
  return data
}

export const dashboardStats = async () => {
  const { data } = await api.get('/api/dashboard/stats')
  return data
}

export const clasificacionPersonas = async () => {
  const { data } = await api.get('/api/modelos/clasificacion')
  return data
}

export const recalcularResultado = async () => {
  const { data } = await api.post('/api/modelos/recalcular-resultado')
  return data
}

export const limpiarDB = async (todo: boolean = false) => {
  const { data } = await api.post('/api/modelos/limpiar-db', { todo })
  return data
}

export const agregarMuestra = async (formData: FormData, resultadoReal: boolean) => {
  const { data } = await api.post(
    `/api/modelos/agregar-muestra?resultado_real=${resultadoReal}`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 },
  )
  return data
}
