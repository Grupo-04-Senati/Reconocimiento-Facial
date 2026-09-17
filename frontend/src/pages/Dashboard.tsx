import React, { useState, useEffect } from 'react'
import { Activity, Users, Scan, BarChart3, AlertCircle } from 'lucide-react'
import { healthCheck, obtenerEstadisticas, obtenerEstadoModelos } from '../services/api'

const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [models, setModels] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthRes, statsRes, modelsRes] = await Promise.allSettled([
          healthCheck(),
          obtenerEstadisticas(),
          obtenerEstadoModelos(),
        ])
        if (healthRes.status === 'fulfilled') setHealth(healthRes.value)
        if (statsRes.status === 'fulfilled') setStats(statsRes.value)
        if (modelsRes.status === 'fulfilled') setModels(modelsRes.value)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="text-blue-600" size={22} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Estado del Sistema</p>
              <p className="text-lg font-bold text-green-600">
                {health?.status === 'healthy' ? 'Activo' : 'Inactivo'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Scan className="text-purple-600" size={22} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Reconocimientos</p>
              <p className="text-lg font-bold text-gray-800">
                {stats?.estadisticas?.total_reconocimientos ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Users className="text-green-600" size={22} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Tasa de Éxito</p>
              <p className="text-lg font-bold text-gray-800">
                {stats?.estadisticas?.tasa_exito
                  ? `${(stats.estadisticas.tasa_exito * 100).toFixed(1)}%`
                  : '0%'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <BarChart3 className="text-orange-600" size={22} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Coincidencias</p>
              <p className="text-lg font-bold text-gray-800">
                {stats?.estadisticas?.coincidencias_positivas ?? 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Estado de Modelos</h2>
        <div className="space-y-3">
          {models?.models &&
            Object.entries(models.models).map(([key, model]: [string, any]) => (
              <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-800">{model.name}</p>
                  <p className="text-sm text-gray-500">{model.type}</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    model.loaded
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {model.loaded ? 'Cargado' : 'No disponible'}
                </span>
              </div>
            ))}
        </div>
      </div>

      {!health && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="text-yellow-600 mt-0.5" size={20} />
          <div>
            <p className="font-medium text-yellow-800">Backend no disponible</p>
            <p className="text-sm text-yellow-600">
              Asegúrate de que el servidor backend esté ejecutándose en http://localhost:8000
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
