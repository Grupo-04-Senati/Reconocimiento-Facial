import { useState, useRef, useEffect } from 'react';
import { CameraCapture } from '../components/CameraCapture';
import { registrarPersona, guardarRostro, healthCheck, confirmarResultado, obtenerHistorial, listarPersonas, autoConfirmarPendientes } from '../services/api';
import { UserPlus, CheckCircle, XCircle, Shield, Upload, RefreshCw, Brain } from 'lucide-react';
import type { HistorialEntry } from '../types/facial';

export function RegistroFacial() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [consentimiento, setConsentimiento] = useState(false);
  const [capturedImages, setCapturedImages] = useState<string[]>([]);
  const [registered, setRegistered] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const [currentStep, setCurrentStep] = useState<'form' | 'photos'>('form');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Historial confirmation state
  const [historial, setHistorial] = useState<(HistorialEntry & { resultado_real?: boolean | null })[]>([]);
  const [historialLoading, setHistorialLoading] = useState(false);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [personas, setPersonas] = useState<{ id: string; nombre: string }[]>([]);
  const [filterPersona, setFilterPersona] = useState('');

  const MIN_PHOTOS = 1;
  const MAX_PHOTOS = 1;

  const validateEmail = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);

  const loadHistorial = async () => {
    setHistorialLoading(true);
    try {
      const data = await obtenerHistorial();
      setHistorial(data.historial || []);
    } catch (err) {
      console.error(err);
    } finally {
      setHistorialLoading(false);
    }
  };

  useEffect(() => {
    loadHistorial();
    listarPersonas().then((d) => setPersonas(d.personas || [])).catch(() => {});
  }, []);

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

  const handleConfirm = async (logId: string, clasificacion: string) => {
    setConfirmingId(logId);
    try {
      await confirmarResultado(logId, clasificacion);
      // humano_real -> true ; no_real -> false (antes una condicion vieja marcaba
      // "no_real" como true por error).
      setHistorial((prev) =>
        prev.map((e) =>
          e.id === logId ? { ...e, resultado_real: clasificacion === 'humano_real', clasificacion } : e
        )
      );
      // Siempre refresca desde el backend para que el estado sea real (antes solo
      // se veia bien tras recargar la pagina).
      loadHistorial();
    } catch (err) {
      console.error('Error confirming:', err);
    } finally {
      setConfirmingId(null);
    }
  };

  const handleAutoConfirm = async () => {
    setConfirmingId('batch');
    try {
      const result = await autoConfirmarPendientes();
      if (result.confirmed > 0) {
        loadHistorial();
      } else if (result.message) {
        // Ej: modelo no entrenado -> avisar en vez de clasificar al azar
        window.alert(result.message);
      }
    } catch (err) {
      console.error('Auto-confirm error:', err);
    } finally {
      setConfirmingId(null);
    }
  };

  // ─── Registration handlers ──────────────────────────────────────
  const handleCapture = (imageSrc: string) => {
    // 1 foto por persona: la captura reemplaza directamente, sin paso intermedio
    // (antes había que pulsar "Agregar foto", lo que confundía y parecía trabarse).
    setCapturedImages([imageSrc]);
    setResult(null);
  };

  const handleRemovePhoto = (index: number) => {
    setCapturedImages(capturedImages.filter((_, i) => i !== index));
  };

  const handleRegisterAnother = () => {
    setNombre('');
    setEmail('');
    setConsentimiento(false);
    setCapturedImages([]);
    setResult(null);
    setRegistered(false);
    setCurrentStep('form');
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const src = ev.target?.result as string;
      if (src) {
        setCapturedImages([src]);
        setResult(null);
      }
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const handleNextStep = () => {
    if (!nombre.trim()) {
      setResult({ success: false, message: 'El nombre es obligatorio' });
      return;
    }
    if (nombre.trim().length < 2) {
      setResult({ success: false, message: 'El nombre debe tener al menos 2 caracteres' });
      return;
    }
    if (!email.trim()) {
      setResult({ success: false, message: 'El correo electronico es obligatorio' });
      return;
    }
    if (!validateEmail(email)) {
      setResult({ success: false, message: 'Ingrese un correo electronico valido' });
      return;
    }
    if (!consentimiento) {
      setResult({ success: false, message: 'Debe aceptar el consentimiento informado' });
      return;
    }
    setResult(null);
    setCurrentStep('photos');
  };

  const handleSubmit = async () => {
    if (capturedImages.length < MIN_PHOTOS) {
      setResult({ success: false, message: 'Capture una foto del rostro' });
      return;
    }

    setLoading(true);
    try {
      let backendOk = false;
      try {
        await healthCheck();
        backendOk = true;
      } catch {
        backendOk = false;
      }

      if (backendOk) {
        const response = await fetch(capturedImages[0]);
        const blob = await response.blob();
        const formData = new FormData();
        formData.append('nombre', nombre.trim());
        formData.append('email', email.trim().toLowerCase());
        formData.append('imagen', blob, 'face.jpg');

        const data = await registrarPersona(formData);
        const personaId = data.persona_id;

        for (let i = 1; i < capturedImages.length; i++) {
          try {
            const resp = await fetch(capturedImages[i]);
            const imgBlob = await resp.blob();
            const fd = new FormData();
            fd.append('imagen', imgBlob, `face_${i}.jpg`);
            await guardarRostro(personaId, fd);
          } catch (err) {
            console.warn(`Error guardando foto ${i + 1}:`, err);
          }
        }

        setResult({
          success: true,
          message: `${nombre} registrado exitosamente`,
        });
        // No se reinicia solo: se muestra el éxito y el usuario decide
        // registrar otra persona con el botón (antes se reiniciaba sin avisar).
        setRegistered(true);

        loadHistorial();
      } else {
        setResult({
          success: false,
          message: 'Backend no disponible. Verifique la conexion.',
        });
        return;
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al registrar persona';
      setResult({ success: false, message: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-[var(--text-h)]">Registro Facial</h1>
        <p className="text-gray-600 dark:text-[var(--text)]">
          Registra un nuevo rostro en el sistema. Se capturara una foto del rostro.
        </p>

        <div className="flex items-center gap-3 mb-4">
          <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
            currentStep === 'form' ? 'bg-blue-600 text-white' : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
          }`}>
            <span className="w-6 h-6 flex items-center justify-center rounded-full bg-white/20 text-xs">1</span>
            Datos personales
          </div>
          <div className="flex-1 h-0.5 bg-gray-200 dark:bg-[var(--border)]" />
          <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
            currentStep === 'photos' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-[var(--code-bg)] text-gray-400 dark:text-[var(--text)]'
          }`}>
            <span className="w-6 h-6 flex items-center justify-center rounded-full bg-white/20 text-xs">2</span>
            Captura facial ({capturedImages.length}/{MAX_PHOTOS})
          </div>
        </div>

        <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-6 border border-gray-200 dark:border-[var(--border)] shadow-sm space-y-5">
          {currentStep === 'form' ? (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-[var(--text-h)] mb-1">Nombre completo</label>
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Ej: Carlos Garcia"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-[var(--border)] rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-[var(--text-h)] mb-1">Correo electronico</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="carlos@senati.pe"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-[var(--border)] rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
                {email && !validateEmail(email) && (
                  <p className="text-xs text-red-500 dark:text-red-400 mt-1">Ingrese un correo valido</p>
                )}
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Shield className="text-blue-600 dark:text-blue-400 mt-0.5 shrink-0" size={20} />
                  <div>
                    <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-300">Consentimiento Informado</h4>
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      De acuerdo con la Ley N. 29733 de Proteccion de Datos Personales en Peru,
                      autorizo al Sistema de Reconocimiento Facial a recopilar, almacenar y procesar
                      mis datos biométricos (imagen facial y su embedding vectorial) exclusivamente
                      para fines de identificacion y autenticacion. Mis datos seran tratados con
                      confidencialidad y no seran compartidos con terceros sin mi consentimiento.
                    </p>
                    <label className="flex items-center gap-2 mt-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={consentimiento}
                        onChange={(e) => setConsentimiento(e.target.checked)}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                      <span className="text-sm font-medium text-blue-800 dark:text-blue-300">
                        Acepto el tratamiento de mis datos personales y biométricos
                      </span>
                    </label>
                  </div>
                </div>
              </div>

              <button
                onClick={handleNextStep}
                disabled={!nombre.trim() || !email.trim() || !consentimiento}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              >
                Siguiente: Captura facial
              </button>
            </>
          ) : registered ? (
            <div className="flex flex-col items-center gap-4 py-6 text-center">
              <CheckCircle className="text-green-600 dark:text-green-400" size={48} />
              <p className="text-lg font-semibold text-gray-800 dark:text-[var(--text-h)]">Persona registrada</p>
              {capturedImages[0] && (
                <img src={capturedImages[0]} alt="Registrada" className="w-24 h-24 object-cover rounded-lg border-2 border-green-300 dark:border-green-700" />
              )}
              <p className="text-sm text-gray-500 dark:text-[var(--text)] max-w-sm">
                Ya puede identificarse en <strong>Reconocimiento</strong>. Recuerda: para las probabilidades del modelo, entrena en <strong>Entrenamiento ML</strong> cuando tengas datos confirmados.
              </p>
              <button
                onClick={handleRegisterAnother}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                <UserPlus size={20} /> Registrar otra persona
              </button>
            </div>
          ) : (
            <>
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-[var(--text)] mb-2">
                  Capture una foto del rostro para el registro.
                </p>
                <p className="text-xs text-gray-400 dark:text-[var(--text)]">
                  Fotos capturadas: {capturedImages.length}
                </p>
              </div>

              {capturedImages.length > 0 && (
                <div className="flex gap-2 flex-wrap justify-center">
                  {capturedImages.map((img, i) => (
                    <div key={i} className="relative group">
                      <img src={img} alt={`Foto ${i + 1}`} className="w-20 h-20 object-cover rounded-lg border-2 border-green-300 dark:border-green-700" />
                      <button
                        onClick={() => handleRemovePhoto(i)}
                        className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        x
                      </button>
                      <span className="absolute bottom-0 left-0 right-0 text-center text-xs bg-black/50 text-white rounded-b-lg">
                        {i + 1}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-4 border border-gray-200 dark:border-[var(--border)]">
                {loading ? (
                  <div className="flex flex-col items-center gap-4 py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
                    <p className="text-gray-600 dark:text-[var(--text)]">Procesando rostro...</p>
                  </div>
                ) : (
                  <>
                    <div className="flex gap-3 justify-center mb-3">
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium"
                      >
                        <Upload size={16} /> Importar imagen
                      </button>
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    <CameraCapture onCapture={handleCapture} disabled={loading} />
                  </>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setCurrentStep('form')}
                  className="flex-1 px-4 py-3 border border-gray-300 dark:border-[var(--border)] text-gray-700 dark:text-[var(--text-h)] rounded-lg hover:bg-gray-50 dark:hover:bg-[var(--code-bg)] transition-colors font-medium"
                >
                  Volver
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={capturedImages.length < MIN_PHOTOS || loading}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  <UserPlus size={20} />
                  {loading ? 'Registrando...' : 'Registrar persona'}
                </button>
              </div>
            </>
          )}

          {result && (
            <div
              className={`flex items-start gap-3 p-4 rounded-lg ${
                result.success
                  ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                  : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
              }`}
            >
              {result.success ? (
                <CheckCircle className="text-green-600 dark:text-green-400 mt-0.5" size={20} />
              ) : (
                <XCircle className="text-red-600 dark:text-red-400 mt-0.5" size={20} />
              )}
              <p className={result.success ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'}>
                {result.message}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ═══ Confirmation Section ═══ */}
      <div className="max-w-5xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 dark:text-[var(--text-h)]">Confirmar Reconocimientos</h2>
            <p className="text-gray-600 dark:text-[var(--text)] text-sm">Revisa y confirma si los reconocimientos fueron correctos o incorrectos</p>
          </div>
          <button
            onClick={loadHistorial}
            disabled={historialLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors text-sm"
          >
            <RefreshCw size={16} className={historialLoading ? 'animate-spin' : ''} />
            Actualizar
          </button>
          <button
            onClick={handleAutoConfirm}
            disabled={confirmingId === 'batch'}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors text-sm"
          >
            <Brain size={16} className={confirmingId === 'batch' ? 'animate-spin' : ''} />
            {confirmingId === 'batch' ? 'Confirmando...' : 'Auto-confirmar'}
          </button>
        </div>

        <div className="flex items-center gap-3">
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
          {historialLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : filteredHistorial.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-8 text-gray-500 dark:text-[var(--text)]">
              <p>No hay registros de reconocimiento para confirmar</p>
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
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Probabilidad</th>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Resultado</th>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-[var(--text)] uppercase">Confirmar</th>
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
                        {entry.resultado_real != null ? (() => {
                          const isReal = entry.resultado_real === true || entry.clasificacion === 'humano_real';
                          return (
                            <span className={`text-xs font-medium ${isReal ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                              {isReal ? 'Humano Real' : 'No Real'}
                            </span>
                          );
                        })() : confirmingId === entry.id ? (
                          <span className="text-xs text-gray-400 dark:text-[var(--text)]">Guardando...</span>
                        ) : (
                          <div className="flex gap-1 flex-wrap">
                            <button
                              onClick={() => handleConfirm(entry.id, 'humano_real')}
                              className="px-2 py-1 text-[10px] font-medium text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded hover:bg-green-100 dark:hover:bg-green-900/40 transition-colors"
                              title="Confirmar como humano real"
                            >
                              Humano Real
                            </button>
                            <button
                              onClick={() => handleConfirm(entry.id, 'no_real')}
                              className="px-2 py-1 text-[10px] font-medium text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
                              title="Confirmar como no real (IA, imagen o dibujo)"
                            >
                              No Real
                            </button>
                          </div>
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
    </div>
  );
}
