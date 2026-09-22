import { supabase } from './supabaseClient'

export const authService = {
  async signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    return { data, error }
  },

  async signUp(email: string, password: string) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    })
    return { data, error }
  },

  async signOut() {
    const { error } = await supabase.auth.signOut()
    return { error }
  },

  async getSession() {
    const { data, error } = await supabase.auth.getSession()
    return { data, error }
  },

  async getUser() {
    const { data, error } = await supabase.auth.getUser()
    return { data, error }
  },
}
