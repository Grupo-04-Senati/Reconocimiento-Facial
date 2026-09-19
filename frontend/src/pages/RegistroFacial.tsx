import React, { useState } from 'react'
import { UserPlus, CheckCircle, XCircle } from 'lucide-react'
import CameraCapture from '../components/CameraCapture'
import { registrarPersona, healthCheck } from '../services/api'
import { supabaseService } from '../services/supabaseService'

const RegistroFacial: React.FC = () => {
  const [nombre, setNombre] = useState('')
  const [email, setEmail] = useState('')
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)

  const handleCapture = (imageSrc: string) => {
    setCapturedImage(imageSrc)
    setResult(null)
  }

  const handleSubmit = async () => {
    if (!nombre || !email || !capturedImage) {
      setResult({ success: false, message: 'Complete todos los campos y capture una imagen' })
      return
    }

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('nombre', nombre)
      formData.append('email', email)

      const response = await fetch(capturedImage)
      const blob = await response.blob()
      formData.append('imagen', blob, 'face.jpg')

      let data
      try {
        await healthCheck()
        data = await registrarPersona(formData)
      } catch {
        await supabaseService.registrarPersona(nombre, email)
        data = { message: `${nombre} registrado en Supabase (sin embedding facial - requiere backend)` }
      }
      setResult({ success: true, message: data.message })
      setNombre('')
      setEmail('')
      setCapturedImage(null)
    } catch (err: any) {
      const msg = err.message || err.response?.data?.detail || 'Error al registrar persona'
      setResult({ success: false, message: msg })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Registro Facial</h1>
      <p className="text-gray-600">
        Registra un nuevo rostro en el sistema. Capture una imagen clara del rostro.
      </p>

      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo</label>
          <input
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Ej: Carlos García"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Correo electrónico</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="carlos@senati.pe"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Captura del rostro</label>
          <CameraCapture onCapture={handleCapture} disabled={loading} />
          {capturedImage && (
            <p className="text-sm text-green-600 mt-2 text-center">
              Imagen capturada correctamente
            </p>
          )}
        </div>

        <button
          onClick={handleSubmit}
          disabled={!nombre || !email || !capturedImage || loading}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          <UserPlus size={20} />
          {loading ? 'Registrando...' : 'Registrar persona'}
        </button>

        {result && (
          <div
            className={`flex items-start gap-3 p-4 rounded-lg ${
              result.success
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            {result.success ? (
              <CheckCircle className="text-green-600 mt-0.5" size={20} />
            ) : (
              <XCircle className="text-red-600 mt-0.5" size={20} />
            )}
            <p className={result.success ? 'text-green-800' : 'text-red-800'}>
              {result.message}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default RegistroFacial
