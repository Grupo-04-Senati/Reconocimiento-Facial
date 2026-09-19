import axios from 'axios'
import type {
  Persona,
  RecognitionResponse,
  HistorialEntry,
  PredictionResponse,
} from '../types/facial.ts'

// En Vercel, frontend y backend comparten el mismo dominio.
// Las peticiones /api/* se redirigen al backend via vercel.json rewrites.
// En desarrollo local, el proxy de vite redirige /api a localhost:8000.
const API_URL = import.meta.env.VITE_API_BASE_URL || ''

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
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
