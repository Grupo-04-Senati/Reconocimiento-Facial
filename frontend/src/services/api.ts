import axios from 'axios'
import type {
  Persona,
  RecognitionResponse,
  HistorialEntry,
  PredictionResponse,
} from '../types/facial.ts'

// Backend en Railway (produccion) o localhost (desarrollo)
// Las rutas ya incluyen /api/, asi que baseURL NO lleva /api
const API_BASE = import.meta.env.VITE_API_URL || 'https://reconocimiento-facial-production-1b3a.up.railway.app'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
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
  const { data } = await api.post('/api/personas', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data as { success: boolean; persona_id: string; message: string }
}

export const guardarRostro = async (personaId: string, formData: FormData) => {
  const { data } = await api.post(`/api/personas/${personaId}/rostro`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data as { success: boolean; message: string; embedding_model: string }
}

export const listarPersonas = async (): Promise<{ success: boolean; personas: Persona[] }> => {
  const { data } = await api.get('/api/personas')
  return data
}

export const eliminarPersona = async (personaId: string) => {
  const { data } = await api.delete(`/api/personas/${personaId}`)
  return data
}

export const reconocerRostro = async (formData: FormData): Promise<RecognitionResponse> => {
  const { data } = await api.post('/api/reconocimiento', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
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
