import React, { useState, useEffect } from 'react'
import { History, RefreshCw } from 'lucide-react'
import { dataService } from '../services/dataService'
import ProbabilityChart from '../components/ProbabilityChart'
import type { HistorialEntry } from '../types/facial'

const Historial: React.FC = () => {
  const [historial, setHistorial] = useState<HistorialEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [chartType, setChartType] = useState<'bar' | 'line'>('bar')

  const fetchHistorial = async () => {
    setLoading(true)
    try {
      const data = await dataService.obtenerHistorial()
      setHistorial(data.historial || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistorial()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Historial</h1>
          <p className="text-gray-600">Registro de reconocimientos realizados</p>
        </div>
        <button
          onClick={fetchHistorial}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Actualizar
        </button>
      </div>

      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-800">Gráfico de Reconocimientos</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setChartType('bar')}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                chartType === 'bar'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Barras
            </button>
            <button
              onClick={() => setChartType('line')}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                chartType === 'line'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Línea
            </button>
          </div>
        </div>
        <ProbabilityChart data={historial} type={chartType} />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-800">Registros recientes</h2>
        </div>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : historial.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-gray-500">
            <History size={40} className="opacity-30" />
            <p>No hay registros de reconocimiento</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Persona</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Similitud</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Probabilidad</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resultado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {historial.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(entry.created_at).toLocaleString('es-PE')}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-800">
                      {entry.personas?.nombre || 'Desconocido'}
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-600">
                      {(entry.similitud * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-600">
                      {entry.probabilidad_calibrada
                        ? `${(entry.probabilidad_calibrada * 100).toFixed(1)}%`
                        : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          entry.coincide
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {entry.coincide ? 'Coincidencia' : 'Sin coincidencia'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default Historial
