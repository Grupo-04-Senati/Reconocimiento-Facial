import React from 'react'

interface SimilarityBarProps {
  value: number
  label: string
  color?: 'blue' | 'green' | 'purple' | 'red'
}

const colorMap = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  purple: 'bg-purple-500',
  red: 'bg-red-500',
}

const SimilarityBar: React.FC<SimilarityBarProps> = ({
  value,
  label,
  color = 'blue',
}) => {
  const percentage = Math.round(value * 100)

  return (
    <div className="w-full">
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-bold text-gray-900">{percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`${colorMap[color]} h-full rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}

export default SimilarityBar
