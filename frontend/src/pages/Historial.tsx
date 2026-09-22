import { useState, useEffect } from 'react';
import { History, RefreshCw, Filter, Download } from 'lucide-react';
import { dataService } from '../services/dataService';
import { listarPersonas, exportarHistorialCSV } from '../services/api';
import type { HistorialEntry } from '../types/facial';

interface Persona { id: string; nombre: string; email: string }

export function Historial() {
  const [historial, setHistorial] = useState<HistorialEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [filterPersona, setFilterPersona] = useState('');
  const [downloading, setDownloading] = useState(false);

  const fetchHistorial = async () => {
    setLoading(true);
    try {
      const data = await dataService.obtenerHistorial();
      setHistorial(data.historial || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistorial();
    listarPersonas().then((d) => setPersonas(d.personas || [])).catch(() => {});
  }, []);

  const handleExportCSV = async () => {
    setDownloading(true);
    try {
      const blob = await exportarHistorialCSV();
      const url = URL.createObjectURL(new Blob([blob], { type: 'text/csv' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `historial_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting CSV:', err);
    } finally {
      setDownloading(false);
    }
  };

  const filteredHistorial = (() => {
    const base = filterPersona
      ? historial.filter((e) => e.persona_id === filterPersona)
      : historial;
    const byPersona = new Map<string, typeof base[0]>();
    for (const entry of base) {
      const key = entry.persona_id || 'desconocido';
      const existing = byPersona.get(key);
      if (!existing || new Date(entry.created_at) > new Date(existing.created_at)) {
        byPersona.set(key, entry);
      }
    }
    return Array.from(byPersona.values()).sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  })();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-[var(--text-h)]">Historial</h1>
          <p className="text-gray-600 dark:text-[var(--text)]">Registro de reconocimientos realizados</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExportCSV}
            disabled={downloading || filteredHistorial.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors text-sm"
          >
            <Download size={16} />
            {downloading ? 'Exportando...' : 'CSV'}
          </button>
          <button
            onClick={fetchHistorial}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors text-sm"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Actualizar
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Filter size={16} className="text-gray-500 dark:text-[var(--text)]" />
        <select
          value={filterPersona}
          onChange={(e) => setFilterPersona(e.target.value)}
          className="px-3 py-2 bg-white dark:bg-[var(--code-bg)] border border-gray-200 dark:border-[var(--border)] rounded-lg text-sm text-gray-700 dark:text-[var(--text)] focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todas las personas</option>
          {personas.map((p) => (
            <option key={p.id} value={p.id}>{p.nombre}</option>
          ))}
        </select>
        {filterPersona && (
          <span className="text-xs text-gray-500 dark:text-[var(--text)]">
            {filteredHistorial.length} registros
          </span>
        )}
      </div>

      <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl border border-gray-200 dark:border-[var(--border)] shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-[var(--border)]">
          <h2 className="text-lg font-bold text-gray-800 dark:text-[var(--text-h)]">Registros recientes ({filteredHistorial.length})</h2>
        </div>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : filteredHistorial.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-gray-500 dark:text-[var(--text)]">
            <History size={40} className="opacity-30" />
            <p>{filterPersona ? 'No hay registros para esta persona' : 'No hay registros de reconocimiento'}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-[var(--code-bg)]">
                <tr>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Fecha</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Persona</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Similitud</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Distancia</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Umbral</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Probabilidad</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Resultado</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-[var(--border)]">
                {filteredHistorial.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50 dark:hover:bg-[var(--bg)]">
                    <td className="px-3 py-3 text-xs text-gray-600 dark:text-[var(--text)]">
                      {new Date(entry.created_at).toLocaleString('es-PE')}
                    </td>
                    <td className="px-3 py-3 text-sm font-medium text-gray-800 dark:text-[var(--text-h)]">
                      {entry.personas?.nombre || 'No reconocido'}
                    </td>
                    <td className="px-3 py-3 text-sm font-mono text-gray-600 dark:text-[var(--text)]">
                      {(entry.similitud * 100).toFixed(1)}%
                    </td>
                    <td className="px-3 py-3 text-sm font-mono text-gray-600 dark:text-[var(--text)]">
                      {entry.distancia.toFixed(4)}
                    </td>
                    <td className="px-3 py-3 text-sm font-mono text-gray-600 dark:text-[var(--text)]">
                      {(entry.umbral * 100).toFixed(0)}%
                    </td>
                    <td className="px-3 py-3 text-sm font-mono text-gray-600 dark:text-[var(--text)]">
                      {entry.probabilidad_calibrada
                        ? `${(entry.probabilidad_calibrada * 100).toFixed(1)}%`
                        : '-'}
                    </td>
                    <td className="px-3 py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          entry.coincide
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                            : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                        }`}
                      >
                        {entry.coincide ? 'Coincidencia' : 'Sin coincidencia'}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      {(entry as HistorialEntry & { resultado_real?: boolean | null; clasificacion?: string | null; coincide?: boolean }).resultado_real != null ? (() => {
                        const e = entry as HistorialEntry & { resultado_real?: boolean | null; clasificacion?: string | null };
                        const isReal = e.resultado_real === true || e.clasificacion === 'humano_real';
                        return (
                          <span className={`text-xs font-medium ${isReal ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                            {isReal ? 'Humano Real' : 'No Real'}
                          </span>
                        );
                      })() : (
                        <span className="text-xs text-gray-400 dark:text-[var(--text)]">Sin confirmar</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
