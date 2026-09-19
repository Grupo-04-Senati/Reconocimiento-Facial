import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from 'recharts'
import type { HistorialEntry } from '../types/facial'

interface ProbabilityChartProps {
  data: HistorialEntry[]
  type?: 'bar' | 'line'
}

const ProbabilityChart: React.FC<ProbabilityChartProps> = ({
  data,
  type = 'bar',
}) => {
  const chartData = data
    .slice(0, 20)
    .reverse()
    .map((entry, index) => ({
      name: `#${index + 1}`,
      similitud: Math.round(entry.similitud * 100),
      probabilidad: entry.probabilidad_calibrada
        ? Math.round(entry.probabilidad_calibrada * 100)
        : 0,
      coincide: entry.coincide ? 1 : 0,
    }))

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 bg-gray-50 rounded-xl">
        No hay datos de reconocimiento disponibles
      </div>
    )
  }

  return (
    <div className="w-full h-80 bg-white rounded-xl p-4 border border-gray-200">
      <ResponsiveContainer width="100%" height="100%">
        {type === 'bar' ? (
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" fontSize={12} />
            <YAxis domain={[0, 100]} fontSize={12} />
            <Tooltip
              formatter={(value: number) => [`${value}%`, '']}
              labelFormatter={(label) => `Reconocimiento ${label}`}
            />
            <Legend />
            <Bar
              dataKey="similitud"
              name="Similitud"
              fill="#3b82f6"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="probabilidad"
              name="Probabilidad"
              fill="#8b5cf6"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        ) : (
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" fontSize={12} />
            <YAxis domain={[0, 100]} fontSize={12} />
            <Tooltip
              formatter={(value: number) => [`${value}%`, '']}
              labelFormatter={(label) => `Reconocimiento ${label}`}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="similitud"
              name="Similitud"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="probabilidad"
              name="Probabilidad"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}

export default ProbabilityChart
