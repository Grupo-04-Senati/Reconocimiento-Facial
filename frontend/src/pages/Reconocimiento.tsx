import { useState, useRef, useEffect, useCallback } from 'react';
import Webcam from 'react-webcam';
import { FaceResultCard } from '../components/FaceResultCard';
import { api, personasCount, obtenerMetricas } from '../services/api';
import type { RecognitionResult } from '../types/facial';
import { Upload, Camera, CameraOff, Radio, Square, AlertTriangle, Info, XCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

export function Reconocimiento() {
  const [result, setResult] = useState<{
    coincide: boolean;
    data: RecognitionResult | null;
    resultadoReal?: boolean | null;
    clasificacion?: string | null;
    esHumano?: boolean;
    detail?: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<'camera' | 'upload'>('camera');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const selectedFileRef = useRef<File | null>(null);

  const [cameraOn, setCameraOn] = useState(false);
  const [autoMode, setAutoMode] = useState(false);
  const webcamRef = useRef<Webcam>(null);
  const autoIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const processingRef = useRef(false);

  // Avisos de flujo (no bloqueantes): guían el orden registrar -> entrenar -> reconocer
  const [numPersonas, setNumPersonas] = useState<number | null>(null);
  const [modeloEntrenado, setModeloEntrenado] = useState<boolean | null>(null);

  useEffect(() => {
    personasCount().then((d) => setNumPersonas(d.total ?? 0)).catch(() => {});
    obtenerMetricas().then((d) => setModeloEntrenado(!!d.trained)).catch(() => {});
  }, []);

  const processImage = useCallback(async (imageSrc: string) => {
    if (processingRef.current) return;
    processingRef.current = true;
    try {
      const response = await fetch(imageSrc);
      const blob = await response.blob();
      const formData = new FormData();
      formData.append('imagen', blob, 'face.jpg');

      const { data } = await api.post('/api/reconocimiento', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });

      setResult({
        coincide: data.coincide,
        data: data.resultado,
        resultadoReal: data.resultado_real,
        clasificacion: data.clasificacion,
        esHumano: data.es_humano,
        detail: data.detail,
      });
    } catch (err: unknown) {
      console.error('Recognition error:', err);
    } finally {
      processingRef.current = false;
    }
  }, []);

  useEffect(() => {
    if (autoMode && cameraOn) {
      autoIntervalRef.current = setInterval(() => {
        if (webcamRef.current) {
          const src = webcamRef.current.getScreenshot();
          if (src) {
            setPreviewUrl(src);
            processImage(src);
          }
        }
      }, 3000);
    } else {
      if (autoIntervalRef.current) {
        clearInterval(autoIntervalRef.current);
        autoIntervalRef.current = null;
      }
    }
    return () => {
      if (autoIntervalRef.current) {
        clearInterval(autoIntervalRef.current);
        autoIntervalRef.current = null;
      }
    };
  }, [autoMode, cameraOn, processImage]);

  useEffect(() => {
    if (!cameraOn) {
      setAutoMode(false);
    }
  }, [cameraOn]);

  const handleManualCapture = useCallback(() => {
    if (webcamRef.current) {
      const src = webcamRef.current.getScreenshot();
      if (src) {
        setPreviewUrl(src);
        setLoading(true);
        setResult(null);
        setError('');
        processImage(src).finally(() => setLoading(false));
      }
    }
  }, [processImage]);

  const processFile = async (file: File) => {
    selectedFileRef.current = file;
    setLoading(true);
    setResult(null);
    setError('');
    try {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);

      const formData = new FormData();
      formData.append('imagen', file, 'face.jpg');

      const { data } = await api.post('/api/reconocimiento', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });

      setResult({
        coincide: data.coincide,
        data: data.resultado,
        resultadoReal: data.resultado_real,
        clasificacion: data.clasificacion,
        esHumano: data.es_humano,
        detail: data.detail,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al procesar';
      console.error('Recognition error:', msg);
      setError(msg.includes('timeout')
        ? 'Tiempo de espera agotado. Intenta con otra imagen.'
        : msg.includes('Network')
        ? 'Error de conexion con el backend.'
        : 'Error al procesar el reconocimiento');
      setResult({ coincide: false, data: null });
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-800 dark:text-[var(--text-h)]">Reconocimiento Facial</h1>
      <p className="text-gray-600 dark:text-[var(--text)]">
        Capture o suba una imagen para identificar una persona en el sistema.
      </p>

      {numPersonas === 0 && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-sm text-amber-800 dark:text-amber-300">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <p>
            Aún no hay personas registradas, así que ningún rostro podrá coincidir. Primero ve a{' '}
            <Link to="/registro" className="font-semibold underline">Registro Facial</Link> y agrega al menos una persona.
          </p>
        </div>
      )}

      {numPersonas !== null && numPersonas > 0 && modeloEntrenado === false && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-sm text-blue-700 dark:text-blue-300">
          <Info size={16} className="mt-0.5 shrink-0" />
          <p>
            El modelo de probabilidades aún no está entrenado: se usará una estimación básica. Para probabilidades calibradas,
            confirma reconocimientos y entrena en{' '}
            <Link to="/entrenamiento" className="font-semibold underline">Entrenamiento ML</Link>.
          </p>
        </div>
      )}

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => { setMode('camera'); setResult(null); setPreviewUrl(null); setAutoMode(false); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            mode === 'camera' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-[var(--code-bg)] text-gray-600 dark:text-[var(--text)] hover:bg-gray-200 dark:hover:bg-[var(--border)]'
          }`}
        >
          <Camera size={16} /> Camara
        </button>
        <button
          onClick={() => { setMode('upload'); setResult(null); setPreviewUrl(null); setAutoMode(false); setCameraOn(false); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            mode === 'upload' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-[var(--code-bg)] text-gray-600 dark:text-[var(--text)] hover:bg-gray-200 dark:hover:bg-[var(--border)]'
          }`}
        >
          <Upload size={16} /> Subir imagen
        </button>
      </div>

      <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-6 border border-gray-200 dark:border-[var(--border)] shadow-sm">
        {mode === 'camera' ? (
          <>
            <div className="camera-capture">
              <div className="camera-viewport">
                {cameraOn ? (
                  <Webcam ref={webcamRef} screenshotFormat="image/jpeg" screenshotQuality={0.85} className="camera-feed" mirrored />
                ) : (
                  <div className="camera-off-state">
                    <CameraOff size={48} />
                    <p>Camara desactivada</p>
                  </div>
                )}
                {cameraOn && (
                  <>
                    <div className="camera-overlay">
                      <div className="camera-frame" />
                    </div>
                    {autoMode && (
                      <div className="absolute top-3 left-3 flex items-center gap-2 bg-red-600 text-white text-xs font-bold px-3 py-1.5 rounded-full animate-pulse z-10">
                        <Radio size={12} />
                        EN VIVO
                      </div>
                    )}
                  </>
                )}
              </div>
              <div className="camera-controls flex gap-2 justify-center">
                <button
                  className={`cam-btn ${cameraOn ? '' : 'primary'}`}
                  onClick={() => setCameraOn(!cameraOn)}
                  disabled={loading}
                >
                  {cameraOn ? <CameraOff size={18} /> : <Camera size={18} />}
                  {cameraOn ? 'Desactivar' : 'Activar Camara'}
                </button>
                {cameraOn && (
                  <button
                    className={`cam-btn ${autoMode ? 'bg-red-600 text-white hover:bg-red-700' : ''}`}
                    onClick={() => setAutoMode(!autoMode)}
                    disabled={loading}
                  >
                    {autoMode ? <Square size={18} /> : <Radio size={18} />}
                    {autoMode ? 'Detener' : 'Modo Tiempo Real'}
                  </button>
                )}
                {cameraOn && !autoMode && (
                  <button className="cam-btn primary" onClick={handleManualCapture} disabled={loading}>
                    <Camera size={18} /> Capturar
                  </button>
                )}
              </div>
            </div>
            {loading && (
              <div className="flex items-center justify-center gap-2 py-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
                <span className="text-sm text-gray-500">Analizando...</span>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center gap-4 py-8">
            {previewUrl && (
              <img src={previewUrl} alt="Preview" className="max-h-64 rounded-lg" />
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
            {previewUrl ? (
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    if (selectedFileRef.current) {
                      setLoading(true);
                      setResult(null);
                      setError('');
                      processFile(selectedFileRef.current).finally(() => setLoading(false));
                    }
                  }}
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50"
                >
                  {loading ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" /> : <Upload size={20} />}
                  Cargar imagen
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
                >
                  <Upload size={20} />
                  Seleccionar otra imagen
                </button>
              </div>
            ) : (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                <Upload size={20} />
                Seleccionar imagen
              </button>
            )}
            <p className="text-sm text-gray-500 dark:text-[var(--text)]">Formatos aceptados: JPG, PNG (max 5MB)</p>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {result && result.esHumano === false ? (
        <div className="rounded-xl p-6 border-2 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
          <div className="flex items-center gap-3 mb-2">
            <XCircle className="text-red-600 dark:text-red-400" size={28} />
            <h3 className="text-xl font-bold text-gray-800 dark:text-[var(--text-h)]">No es humano</h3>
          </div>
          <div className="flex items-start gap-2 text-gray-600 dark:text-[var(--text)]">
            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
            <p className="text-sm">
              No se detectó un rostro humano (posible objeto, animal o dibujo). Acceso denegado.
            </p>
          </div>
        </div>
      ) : result ? (
        <FaceResultCard
          name={result.data?.nombre || ''}
          photo=""
          result={result.data}
          coincide={result.coincide}
          clasificacion={result.clasificacion}
        />
      ) : null}
    </div>
  );
}
