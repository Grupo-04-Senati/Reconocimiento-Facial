import { supabase } from '../lib/supabase'
import type {
  Persona,
  HistorialEntry,
  Stats,
} from '../types/facial'

export const supabaseService = {
  async listarPersonas(): Promise<Persona[]> {
    const { data, error } = await supabase
      .from('personas')
      .select('*')
      .eq('activo', true)
      .order('created_at', { ascending: false })

    if (error) throw error
    return data || []
  },

  async obtenerHistorial(): Promise<HistorialEntry[]> {
    const { data, error } = await supabase
      .from('recognition_logs')
      .select('*, personas(nombre)')
      .order('created_at', { ascending: false })
      .limit(100)

    if (error) throw error
    return data || []
  },

  async obtenerEstadisticas(): Promise<Stats> {
    const { count: total } = await supabase
      .from('recognition_logs')
      .select('*', { count: 'exact', head: true })

    const { count: positivos } = await supabase
      .from('recognition_logs')
      .select('*', { count: 'exact', head: true })
      .eq('coincide', true)

    const totalReconocimientos = total || 0
    const coincidenciasPositivas = positivos || 0

    return {
      total_reconocimientos: totalReconocimientos,
      coincidencias_positivas: coincidenciasPositivas,
      tasa_exito: totalReconocimientos > 0
        ? coincidenciasPositivas / totalReconocimientos
        : 0,
    }
  },

  async registrarPersona(nombre: string, email: string) {
    const { data, error } = await supabase
      .from('personas')
      .insert({ nombre, email, activo: true })
      .select('id')
      .single()

    if (error) throw error
    return data
  },

  async eliminarPersona(personaId: string) {
    const { error } = await supabase
      .from('personas')
      .delete()
      .eq('id', personaId)

    if (error) throw error
  },
}
