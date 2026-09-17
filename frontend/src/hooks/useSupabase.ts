import { useState, useCallback } from 'react'
import { supabase } from '../services/supabaseClient'

export function useSupabase() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const uploadImage = useCallback(
    async (bucket: string, path: string, file: File) => {
      setLoading(true)
      setError(null)
      try {
        const { data, error } = await supabase.storage
          .from(bucket)
          .upload(path, file, {
            contentType: file.type,
          })
        if (error) throw error
        return data
      } catch (err: any) {
        setError(err.message)
        return null
      } finally {
        setLoading(false)
      }
    },
    []
  )

  const getImageUrl = useCallback(
    (bucket: string, path: string) => {
      const { data } = supabase.storage.from(bucket).getPublicUrl(path)
      return data.publicUrl
    },
    []
  )

  const query = useCallback(
    async <T = any>(
      table: string,
      operation: 'select' | 'insert' | 'update' | 'delete',
      filters?: Record<string, any>,
      payload?: any
    ) => {
      setLoading(true)
      setError(null)
      try {
        let result
        switch (operation) {
          case 'select':
            result = await supabase.from(table).select('*').match(filters || {})
            break
          case 'insert':
            result = await supabase.from(table).insert(payload)
            break
          case 'update':
            result = await supabase.from(table).update(payload).match(filters || {})
            break
          case 'delete':
            result = await supabase.from(table).delete().match(filters || {})
            break
        }
        if (result?.error) throw result.error
        return result?.data as T
      } catch (err: any) {
        setError(err.message)
        return null
      } finally {
        setLoading(false)
      }
    },
    []
  )

  return { loading, error, uploadImage, getImageUrl, query }
}
