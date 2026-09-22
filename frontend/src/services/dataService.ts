import {
  healthCheck,
  listarPersonas as apiListarPersonas,
  eliminarPersona as apiEliminarPersona,
  obtenerHistorial as apiObtenerHistorial,
  obtenerEstadisticas as apiObtenerEstadisticas,
  obtenerEstadoModelos,
  predecirProbabilidad as apiPredecirProbabilidad,
  entrenarModelo as apiEntrenarModelo,
  obtenerMetricas as apiObtenerMetricas,
} from './api'
import { supabaseService } from './supabaseService'
import type { Persona, HistorialEntry, Stats } from '../types/facial'

let backendAvailable: boolean | null = null

async function isBackendAvailable(): Promise<boolean> {
  if (backendAvailable !== null) return backendAvailable
  try {
    await healthCheck()
    backendAvailable = true
  } catch {
    backendAvailable = false
  }
  return backendAvailable
}

export const dataService = {
  async listarPersonas(): Promise<{ success: boolean; personas: Persona[] }> {
    if (await isBackendAvailable()) {
      return apiListarPersonas()
    }
    const personas = await supabaseService.listarPersonas()
    return { success: true, personas }
  },

  async eliminarPersona(personaId: string) {
    if (await isBackendAvailable()) {
      return apiEliminarPersona(personaId)
    }
    await supabaseService.eliminarPersona(personaId)
    return { success: true, message: 'Persona eliminada' }
  },

  async obtenerHistorial(): Promise<{
    success: boolean
    historial: HistorialEntry[]
  }> {
    if (await isBackendAvailable()) {
      return apiObtenerHistorial()
    }
    const historial = await supabaseService.obtenerHistorial()
    return { success: true, historial }
  },

  async obtenerEstadisticas(): Promise<{
    success: boolean
    estadisticas: Stats
  }> {
    if (await isBackendAvailable()) {
      return apiObtenerEstadisticas()
    }
    const estadisticas = await supabaseService.obtenerEstadisticas()
    return { success: true, estadisticas }
  },

  async obtenerEstadoModelos() {
    if (await isBackendAvailable()) {
      return obtenerEstadoModelos()
    }
    return {
      success: true,
      models: {
        face_detection: { name: 'Modo Supabase directo', loaded: false, type: 'supabase_direct' },
        probability: { name: 'Modo Supabase directo', loaded: false, type: 'supabase_direct' },
      },
    }
  },

  async predecirProbabilidad(features: {
    similitud: number
    distancia: number
    calidad_imagen: number
    iluminacion: number
  }) {
    if (await isBackendAvailable()) {
      return apiPredecirProbabilidad(features)
    }
    const prob =
      features.similitud * 0.7 +
      features.calidad_imagen * 0.15 +
      features.iluminacion * 0.15
    return {
      success: true,
      probabilidad_calibrada: Math.round(Math.max(0, Math.min(1, prob)) * 1000) / 1000,
    }
  },

  async checkHealth() {
    if (await isBackendAvailable()) {
      return healthCheck()
    }
    return { status: 'healthy', service: 'Supabase Direct Mode', version: '1.0.0' }
  },

  async entrenarModelo() {
    if (await isBackendAvailable()) {
      return apiEntrenarModelo()
    }
    return { success: false, message: 'Entrenamiento requiere backend con InsightFace' }
  },

  async obtenerMetricas() {
    if (await isBackendAvailable()) {
      return apiObtenerMetricas()
    }
    return { success: true, trained: false, metrics: null }
  },

  resetBackendStatus() {
    backendAvailable = null
  },
}
