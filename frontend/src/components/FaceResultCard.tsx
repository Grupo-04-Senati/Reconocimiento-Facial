import React from 'react'
import { User, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import type { RecognitionResult } from '../types/facial'
import SimilarityBar from './SimilarityBar'

interface FaceResultCardProps {
  result: RecognitionResult | null
  coincide: boolean
}

const FaceResultCard: React.FC<FaceResultCardProps> = ({ result, coincide }) => {
  return (
    <div
      className={`rounded-xl p-6 border-2 ${
        coincide
          ? 'border-green-200 bg-green-50'
          : 'border-red-200 bg-red-50'
      }`}
    >
      <div className="flex items-center gap-3 mb-4">
        {coincide ? (
          <CheckCircle className="text-green-600" size={28} />
        ) : (
          <XCircle className="text-red-600" size={28} />
        )}
        <h3 className="text-xl font-bold text-gray-800">
          {coincide ? 'Rostro identificado' : 'Sin coincidencia'}
        </h3>
      </div>

      {result && coincide && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-gray-700">
            <User size={18} />
            <span className="font-semibold">{result.nombre}</span>
          </div>

          <SimilarityBar value={result.similitud} label="Similitud" />

          {result.probabilidad_calibrada !== undefined && (
            <SimilarityBar
              value={result.probabilidad_calibrada}
              label="Probabilidad calibrada"
              color="purple"
            />
          )}

          <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
            <div className="bg-white rounded-lg p-3">
              <span className="text-gray-500">Distancia</span>
              <p className="font-mono font-bold text-gray-800">
                {result.distancia.toFixed(4)}
              </p>
            </div>
            <div className="bg-white rounded-lg p-3">
              <span className="text-gray-500">Umbral</span>
              <p className="font-mono font-bold text-gray-800">
                {result.umbral}
              </p>
            </div>
            {result.calidad_imagen !== undefined && (
              <div className="bg-white rounded-lg p-3">
                <span className="text-gray-500">Calidad imagen</span>
                <p className="font-mono font-bold text-gray-800">
                  {(result.calidad_imagen * 100).toFixed(1)}%
                </p>
              </div>
            )}
            {result.iluminacion !== undefined && (
              <div className="bg-white rounded-lg p-3">
                <span className="text-gray-500">Iluminación</span>
                <p className="font-mono font-bold text-gray-800">
                  {(result.iluminacion * 100).toFixed(1)}%
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {!coincide && (
        <div className="flex items-start gap-2 mt-2 text-gray-600">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <p className="text-sm">
            {result?.detail || 'No se encontró una coincidencia en la base de datos.'}
          </p>
        </div>
      )}
    </div>
  )
}

export default FaceResultCard
