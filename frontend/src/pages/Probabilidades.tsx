import React, { useState } from 'react'
import { TrendingUp, Calculator } from 'lucide-react'
import { predecirProbabilidad } from '../services/api'
import SimilarityBar from '../components/SimilarityBar'

const Probabilidades: React.FC = () => {
  const [similitud, setSimilitud] = useState(0.85)
  const [distancia, setDistancia] = useState(0.35)
  const [calidad, setCalidad] = useState(0.9)
  const [iluminacion, setIluminacion] = useState(0.7)
  const [prediction, setPrediction] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)

  const handlePredict = async () => {
    setLoading(true)
    try {
      const data = await predecirProbabilidad({
        similitud,
        distancia,
        calidad_imagen: calidad,
        iluminacion,
      })
      setPrediction(data.probabilidad_calibrada)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Análisis de Probabilidades</h1>
      <p className="text-gray-600">
        Ajuste los parámetros para predecir la probabilidad de coincidencia.
      </p>

      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm space-y-5">
        <div>
          <label className="flex justify-between text-sm font-medium text-gray-700 mb-1">
            <span>Similitud</span>
            <span className="font-mono">{similitud.toFixed(2)}</span>
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={similitud}
            onChange={(e) => setSimilitud(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
        </div>

        <div>
          <label className="flex justify-between text-sm font-medium text-gray-700 mb-1">
            <span>Distancia</span>
            <span className="font-mono">{distancia.toFixed(2)}</span>
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.01"
            value={distancia}
            onChange={(e) => setDistancia(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
        </div>

        <div>
          <label className="flex justify-between text-sm font-medium text-gray-700 mb-1">
            <span>Calidad de imagen</span>
            <span className="font-mono">{calidad.toFixed(2)}</span>
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={calidad}
            onChange={(e) => setCalidad(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
        </div>

        <div>
          <label className="flex justify-between text-sm font-medium text-gray-700 mb-1">
            <span>Iluminación</span>
            <span className="font-mono">{iluminacion.toFixed(2)}</span>
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={iluminacion}
            onChange={(e) => setIluminacion(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
        </div>

        <button
          onClick={handlePredict}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors font-medium"
        >
          <Calculator size={20} />
          {loading ? 'Calculando...' : 'Predecir probabilidad'}
        </button>
      </div>

      {prediction !== null && (
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="text-purple-600" size={22} />
            <h2 className="text-xl font-bold text-gray-800">Resultado</h2>
          </div>
          <SimilarityBar
            value={prediction}
            label="Probabilidad calibrada"
            color="purple"
          />
          <div className="text-center">
            <p className="text-4xl font-bold text-gray-800">
              {(prediction * 100).toFixed(1)}%
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Probabilidad de coincidencia real
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default Probabilidades
