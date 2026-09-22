import { User, CheckCircle, XCircle, AlertTriangle, TrendingUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { RecognitionResult } from '../types/facial';

interface FaceResultCardProps {
  name: string;
  photo: string;
  subtitle?: string;
  result?: RecognitionResult | null;
  coincide?: boolean;
  clasificacion?: string | null;
}

const classificationLabels: Record<string, { label: string; color: string }> = {
  humano_real: { label: 'Humano Real', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  no_real: { label: 'No Real', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
};

export function FaceResultCard({ name, photo, subtitle, result, coincide, clasificacion }: FaceResultCardProps) {
  const navigate = useNavigate();

  const handleVerProbabilidades = () => {
    if (!result) return;
    navigate('/probabilidades', {
      state: {
        similitud: result.similitud,
        distancia: result.distancia,
        calidad_imagen: result.calidad_imagen || 0,
        iluminacion: result.iluminacion || 0,
      },
    });
  };

  if (result) {
    return (
      <div
        className={`rounded-xl p-6 border-2 ${
          coincide
            ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
            : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
        }`}
      >
        <div className="flex items-center gap-3 mb-4">
          {coincide ? (
            <CheckCircle className="text-green-600 dark:text-green-400" size={28} />
          ) : (
            <XCircle className="text-red-600 dark:text-red-400" size={28} />
          )}
          <h3 className="text-xl font-bold text-gray-800 dark:text-[var(--text-h)]">
            {coincide ? 'Rostro identificado' : 'Sin coincidencia'}
          </h3>
        </div>

        {clasificacion && (
          <div className="mb-4">
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${classificationLabels[clasificacion]?.color || 'bg-gray-100 text-gray-600'}`}>
              {classificationLabels[clasificacion]?.label || clasificacion}
            </span>
          </div>
        )}

        {coincide && result.nombre && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-gray-700 dark:text-[var(--text-h)]">
              <User size={18} />
              <span className="font-semibold">{result.nombre}</span>
            </div>
            {result.email && (
              <div className="text-sm text-gray-500 dark:text-[var(--text)] ml-7">{result.email}</div>
            )}
            <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
              <div className="bg-white dark:bg-[var(--code-bg)] rounded-lg p-3">
                <span className="text-gray-500 dark:text-[var(--text)]">Similitud</span>
                <p className="font-mono font-bold text-gray-800 dark:text-[var(--text-h)]">{(result.similitud * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-white dark:bg-[var(--code-bg)] rounded-lg p-3">
                <span className="text-gray-500 dark:text-[var(--text)]">Distancia</span>
                <p className="font-mono font-bold text-gray-800 dark:text-[var(--text-h)]">{result.distancia.toFixed(4)}</p>
              </div>
              <div className="bg-white dark:bg-[var(--code-bg)] rounded-lg p-3">
                <span className="text-gray-500 dark:text-[var(--text)]">Umbral</span>
                <p className="font-mono font-bold text-gray-800 dark:text-[var(--text-h)]">{result.umbral}</p>
              </div>
              {result.probabilidad_calibrada !== undefined && result.probabilidad_calibrada !== null && (
                <div className="bg-white dark:bg-[var(--code-bg)] rounded-lg p-3">
                  <span className="text-gray-500 dark:text-[var(--text)]">Probabilidad</span>
                  <p className="font-mono font-bold text-blue-600 dark:text-blue-400">{(result.probabilidad_calibrada * 100).toFixed(1)}%</p>
                </div>
              )}
              {result.calidad_imagen !== undefined && (
                <div className="bg-white dark:bg-[var(--code-bg)] rounded-lg p-3">
                  <span className="text-gray-500 dark:text-[var(--text)]">Calidad imagen</span>
                  <p className="font-mono font-bold text-gray-800 dark:text-[var(--text-h)]">{(result.calidad_imagen * 100).toFixed(1)}%</p>
                </div>
              )}
              {result.iluminacion !== undefined && (
                <div className="bg-white dark:bg-[var(--code-bg)] rounded-lg p-3">
                  <span className="text-gray-500 dark:text-[var(--text)]">Iluminacion</span>
                  <p className="font-mono font-bold text-gray-800 dark:text-[var(--text-h)]">{(result.iluminacion * 100).toFixed(1)}%</p>
                </div>
              )}
            </div>
            <button
              onClick={handleVerProbabilidades}
              className="mt-3 flex items-center gap-2 px-4 py-2 text-sm text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
            >
              <TrendingUp size={16} />
              Ver en Probabilidades
            </button>
          </div>
        )}

        {!coincide && (
          <div className="flex items-start gap-2 mt-2 text-gray-600 dark:text-[var(--text)]">
            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
            <p className="text-sm">{result.detail || 'No se encontro una coincidencia en la base de datos.'}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="face-result-card">
      <div className="face-result-photo">
        {photo ? (
          <img src={photo} alt={name} />
        ) : (
          <div className="face-result-placeholder">
            <User size={32} />
          </div>
        )}
      </div>
      <div className="face-result-info">
        <span className="face-result-name">{name}</span>
        {subtitle && <span className="face-result-subtitle">{subtitle}</span>}
      </div>
    </div>
  );
}
