import { useState, useEffect } from 'react';
import { Card } from '../components/Card';
import { comparar1N, comparar1A1, listarPersonasConEmbedding, predecirManual, curvaSensibilidad, compararEscenarios, modeloInfo } from '../services/api';
import { Target, CheckCircle, XCircle, Users, Zap, AlertTriangle, Brain } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell } from 'recharts';
import './Probabilidades.css';

interface Persona { id: string; nombre: string; email: string }

interface Resultado1N {
  persona_id: string;
  nombre: string;
  email: string;
  tipo?: string;
  similitud: number;
  distancia: number;
  calidad_imagen: number;
  iluminacion: number;
  probabilidad_calibrada: number | null;
  confianza: number;
  supera_umbral: boolean;
  num_embeddings: number;
}

interface Resultado1A1 {
  persona_a: { id: string; nombre: string; email: string };
  persona_b: { id: string; nombre: string; email: string };
  similitud: number;
  distancia: number;
  calidad_imagen: number;
  iluminacion: number;
  probabilidad_calibrada: number | null;
  confianza: number;
  supera_umbral: boolean;
  umbral: number;
}

interface ModeloInfo {
  trained: boolean;
  model_class?: string;
  n_records?: number;
  positivos?: number;
  negativos?: number;
  feature_importance?: Record<string, number>;
  pocos_datos?: boolean;
  message?: string;
}

interface SensitivityPoint {
  similitud: number;
  distancia: number;
  probabilidad: number;
}

interface EscenarioRow {
  similitud: string;
  buena_luz: number;
}

export function Probabilidades() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [modo, setModo] = useState<'1n' | '1a1' | 'manual'>('1n');

  const [personaOrigen, setPersonaOrigen] = useState('');
  const [result1N, setResult1N] = useState<{ ranking: Resultado1N[]; umbral: number; personaOrigen: { nombre: string; email: string } } | null>(null);

  const [personaA, setPersonaA] = useState('');
  const [personaB, setPersonaB] = useState('');
  const [result1A1, setResult1A1] = useState<Resultado1A1 | null>(null);

  const [similitud, setSimilitud] = useState(0.65);
  const [calidad, setCalidad] = useState(0.80);
  const [iluminacion, setIluminacion] = useState(0.70);
  const [manualResult, setManualResult] = useState<{ probabilidad: number; supera_umbral: boolean; confianza: number; distancia: number } | null>(null);
  const [manualLoading, setManualLoading] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [modelo, setModelo] = useState<ModeloInfo | null>(null);
  const [sensibilidad, setSensibilidad] = useState<SensitivityPoint[]>([]);
  const [escenarios, setEscenarios] = useState<EscenarioRow[]>([]);

  useEffect(() => {
    listarPersonasConEmbedding().then((d) => setPersonas(d.personas || [])).catch(() => {});
    modeloInfo().then((d) => setModelo(d)).catch(() => {});
    curvaSensibilidad().then((d) => setSensibilidad(d.points || [])).catch(() => {});
    compararEscenarios().then((d) => setEscenarios(d.escenarios || [])).catch(() => {});
  }, []);

  const handleComparar1N = async () => {
    if (!personaOrigen) return;
    setLoading(true);
    setError('');
    setResult1N(null);
    try {
      const data = await comparar1N(personaOrigen);
      setResult1N({
        ranking: data.ranking || [],
        umbral: data.umbral,
        personaOrigen: data.persona_origen,
      });
    } catch (err) {
      console.error('Error 1:N:', err);
      setError('Error al comparar. Verifica que el backend este activo.');
    } finally {
      setLoading(false);
    }
  };

  const handleComparar1A1 = async () => {
    if (!personaA || !personaB) return;
    setLoading(true);
    setError('');
    setResult1A1(null);
    try {
      const data = await comparar1A1(personaA, personaB);
      setResult1A1(data);
    } catch (err) {
      console.error('Error 1:1:', err);
      setError('Error al comparar. Verifica que el backend este activo.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualPredict = async () => {
    setManualLoading(true);
    try {
      const data = await predecirManual(similitud, calidad, iluminacion);
      setManualResult({ probabilidad: data.probabilidad_calibrada, supera_umbral: data.supera_umbral, confianza: data.confianza ?? 0, distancia: data.distancia ?? 0 });
    } catch (err) {
      console.error('Error manual predict:', err);
    } finally {
      setManualLoading(false);
    }
  };

  useEffect(() => {
    if (modo === 'manual') {
      handleManualPredict();
    }
  }, [similitud, calidad, iluminacion, modo]);

  const getSimColor = (sim: number, umbral: number) => {
    if (sim >= umbral) return 'text-green-600 dark:text-green-400';
    if (sim >= umbral * 0.8) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getBarColor = (sim: number, umbral: number) => {
    if (sim >= umbral) return 'bg-green-500';
    if (sim >= umbral * 0.8) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="probabilidades">
      <div className="prob-header">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-[var(--text-h)]">Laboratorio de Pruebas</h1>
        <p className="text-gray-600 dark:text-[var(--text)]">Comparacion en tiempo real entre personas registradas en la BD</p>
      </div>

      <div className="prob-mode-selector">
        <button
          className={`prob-mode-btn ${modo === '1n' ? 'active' : ''}`}
          onClick={() => { setModo('1n'); setResult1N(null); setResult1A1(null); setError(''); }}
        >
          <Users size={18} />
          <div>
            <span className="font-bold">1 a N</span>
            <span className="text-xs block opacity-70">Comparar persona contra todas</span>
          </div>
        </button>
        <button
          className={`prob-mode-btn ${modo === '1a1' ? 'active' : ''}`}
          onClick={() => { setModo('1a1'); setResult1N(null); setResult1A1(null); setError(''); }}
        >
          <Zap size={18} />
          <div>
            <span className="font-bold">1 a 1</span>
            <span className="text-xs block opacity-70">Comparar dos personas</span>
          </div>
        </button>
        <button
          className={`prob-mode-btn ${modo === 'manual' ? 'active' : ''}`}
          onClick={() => { setModo('manual'); setResult1N(null); setResult1A1(null); setError(''); }}
        >
          <Brain size={18} />
          <div>
            <span className="font-bold">Manual</span>
            <span className="text-xs block opacity-70">Ajustar sliders y predecir</span>
          </div>
        </button>
      </div>

      {(modo === '1n' || modo === '1a1') && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-sm text-blue-700 dark:text-blue-300">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <p>
            Aquí se comparan los <strong>vectores faciales ya guardados</strong> (embedding vs embedding). Como no hay una
            foto en vivo, la <strong>calidad e iluminación se fijan en 100%</strong> (su valor real solo se mide en la pestaña
            <strong> Reconocimiento</strong>). Se muestran las 4 variables del ML para el análisis completo.
          </p>
        </div>
      )}

      {/* ═══ 1:N MODE ═══ */}
      {modo === '1n' && (
        <div className="prob-grid">
          <Card title="Seleccionar persona">
            <div className="prob-config">
              <div className="prob-field">
                <label>Persona de origen</label>
                <select value={personaOrigen} onChange={(e) => { setPersonaOrigen(e.target.value); setResult1N(null); setError(''); }}>
                  <option value="">Seleccionar persona...</option>
                  {personas.map((p) => (
                    <option key={p.id} value={p.id}>{p.nombre} ({p.email})</option>
                  ))}
                </select>
              </div>
              <button className="prob-run-btn" onClick={handleComparar1N} disabled={!personaOrigen || loading}>
                <Target size={18} />
                {loading ? 'Comparando...' : 'Comparar con todas'}
              </button>
            </div>
          </Card>

          {result1N && (
            <Card title="Resultado">
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                    <div className="text-xs text-gray-500">Comparaciones</div>
                    <div className="font-bold">{result1N.ranking.length}</div>
                  </div>
                  <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                    <div className="text-xs text-gray-500">Coincidencias</div>
                    <div className="font-bold text-green-600">{result1N.ranking.filter((r) => r.supera_umbral).length}</div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 text-center">Umbral: {(result1N.umbral * 100).toFixed(0)}%</p>
              </div>
            </Card>
          )}
        </div>
      )}

      {modo === '1n' && result1N && result1N.ranking.length > 0 && (
        <Card title="Ranking de Similitud (1 a N)">
          <div className="space-y-2">
            {result1N.ranking.map((r, i) => (
              <div
                key={r.persona_id}
                className={`p-3 rounded-lg border transition-colors ${
                  r.supera_umbral
                    ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
                    : 'bg-white dark:bg-[var(--code-bg)] border-gray-100 dark:border-[var(--border)]'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-xs text-gray-400 w-6 font-mono">#{i + 1}</span>
                  <div className="flex-1">
                    <span className="font-medium text-sm text-gray-800 dark:text-[var(--text-h)]">{r.nombre}</span>
                    <span className={`ml-2 px-1.5 py-0.5 rounded text-[10px] font-semibold ${r.tipo === 'ia' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'}`}>
                      {r.tipo === 'ia' ? 'IA' : 'Real'}
                    </span>
                    <span className="text-xs text-gray-400 ml-2">{r.email}</span>
                  </div>
                  <div className="w-32 bg-gray-200 dark:bg-[var(--border)] rounded-full h-2.5">
                    <div className={`h-2.5 rounded-full ${getBarColor(r.similitud, result1N.umbral)}`} style={{ width: `${Math.min(r.similitud * 100, 100)}%` }} />
                  </div>
                  <span className={`text-sm font-mono w-16 text-right font-bold ${getSimColor(r.similitud, result1N.umbral)}`}>
                    {(r.similitud * 100).toFixed(1)}%
                  </span>
                  {r.supera_umbral ? <CheckCircle size={16} className="text-green-500" /> : <XCircle size={16} className="text-gray-300" />}
                </div>
                <div className="grid grid-cols-7 gap-2 ml-9">
                  <div className="text-center p-1.5 bg-gray-50 dark:bg-[var(--bg)] rounded">
                    <div className="text-[10px] text-gray-400 uppercase">Similitud</div>
                    <div className="text-xs font-mono font-bold">{(r.similitud * 100).toFixed(1)}%</div>
                  </div>
                  <div className="text-center p-1.5 bg-gray-50 dark:bg-[var(--bg)] rounded">
                    <div className="text-[10px] text-gray-400 uppercase">Distancia</div>
                    <div className="text-xs font-mono font-bold">{r.distancia.toFixed(4)}</div>
                  </div>
                  <div className="text-center p-1.5 bg-gray-50 dark:bg-[var(--bg)] rounded">
                    <div className="text-[10px] text-gray-400 uppercase">Calidad</div>
                    <div className="text-xs font-mono font-bold">{(r.calidad_imagen * 100).toFixed(0)}%</div>
                  </div>
                  <div className="text-center p-1.5 bg-gray-50 dark:bg-[var(--bg)] rounded">
                    <div className="text-[10px] text-gray-400 uppercase">Iluminacion</div>
                    <div className="text-xs font-mono font-bold">{(r.iluminacion * 100).toFixed(0)}%</div>
                  </div>
                  <div className="text-center p-1.5 bg-gray-50 dark:bg-[var(--bg)] rounded">
                    <div className="text-[10px] text-gray-400 uppercase">Probabilidad</div>
                    <div className="text-xs font-mono font-bold text-blue-600">{r.probabilidad_calibrada != null ? `${(r.probabilidad_calibrada * 100).toFixed(1)}%` : '-'}</div>
                  </div>
                  <div className="text-center p-1.5 bg-gray-50 dark:bg-[var(--bg)] rounded">
                    <div className="text-[10px] text-gray-400 uppercase">Confianza</div>
                    <div className="text-xs font-mono font-bold">{(r.confianza * 100).toFixed(1)}%</div>
                  </div>
                  <div className="text-center p-1.5 bg-gray-50 dark:bg-[var(--bg)] rounded">
                    <div className="text-[10px] text-gray-400 uppercase">Umbral</div>
                    <div className="text-xs font-mono font-bold">{(result1N.umbral * 100).toFixed(0)}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ═══ 1:1 MODE ═══ */}
      {modo === '1a1' && (
        <div className="prob-grid">
          <Card title="Seleccionar dos personas">
            <div className="prob-config">
              <div className="prob-field">
                <label>Persona A</label>
                <select value={personaA} onChange={(e) => { setPersonaA(e.target.value); setResult1A1(null); setError(''); }}>
                  <option value="">Seleccionar persona A...</option>
                  {personas.map((p) => (
                    <option key={p.id} value={p.id}>{p.nombre} ({p.email})</option>
                  ))}
                </select>
              </div>
              <div className="prob-field">
                <label>Persona B</label>
                <select value={personaB} onChange={(e) => { setPersonaB(e.target.value); setResult1A1(null); setError(''); }}>
                  <option value="">Seleccionar persona B...</option>
                  {personas.filter((p) => p.id !== personaA).map((p) => (
                    <option key={p.id} value={p.id}>{p.nombre} ({p.email})</option>
                  ))}
                </select>
              </div>
              <button className="prob-run-btn" onClick={handleComparar1A1} disabled={!personaA || !personaB || loading}>
                <Target size={18} />
                {loading ? 'Comparando...' : 'Comparar estas dos personas'}
              </button>
            </div>
          </Card>

          {result1A1 && (
            <Card title="Resultado de la comparacion">
              <div className="space-y-4">
                <div className={`flex items-center gap-3 p-4 rounded-lg ${result1A1.supera_umbral ? 'bg-green-50 dark:bg-green-900/20 border border-green-200' : 'bg-red-50 dark:bg-red-900/20 border border-red-200'}`}>
                  {result1A1.supera_umbral ? <CheckCircle size={28} className="text-green-600" /> : <XCircle size={28} className="text-red-600" />}
                  <div>
                    <span className={`text-lg font-bold ${result1A1.supera_umbral ? 'text-green-700' : 'text-red-700'}`}>
                      {result1A1.supera_umbral ? 'MISMA PERSONA' : 'PERSONAS DIFERENTES'}
                    </span>
                    <p className="text-sm text-gray-600">{result1A1.persona_a.nombre} vs {result1A1.persona_b.nombre}</p>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Similitud: {(result1A1.similitud * 100).toFixed(1)}%</span>
                    <span className="text-gray-400">Umbral: {(result1A1.umbral * 100).toFixed(0)}%</span>
                  </div>
                  <div className="relative w-full bg-gray-200 dark:bg-[var(--border)] rounded-full h-3">
                    <div className={`h-3 rounded-full ${result1A1.supera_umbral ? 'bg-green-500' : 'bg-red-500'}`} style={{ width: `${Math.min(result1A1.similitud * 100, 100)}%` }} />
                    <div className="absolute top-0 w-0.5 h-3 bg-gray-400" style={{ left: `${result1A1.umbral * 100}%` }} />
                  </div>
                </div>

                <div className="grid grid-cols-7 gap-2 text-center">
                  <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                    <div className="text-xs text-gray-500">Similitud</div>
                    <div className="font-bold">{(result1A1.similitud * 100).toFixed(1)}%</div>
                  </div>
                  <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                    <div className="text-xs text-gray-500">Distancia</div>
                    <div className="font-bold">{result1A1.distancia.toFixed(4)}</div>
                  </div>
                  <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                    <div className="text-xs text-gray-500">Calidad</div>
                    <div className="font-bold">{(result1A1.calidad_imagen * 100).toFixed(0)}%</div>
                  </div>
                  <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                    <div className="text-xs text-gray-500">Iluminacion</div>
                    <div className="font-bold">{(result1A1.iluminacion * 100).toFixed(0)}%</div>
                  </div>
                  <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                    <div className="text-xs text-gray-500">Umbral</div>
                    <div className="font-bold">{(result1A1.umbral * 100).toFixed(0)}%</div>
                  </div>
                  <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                    <div className="text-xs text-gray-500">Probabilidad</div>
                    <div className="font-bold text-blue-600">{result1A1.probabilidad_calibrada != null ? `${(result1A1.probabilidad_calibrada * 100).toFixed(1)}%` : 'N/A'}</div>
                  </div>
                  <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                    <div className="text-xs text-gray-500">Confianza</div>
                    <div className="font-bold">{(result1A1.confianza * 100).toFixed(1)}%</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200">
                    <span className="text-xs text-blue-600 font-medium">Persona A</span>
                    <p className="font-bold text-gray-800">{result1A1.persona_a.nombre}</p>
                    <p className="text-xs text-gray-500">{result1A1.persona_a.email}</p>
                  </div>
                  <div className="p-3 bg-purple-50 dark:bg-purple-900/10 rounded-lg border border-purple-200">
                    <span className="text-xs text-purple-600 font-medium">Persona B</span>
                    <p className="font-bold text-gray-800">{result1A1.persona_b.nombre}</p>
                    <p className="text-xs text-gray-500">{result1A1.persona_b.email}</p>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* ═══ MANUAL MODE ═══ */}
      {modo === 'manual' && (
        <>
          <div className="prob-grid">
            <Card title="Ajustar Parametros">
              <div className="prob-config space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <label className="font-medium text-gray-700 dark:text-[var(--text-h)]">Similitud</label>
                    <span className={`font-mono font-bold ${getSimColor(similitud, 0.4)}`}>{(similitud * 100).toFixed(0)}%</span>
                  </div>
                  <input type="range" min="0" max="100" value={similitud * 100} onChange={(e) => setSimilitud(parseInt(e.target.value) / 100)}
                    className="w-full h-2 bg-gray-200 dark:bg-[var(--border)] rounded-lg appearance-none cursor-pointer accent-blue-600" />
                  <div className="flex justify-between text-xs text-gray-400 mt-1"><span>0%</span><span>Umbral: 40%</span><span>100%</span></div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <label className="font-medium text-gray-700 dark:text-[var(--text-h)]">Calidad Imagen</label>
                    <span className="font-mono font-bold">{(calidad * 100).toFixed(0)}%</span>
                  </div>
                  <input type="range" min="0" max="100" value={calidad * 100} onChange={(e) => setCalidad(parseInt(e.target.value) / 100)}
                    className="w-full h-2 bg-gray-200 dark:bg-[var(--border)] rounded-lg appearance-none cursor-pointer accent-blue-600" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <label className="font-medium text-gray-700 dark:text-[var(--text-h)]">Iluminacion</label>
                    <span className="font-mono font-bold">{(iluminacion * 100).toFixed(0)}%</span>
                  </div>
                  <input type="range" min="0" max="100" value={iluminacion * 100} onChange={(e) => setIluminacion(parseInt(e.target.value) / 100)}
                    className="w-full h-2 bg-gray-200 dark:bg-[var(--border)] rounded-lg appearance-none cursor-pointer accent-blue-600" />
                </div>
              </div>
            </Card>

            <Card title="Prediccion del Modelo">
              {manualLoading ? (
                <div className="flex items-center justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
              ) : manualResult ? (
                <div className="space-y-4">
                  <div className={`p-4 rounded-lg text-center ${manualResult.supera_umbral ? 'bg-green-50 dark:bg-green-900/20 border border-green-200' : 'bg-red-50 dark:bg-red-900/20 border border-red-200'}`}>
                    <p className={`text-sm font-bold ${manualResult.supera_umbral ? 'text-green-700' : 'text-red-700'}`}>
                      {manualResult.supera_umbral ? 'COINCIDENCIA' : 'SIN COINCIDENCIA'}
                    </p>
                    <p className="text-3xl font-bold mt-1">{(manualResult.probabilidad * 100).toFixed(1)}%</p>
                    <p className="text-xs text-gray-500 mt-1">Probabilidad calibrada</p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                      <div className="text-xs text-gray-500">Similitud</div>
                      <div className="font-bold">{(similitud * 100).toFixed(0)}%</div>
                    </div>
                    <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                      <div className="text-xs text-gray-500">Distancia</div>
                      <div className="font-bold">{(1 - similitud).toFixed(4)}</div>
                    </div>
                    <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                      <div className="text-xs text-gray-500">Umbral</div>
                      <div className="font-bold">40%</div>
                    </div>
                    <div className="p-2 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
                      <div className="text-xs text-gray-500">Confianza</div>
                      <div className="font-bold">{manualResult.confianza != null ? `${(manualResult.confianza * 100).toFixed(1)}%` : 'N/A'}</div>
                    </div>
                  </div>

                  {modelo?.trained && (
                    <div className="text-xs text-gray-500 text-center">
                      Modelo: {modelo.model_class} | {modelo.n_records} registros
                      {modelo.pocos_datos && <span className="text-yellow-600 ml-2">Pocos datos: estimacion poco fiable</span>}
                    </div>
                  )}
                  {!modelo?.trained && (
                    <div className="text-xs text-orange-500 text-center flex items-center justify-center gap-1">
                      <AlertTriangle size={12} />
                      Sin modelo ML entrenado. Entrena en Entrenamiento ML.
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-8">Ajusta los sliders para ver la prediccion</p>
              )}
            </Card>
          </div>

          {/* Graficos */}
          {sensibilidad.length > 0 && (
            <Card title="Curva de Sensibilidad">
              <p className="text-xs text-gray-500 mb-3">Probabilidad del modelo variando la similitud (calidad e iluminacion fijas al 100%)</p>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={sensibilidad}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="similitud" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <Tooltip formatter={(v: any) => `${(Number(v) * 100).toFixed(1)}%`} labelFormatter={(l: any) => `Similitud: ${(Number(l) * 100).toFixed(0)}%`} />
                  <ReferenceLine x={0.4} stroke="#ef4444" strokeDasharray="5 5" label={{ value: 'Umbral', position: 'top', fill: '#ef4444', fontSize: 11 }} />
                  <Line type="monotone" dataKey="probabilidad" stroke="#2563eb" strokeWidth={2} dot={false} name="Probabilidad" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          )}

          {escenarios.length > 0 && (
            <Card title="Comparacion de Escenarios">
              <p className="text-xs text-gray-500 mb-3">Misma similitud con buena iluminacion (100%)</p>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={escenarios}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="similitud" />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <Tooltip formatter={(v: any) => `${(Number(v) * 100).toFixed(1)}%`} />
                  <ReferenceLine y={0.4} stroke="#ef4444" strokeDasharray="5 5" />
                  <Bar dataKey="buena_luz" name="Buena luz" radius={[4, 4, 0, 0]}>
                    {escenarios.map((entry, index) => (
                      <Cell key={index} fill={entry.buena_luz >= 0.4 ? '#22c55e' : '#ef4444'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {modelo?.feature_importance && (
            <Card title="Contribucion de Variables (Feature Importance)">
              <p className="text-xs text-gray-500 mb-3">Peso de cada variable en la decision del modelo</p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(modelo.feature_importance).map(([k, v]) => ({ name: k, value: v }))} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  <YAxis type="category" dataKey="name" width={120} />
                  <Tooltip formatter={(v: any) => `${(Number(v) * 100).toFixed(1)}%`} />
                  <Bar dataKey="value" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
