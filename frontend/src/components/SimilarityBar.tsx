interface SimilarityBarProps {
  value: number;
}

export function SimilarityBar({ value }: SimilarityBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const color = clamped >= 80 ? '#22c55e' : clamped >= 50 ? '#f59e0b' : '#ef4444';
  const label = clamped >= 80 ? 'Alta' : clamped >= 50 ? 'Media' : 'Baja';

  return (
    <div className="similarity-bar-wrap">
      <div className="similarity-header">
        <span className="similarity-label">Similitud</span>
        <span className="similarity-value" style={{ color }}>{clamped}% - {label}</span>
      </div>
      <div className="similarity-track">
        <div className="similarity-fill" style={{ width: `${clamped}%`, background: color }} />
      </div>
    </div>
  );
}
