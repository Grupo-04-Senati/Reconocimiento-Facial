import { useState, useEffect } from 'react';
import { Card } from '../components/Card';
import { entrenarModelo, obtenerMetricas, clasificacionPersonas, recalcularResultado, limpiarDB } from '../services/api';
import { Brain, Database, Target, CheckCircle, XCircle, AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react';
import './EntrenamientoML.css';

interface ClassificationPerson {
  persona_id: string;
  nombre: string;
  email: string;
  similitud: number;
  distancia: number;
  fecha: string;
}

interface ClassificationData {
  humanos_reales: ClassificationPerson[];
  humanos_semi_reales: ClassificationPerson[];
  no_reales_detectados: ClassificationPerson[];
  no_reales_rechazados: ClassificationPerson[];
}

interface MLMetricsData {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  falsePositiveRate: number;
  falseNegativeRate: number;
  confusionMatrix: { tp: number; tn: number; fp: number; fn: number };
}

export function EntrenamientoML() {
  const [metrics, setMetrics] = useState<MLMetricsData | null>(null);
  const [training, setTraining] = useState(false);
  const [recordsCount, setRecordsCount] = useState<number | null>(null);
  const [positiveCount, setPositiveCount] = useState(0);
  const [negativeCount, setNegativeCount] = useState(0);
  const [trainingResult, setTrainingResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');
  const [recalculando, setRecalculando] = useState(false);
  const [recalcMsg, setRecalcMsg] = useState('');
  const [limpiando, setLimpiando] = useState(false);
  const [limpMsg, setLimpMsg] = useState('');
  const [clasificacion, setClasificacion] = useState<ClassificationData | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [metricsWarning, setMetricsWarning] = useState<string | null>(null);
  const [evaluacion, setEvaluacion] = useState<string>('');
  const [overfittingMsg, setOverfittingMsg] = useState<string | null>(null);
  const [cvAccuracy, setCvAccuracy] = useState<number | null>(null);
  const [cvGap, setCvGap] = useState<number | null>(null);
  const [trainAccuracy, setTrainAccuracy] = useState<number | null>(null);
  const [fuenteCounts, setFuenteCounts] = useState<Record<string, number>>({});
  const [kaggleCount, setKaggleCount] = useState(0);

  useEffect(() => {
    loadStatus();
    clasificacionPersonas().then((d) => setClasificacion(d)).catch(() => {});
  }, []);

  const loadStatus = async () => {
    try {
      const data = await obtenerMetricas();
      if (data.fuente_counts) {
        setFuenteCounts(data.fuente_counts);
      }
      if (data.kaggle_count) {
        setKaggleCount(data.kaggle_count);
      }
      if (data.trained) {
        if (data.detailed_metrics) {
          const dm = data.detailed_metrics;
          setRecordsCount(dm.n_records ?? 0);
          setPositiveCount(dm.positivos ?? 0);
          setNegativeCount(dm.negativos ?? 0);
        }
        if (data.metrics && (data.metrics.accuracy !== undefined || data.metrics.true_positives !== undefined)) {
          setMetricsWarning(data.metrics.metricas_fiables === false ? (data.metrics.warning || null) : null);
          setEvaluacion(data.metrics.evaluacion || '');
          setOverfittingMsg(data.metrics.overfitting ? (data.metrics.overfitting_msg || 'Posible sobreajuste.') : null);
          setCvAccuracy(data.metrics.cv_accuracy ?? null);
          setCvGap(data.metrics.cv_gap ?? null);
          setTrainAccuracy(data.metrics.train_accuracy ?? null);
          setMetrics({
            accuracy: Math.round((data.metrics.accuracy ?? 0) * 100),
            precision: Math.round((data.metrics.precision ?? 0) * 100),
            recall: Math.round((data.metrics.recall ?? 0) * 100),
            f1: Math.round((data.metrics.f1_score ?? 0) * 100),
            falsePositiveRate: Math.round((data.metrics.far ?? 0) * 100),
            falseNegativeRate: Math.round((data.metrics.frr ?? 0) * 100),
            confusionMatrix: {
              tp: data.metrics.true_positives ?? 0,
              tn: data.metrics.true_negatives ?? 0,
              fp: data.metrics.false_positives ?? 0,
              fn: data.metrics.false_negatives ?? 0,
            },
          });
        }
      } else if (data.detailed_metrics) {
        const dm = data.detailed_metrics;
        setRecordsCount(dm.n_records ?? 0);
        setPositiveCount(dm.positivos ?? 0);
        setNegativeCount(dm.negativos ?? 0);
      }
    } catch (err) {
      console.error('Error loading metrics:', err);
    }
  };

  const MIN_PER_CLASS = 10;
  const totalRecords = (recordsCount ?? 0) + kaggleCount;
  const canTrain = positiveCount >= MIN_PER_CLASS && negativeCount >= MIN_PER_CLASS || totalRecords >= MIN_PER_CLASS * 2;

  const handleRecalcular = async () => {
    setRecalculando(true);
    setRecalcMsg('');
    try {
      const result = await recalcularResultado();
      setRecalcMsg(result.message || 'Recalculado');
      clasificacionPersonas().then((d) => setClasificacion(d)).catch(() => {});
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al recalcular';
      setRecalcMsg(msg);
    } finally {
      setRecalculando(false);
    }
  };

  const handleLimpiar = async (todo: boolean) => {
    const msg = todo
      ? 'ELIMINARA TODO: personas, embeddings, logs, training records y modelo ML. Continuar?'
      : 'Eliminara recognition_logs, ml_training_records y modelo ML. Las personas se mantienen. Continuar?';
    if (!window.confirm(msg)) return;
    setLimpiando(true);
    setLimpMsg('');
    try {
      const result = await limpiarDB(todo);
      setLimpMsg(result.message || 'Limpieza completada');
      setClasificacion(null);
      setMetrics(null);
      setRecordsCount(0);
      setPositiveCount(0);
      setNegativeCount(0);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al limpiar';
      setLimpMsg(msg);
    } finally {
      setLimpiando(false);
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    setError('');
    setTrainingResult(null);
    try {
      const result = await entrenarModelo();
      setTrainingResult(result);
      if (result.metrics) {
        const m = result.metrics;
        setMetricsWarning(m.metricas_fiables === false ? (m.warning || 'Métricas poco fiables por pocos datos.') : null);
        setEvaluacion(m.evaluacion || '');
        setOverfittingMsg(m.overfitting ? (m.overfitting_msg || 'Posible sobreajuste.') : null);
        setCvAccuracy(m.cv_accuracy ?? null);
        setCvGap(m.cv_gap ?? null);
        setTrainAccuracy(m.train_accuracy ?? null);
        setMetrics({
          accuracy: Math.round((m.accuracy ?? 0) * 100),
          precision: Math.round((m.precision ?? 0) * 100),
          recall: Math.round((m.recall ?? 0) * 100),
          f1: Math.round((m.f1_score ?? 0) * 100),
          falsePositiveRate: Math.round((m.far ?? 0) * 100),
          falseNegativeRate: Math.round((m.frr ?? 0) * 100),
          confusionMatrix: {
            tp: m.true_positives ?? 0,
            tn: m.true_negatives ?? 0,
            fp: m.false_positives ?? 0,
            fn: m.false_negatives ?? 0,
          },
        });
        setRecordsCount(m.n_records ?? null);
        setPositiveCount(m.positivos ?? 0);
        setNegativeCount(m.negativos ?? 0);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al entrenar';
      setError(msg.includes('400') ? 'Se necesitan al menos 10 de cada clase (Humano Real y No Real) para entrenar.' : msg);
    } finally {
      setTraining(false);
    }
  };

  const getClassCatData = () => {
    // Composicion REAL del entrenamiento (incluye Kaggle) tomada de la matriz de
    // confusion. Antes contaba solo personas de recognition_logs, por eso salia 0
    // cuando los datos venian de Kaggle (que es entrenamiento interno, no personas).
    const cm = metrics?.confusionMatrix;
    const realesCM = cm ? (cm.tp + cm.fn) : 0;
    const noRealesCM = cm ? (cm.fp + cm.tn) : 0;
    const reales = realesCM || ((clasificacion?.humanos_reales?.length || 0) + (clasificacion?.humanos_semi_reales?.length || 0));
    const noReales = noRealesCM || ((clasificacion?.no_reales_detectados?.length || 0) + (clasificacion?.no_reales_rechazados?.length || 0));
    const total = reales + noReales || 1;
    return [
      { key: 'reales', label: 'Humanos Reales', desc: 'Muestras reales del entrenamiento (incluye Kaggle)', color: 'green', pct: Math.round((reales / total) * 100), count: reales, list: [...(clasificacion?.humanos_reales || []), ...(clasificacion?.humanos_semi_reales || [])] },
      { key: 'no_reales', label: 'No Reales', desc: 'Muestras IA/no reales del entrenamiento (incluye Kaggle)', color: 'red', pct: Math.round((noReales / total) * 100), count: noReales, list: [...(clasificacion?.no_reales_detectados || []), ...(clasificacion?.no_reales_rechazados || [])] },
    ];
  };

  return (
    <div className="entrenamiento">
      <div className="ml-stats-row">
        <Card title="Registros Sistema">
          <div className="ml-big-number">{recordsCount ?? 0}</div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">registro + reconocimiento</p>
        </Card>
        <Card title="Muestras Kaggle">
          <div className="ml-big-number" style={{ color: '#8b5cf6' }}>{kaggleCount}</div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1"> embeddings reales/IA</p>
        </Card>
        <Card title="Positivos / Negativos">
          <div className="flex items-center gap-3">
            <div className="ml-big-number" style={{ color: '#22c55e' }}>{positiveCount}</div>
            <span className="text-gray-400 text-lg">/</span>
            <div className="ml-big-number" style={{ color: '#ef4444' }}>{negativeCount}</div>
          </div>
          {(positiveCount < MIN_PER_CLASS || negativeCount < MIN_PER_CLASS) && (
            <p className="text-xs text-orange-500 dark:text-orange-400 mt-1">
              Se necesitan {MIN_PER_CLASS} de cada tipo (Humano Real y No Real) para entrenar
            </p>
          )}
        </Card>
        {metrics && (
          <Card title="Ultima Precision">
            <div className="ml-big-number" style={{ color: metrics.accuracy >= 80 ? '#22c55e' : '#f59e0b' }}>{metrics.accuracy}%</div>
          </Card>
        )}
      </div>

      <div className="ml-grid">
        <Card title="Entrenar Modelo (Backend)">
          <div className="ml-train-section">
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-700 dark:text-blue-400">
              <strong>Regresion Logistica</strong> con 21 features (similitud + OpenCV: textura, FFT, ruido, LBP, entropia, suavidad) + class_weight=balanced + calibracion Isotonica.
            </div>
            <button
              className="ml-train-btn"
              onClick={handleTrain}
              disabled={training || !canTrain}
              title={!canTrain ? `Necesitas al menos ${MIN_PER_CLASS} de cada clase (Humano Real y No Real)` : ''}
            >
              <Brain size={18} />
              {training ? 'Entrenando en backend...' : canTrain ? 'Entrenar Modelo' : `Faltan datos (${positiveCount < MIN_PER_CLASS ? `${MIN_PER_CLASS - positiveCount} reales` : ''} ${negativeCount < MIN_PER_CLASS ? `${MIN_PER_CLASS - negativeCount} no reales` : ''})`}
            </button>
            <p className="text-xs text-gray-500 dark:text-[var(--text)] mt-2">
              Entrena con datos del sistema (21 features reales). Se auto-entrena cuando hay 10+ de cada clase.
            </p>
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <button
                className="ml-train-btn"
                onClick={handleRecalcular}
                disabled={recalculando}
                style={{ background: '#f59e0b' }}
              >
                <Database size={18} />
                {recalculando ? 'Recalculando...' : 'Recalcular Resultados (ML)'}
              </button>
              <p className="text-xs text-gray-500 dark:text-[var(--text)] mt-1">
                Recalcula resultado_real de todos los registros usando el modelo ML actual.
              </p>
              {recalcMsg && (
                <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded text-xs text-yellow-700 dark:text-yellow-400">
                  {recalcMsg}
                </div>
              )}
            </div>
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex gap-2">
                <button
                  className="ml-train-btn"
                  onClick={() => handleLimpiar(false)}
                  disabled={limpiando}
                  style={{ background: '#f59e0b', flex: 1 }}
                >
                  <Database size={18} />
                  {limpiando ? 'Limpiando...' : 'Limpiar Logs y Training'}
                </button>
                <button
                  className="ml-train-btn"
                  onClick={() => handleLimpiar(true)}
                  disabled={limpiando}
                  style={{ background: '#ef4444', flex: 1 }}
                >
                  <XCircle size={18} />
                  {limpiando ? 'Limpiando...' : 'Limpiar TODO (Reset Total)'}
                </button>
              </div>
              <p className="text-xs text-gray-500 dark:text-[var(--text)] mt-1">
                Amarillo: solo logs y training. Rojo: TODO (personas, embeddings, logs, training, modelo).
              </p>
              {limpMsg && (
                <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-xs text-red-700 dark:text-red-400">
                  {limpMsg}
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-400">
              {error}
            </div>
          )}

          {trainingResult && (
            <div className="mt-3 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-sm text-green-700 dark:text-green-400">
              Modelo entrenado con {String(trainingResult.records_used)} registros
            </div>
          )}
        </Card>

        <Card title="Informacion del Dataset">
          <div className="ml-dataset-actions">
            <p className="text-sm text-gray-600 dark:text-[var(--text)] mb-2">
              <strong>Datos del sistema:</strong> {recordsCount ?? 0} registros con 21 features reales (similitud, textura, FFT, ruido, LBP, entropia, suavidad).
            </p>
            <p className="text-sm text-gray-600 dark:text-[var(--text)] mb-2">
              <strong>Kaggle:</strong> {kaggleCount} muestras de embeddings (features por defecto 0.5).
            </p>
            <p className="text-sm text-gray-600 dark:text-[var(--text)] mb-2">
              <strong>Label:</strong> resultado_real (Humano Real / No Real), confirmado desde el Historial.
            </p>
            {Object.keys(fuenteCounts).length > 0 && (
              <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-800 rounded text-xs">
                <strong>Fuentes (sistema):</strong>
                {Object.entries(fuenteCounts).map(([fuente, count]) => (
                  <span key={fuente} className="ml-2 inline-block px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                    {fuente}: {count}
                  </span>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>

      {metrics && (
        <Card title="Metricas del Modelo">
          {overfittingMsg && (
            <div className="mb-3 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-300 dark:border-orange-800 rounded-lg text-sm text-orange-800 dark:text-orange-300 flex items-start gap-2">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" />
              <span><strong>Posible sobreajuste (overfitting):</strong> {overfittingMsg}</span>
            </div>
          )}
          {metricsWarning && (
            <div className="mb-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg text-sm text-yellow-800 dark:text-yellow-300 flex items-start gap-2">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" />
              <span>{metricsWarning}</span>
            </div>
          )}
          {evaluacion && (
            <p className="mb-3 text-xs text-gray-500 dark:text-[var(--text)]">
              Evaluación: <strong>{evaluacion}</strong>
            </p>
          )}
          {cvAccuracy !== null && (
            <div className="mb-3 p-3 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg text-sm">
              <div className="flex items-center gap-4 flex-wrap">
                <span className="text-purple-700 dark:text-purple-300 font-medium">Validacion Cruzada (CV):</span>
                {trainAccuracy !== null && (
                  <span className="text-gray-700 dark:text-gray-300">Train: <strong>{Math.round(trainAccuracy * 100)}%</strong></span>
                )}
                <span className="text-gray-700 dark:text-gray-300">CV Promedio: <strong>{Math.round(cvAccuracy * 100)}%</strong></span>
                {cvGap !== null && (
                  <span className={`font-bold ${cvGap >= 0.10 ? 'text-red-600 dark:text-red-400' : cvGap >= 0.05 ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400'}`}>
                    Brecha: {Math.round(cvGap * 100)}% {cvGap >= 0.10 ? '(sobreajuste)' : cvGap >= 0.05 ? '(leve)' : '(OK)'}
                  </span>
                )}
              </div>
            </div>
          )}
          <div className="ml-metrics-grid">
            <div className="ml-metric-card"><Target size={20} /><span className="ml-metric-val">{metrics.accuracy}%</span><span className="ml-metric-lbl">Accuracy</span></div>
            <div className="ml-metric-card"><CheckCircle size={20} /><span className="ml-metric-val">{metrics.precision}%</span><span className="ml-metric-lbl">Precision</span></div>
            <div className="ml-metric-card"><AlertTriangle size={20} /><span className="ml-metric-val">{metrics.recall}%</span><span className="ml-metric-lbl">Recall</span></div>
            <div className="ml-metric-card"><Database size={20} /><span className="ml-metric-val">{metrics.f1}%</span><span className="ml-metric-lbl">F1-Score</span></div>
            <div className="ml-metric-card"><XCircle size={20} /><span className="ml-metric-val" style={{ color: '#ef4444' }}>{metrics.falsePositiveRate}%</span><span className="ml-metric-lbl">FAR</span></div>
            <div className="ml-metric-card"><XCircle size={20} /><span className="ml-metric-val" style={{ color: '#f59e0b' }}>{metrics.falseNegativeRate}%</span><span className="ml-metric-lbl">FRR</span></div>
          </div>

          <div className="ml-confusion">
            <h4>Matriz de Confusion</h4>
            <div className="ml-cm-grid">
              <div className="ml-cm-header"></div>
              <div className="ml-cm-header">Pred: Real</div>
              <div className="ml-cm-header">Pred: No Real</div>
              <div className="ml-cm-label">Humano Real</div>
              <div className="ml-cm-cell tp">{metrics.confusionMatrix.tp}</div>
              <div className="ml-cm-cell fn">{metrics.confusionMatrix.fn}</div>
              <div className="ml-cm-label">No Real</div>
              <div className="ml-cm-cell fp">{metrics.confusionMatrix.fp}</div>
              <div className="ml-cm-cell tn">{metrics.confusionMatrix.tn}</div>
            </div>
            <div className="ml-cm-legend">
              <div className="ml-cm-legend-item">
                <span className="ml-cm-legend-dot" style={{ background: '#22c55e' }} />
                <div>
                  <strong>Verdaderos Positivos ({metrics.confusionMatrix.tp})</strong>
                  <p>Humanos reales correctamente identificados</p>
                </div>
              </div>
              <div className="ml-cm-legend-item">
                <span className="ml-cm-legend-dot" style={{ background: '#ef4444' }} />
                <div>
                  <strong>Falsos Negativos ({metrics.confusionMatrix.fn})</strong>
                  <p>Humanos reales clasificados como no reales</p>
                </div>
              </div>
              <div className="ml-cm-legend-item">
                <span className="ml-cm-legend-dot" style={{ background: '#f59e0b' }} />
                <div>
                  <strong>Falsos Positivos ({metrics.confusionMatrix.fp})</strong>
                  <p>No reales clasificados como humanos reales</p>
                </div>
              </div>
              <div className="ml-cm-legend-item">
                <span className="ml-cm-legend-dot" style={{ background: '#3b82f6' }} />
                <div>
                  <strong>Verdaderos Negativos ({metrics.confusionMatrix.tn})</strong>
                  <p>No reales correctamente identificados</p>
                </div>
              </div>
            </div>
            <div className="ml-cm-categories">
              <h5>Clasificacion del ML</h5>
              <div className="ml-cm-cat-grid">
                {getClassCatData().map((cat) => (
                  <div key={cat.key}>
                    <div
                      className={`ml-cm-cat ${cat.color} clickable`}
                      onClick={() => setExpandedCategory(expandedCategory === cat.key ? null : cat.key)}
                    >
                      <span className="ml-cm-cat-pct">{cat.pct}%</span>
                      <span className="ml-cm-cat-label">{cat.label}</span>
                      <span className="ml-cm-cat-desc">{cat.desc}</span>
                      <span className="ml-cm-cat-count">{cat.count} muestras {expandedCategory === cat.key ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</span>
                    </div>
                    {expandedCategory === cat.key && (
                      <div className="ml-cm-cat-list">
                        {cat.list.length === 0 ? (
                          <p className="ml-cm-cat-empty">Solo se listan personas enroladas. Las muestras del dataset (Kaggle) cuentan para el modelo pero no se listan individualmente.</p>
                        ) : (
                          <table className="ml-cm-cat-table">
                            <thead>
                              <tr>
                                <th>Nombre</th>
                                <th>Email</th>
                                <th>Similitud</th>
                              </tr>
                            </thead>
                            <tbody>
                              {cat.list.map((p, i) => (
                                <tr key={i}>
                                  <td className="font-medium">{p.nombre}</td>
                                  <td>{p.email}</td>
                                  <td>{p.similitud}%</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
