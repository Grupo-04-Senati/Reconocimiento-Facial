import React, { useState } from 'react'
import { Scan } from 'lucide-react'
import CameraCapture from '../components/CameraCapture'
import FaceResultCard from '../components/FaceResultCard'
import { reconocerRostro } from '../services/api'
import type { RecognitionResult } from '../types/facial'

const Reconocimiento: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{
    coincide: boolean
    data: RecognitionResult | null
  } | null>(null)

  const handleCapture = async (imageSrc: string) => {
    setLoading(true)
    setResult(null)
    try {
      const formData = new FormData()
      const response = await fetch(imageSrc)
      const blob = await response.blob()
      formData.append('imagen', blob, 'face.jpg')

      const data = await reconocerRostro(formData)
      setResult({
        coincide: data.coincide,
        data: data.resultado,
      })
    } catch (err: any) {
      console.error('Recognition error:', err)
      setResult({
        coincide: false,
        data: null,
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Reconocimiento Facial</h1>
      <p className="text-gray-600">
        Capture o suba una imagen para identificar una persona en el sistema.
      </p>

      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        {loading ? (
          <div className="flex flex-col items-center gap-4 py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            <p className="text-gray-600">Analizando rostro...</p>
          </div>
        ) : (
          <CameraCapture onCapture={handleCapture} disabled={loading} />
        )}
      </div>

      {result && (
        <FaceResultCard result={result.data} coincide={result.coincide} />
      )}
    </div>
  )
}

export default Reconocimiento
