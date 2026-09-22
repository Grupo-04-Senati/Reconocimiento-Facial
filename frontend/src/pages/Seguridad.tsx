import { useState, useEffect, useRef } from 'react';
import { Card } from '../components/Card';
import { authListUsers, authDeleteUser, authRegister, authChangeRole, agregarMuestra } from '../services/api';
import { api } from '../services/api';
import type { Role } from '../types';
import { ROLE_LABELS } from '../types';
import { Shield, UserPlus, Trash2, Brain, Fingerprint, Upload, Images, CheckCircle, XCircle } from 'lucide-react';
import './Seguridad.css';

interface BackendUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  active: boolean;
  created_at: string;
}

interface AuditLogEntry {
  id: string;
  persona_id: string | null;
  similitud: number;
  distancia: number;
  umbral: number;
  coincide: boolean;
  probabilidad_calibrada: number | null;
  resultado_real: boolean | null;
  created_at: string;
  personas?: { nombre: string };
}

// Redimensiona una imagen en el navegador a max `maxDim` px y la convierte a JPEG.
// Reduce la carga del backend (evita timeouts) y normaliza formatos (WEBP/AVIF -> JPEG).
function resizeImage(file: File, maxDim = 800, quality = 0.85): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      let { width, height } = img;
      if (width > maxDim || height > maxDim) {
        if (width >= height) { height = Math.round((height * maxDim) / width); width = maxDim; }
        else { width = Math.round((width * maxDim) / height); height = maxDim; }
      }
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) { reject(new Error('canvas')); return; }
      ctx.drawImage(img, 0, 0, width, height);
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('blob'))), 'image/jpeg', quality);
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('No se pudo leer la imagen')); };
    img.src = url;
  });
}

export function Seguridad() {
  const [users, setUsers] = useState<BackendUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'operador' as Role });
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(true);
  const [error, setError] = useState('');

  // Carga masiva de imagenes: registra + etiqueta + crea dato ML, todo junto
  const [regTipo, setRegTipo] = useState<'real' | 'ia'>('real');
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchResults, setBatchResults] = useState<{ name: string; status: string; ok: boolean }[]>([]);
  const batchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadUsers();
    loadAuditLogs();
  }, []);

  const handleBatchFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setBatchRunning(true);
    setBatchResults([]);
    const ts = Date.now();
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      // Optimiza en el navegador: reduce a max 800px y convierte a JPEG.
      // Baja la carga del backend (evita timeouts) y admite WEBP/AVIF.
      let blob: Blob;
      try {
        blob = await resizeImage(file, 800, 0.85);
      } catch {
        setBatchResults((p) => [...p, { name: file.name, status: 'No se pudo leer la imagen (formato no soportado)', ok: false }]);
        continue;
      }
      try {
        const esReal = regTipo === 'real';
        const fd = new FormData();
        fd.append('imagen', blob, 'face.jpg');
        fd.append('nombre', `Persona ${ts}-${i + 1}`);
        fd.append('email', `carga_${ts}_${i + 1}@dataset.local`);
        const data = await agregarMuestra(fd, esReal);
        setBatchResults((p) => [...p, { name: file.name, status: `Registrada (${esReal ? 'Humano Real' : 'No Real'}) · sim ${Math.round((data.similitud || 0) * 100)}%`, ok: true }]);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Error';
        const low = msg.toLowerCase();
        let nice: string;
        if (msg.includes('422') || low.includes('rostro')) nice = 'No se detecto un rostro';
        else if (msg.includes('400')) nice = 'Ya registrado';
        else if (low.includes('network') || low.includes('cors') || low.includes('failed') || low.includes('timeout')) nice = 'Error de red/servidor (reintenta esta imagen)';
        else nice = msg.slice(0, 60);
        setBatchResults((p) => [...p, { name: file.name, status: nice, ok: false }]);
      }
      // Pequena pausa para no saturar el backend
      await new Promise((r) => setTimeout(r, 250));
    }
    setBatchRunning(false);
    if (batchInputRef.current) batchInputRef.current.value = '';
  };

  const loadUsers = async () => {
    try {
      const result = await authListUsers();
      setUsers(result.users || []);
    } catch {
      console.error('Error loading users');
    } finally {
      setLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    try {
      const { data } = await api.get('/api/reconocimiento/audit-log');
      setAuditLogs(data.logs || []);
    } catch {
      console.error('Error loading audit logs');
    } finally {
      setAuditLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!form.name || !form.email || !form.password) return;
    try {
      await authRegister(form.name, form.email, form.password, form.role);
      setForm({ name: '', email: '', password: '', role: 'operador' });
      setShowModal(false);
      loadUsers();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al crear usuario';
      setError(msg);
      console.error('Error creating user:', msg);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await authDeleteUser(id);
      setUsers((p) => p.filter((u) => u.id !== id));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al eliminar';
      setError(msg);
      console.error('Error deleting user:', msg);
    }
  };

  const handleRoleChange = async (userId: string, newRole: Role) => {
    try {
      await authChangeRole(userId, newRole);
      setUsers((p) => p.map((u) => u.id === userId ? { ...u, role: newRole } : u));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cambiar rol';
      setError(msg);
      console.error('Error changing role:', msg);
    }
  };

  const getRoleIcon = (role: Role) => {
    if (role === 'admin') return <Shield size={14} />;
    if (role === 'operador') return <Fingerprint size={14} />;
    return <Brain size={14} />;
  };

  if (loading) {
    return <div className="loading">Cargando usuarios...</div>;
  }

  return (
    <div className="seguridad">
      <div className="seg-header">
        <div className="seg-info"><Shield size={18} /><span>Gestion de usuarios, roles, permisos y control de acceso</span></div>
        <button className="seg-add-btn" onClick={() => setShowModal(true)}><UserPlus size={16} /> Nuevo Usuario</button>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Crear Usuario</h3>
            <div className="modal-form">
              <input type="text" placeholder="Nombre completo" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <input type="email" placeholder="Correo electronico" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <input type="password" placeholder="Contrasena" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
              <div className="seg-role-select">
                <label>Rol</label>
                <div className="seg-role-options">
                  {(Object.entries(ROLE_LABELS) as [Role, string][]).map(([key, label]) => (
                    <button key={key} className={`seg-role-opt ${form.role === key ? 'active' : ''}`} onClick={() => setForm({ ...form, role: key })} type="button">
                      {getRoleIcon(key)} {label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="seg-role-desc">
                {form.role === 'admin' && 'Gobernar el sistema: usuarios, roles, umbral, auditoria y retencion de datos. Acceso total.'}
                {form.role === 'operador' && 'Trabajo diario: registrar personas, ejecutar reconocimientos y ver historial.'}
                {form.role === 'analista' && 'Mejorar el modelo: revisar resultados, analizar probabilidades, entrenar y calibrar.'}
              </div>
              <div className="modal-actions">
                <button className="cancel-btn" onClick={() => setShowModal(false)}>Cancelar</button>
                <button className="confirm-btn" onClick={handleAdd}>Crear</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <Card title={`Usuarios (${users.length})`}>
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-4 text-red-700 dark:text-red-400 text-sm flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => setError('')} className="text-red-500 hover:text-red-700 font-bold ml-2">X</button>
          </div>
        )}
        <div className="seg-table-wrap">
          <table className="seg-table">
            <thead><tr><th>Usuario</th><th>Correo</th><th>Rol</th><th>Permisos</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="seg-name-cell"><div className="seg-name-inner"><div className="seg-avatar">{u.name.charAt(0)}</div>{u.name}</div></td>
                  <td>{u.email}</td>
                  <td>
                    <select
                      className={`seg-role-select-dropdown role-${u.role}`}
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value as Role)}
                    >
                      {(Object.entries(ROLE_LABELS) as [Role, string][]).map(([key, label]) => (
                        <option key={key} value={key}>{label}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <div className="seg-perms">
                      {u.role === 'admin' && <span className="seg-perm">Todo</span>}
                      {u.role === 'operador' && <><span className="seg-perm">Registro</span><span className="seg-perm">Reconocimiento</span></>}
                      {u.role === 'analista' && <><span className="seg-perm">Probabilidades</span><span className="seg-perm">ML</span></>}
                    </div>
                  </td>
                  <td><span className={`seg-dot ${u.active ? 'on' : 'off'}`} />{u.active ? 'Activo' : 'Inactivo'}</td>
                  <td className="seg-actions">
                    <button className="seg-del-btn" onClick={() => { if (window.confirm('¿Eliminar este usuario permanentemente?')) handleDelete(u.id); }} title="Eliminar"><Trash2 size={14} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Carga masiva de imagenes">
        <p className="text-sm text-gray-600 dark:text-[var(--text)] mb-3">
          Selecciona varias imagenes de golpe y cargalas a la base de datos. Se optimizan automaticamente (JPG, PNG, WEBP, AVIF). Todas deben tener un rostro visible.
        </p>
        <div className="flex flex-wrap gap-2 mb-3">
          <button
            onClick={() => setRegTipo('real')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${regTipo === 'real' ? 'bg-green-600 text-white' : 'bg-gray-100 dark:bg-[var(--code-bg)] text-gray-600 dark:text-[var(--text)]'}`}
          >
            <CheckCircle size={16} /> Humano Real
          </button>
          <button
            onClick={() => setRegTipo('ia')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${regTipo === 'ia' ? 'bg-purple-600 text-white' : 'bg-gray-100 dark:bg-[var(--code-bg)] text-gray-600 dark:text-[var(--text)]'}`}
          >
            <XCircle size={16} /> No Real (IA)
          </button>
        </div>
        <div className="p-3 mb-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-xs text-blue-700 dark:text-blue-300">
          {regTipo === 'real'
            ? 'Humano Real: cada foto REGISTRA a la persona (aparece en Historial, 1:N, etc.), queda confirmada y crea un ejemplo POSITIVO para el ML. Tip: sube varias fotos de la MISMA persona real para dar similitud alta.'
            : 'No Real (IA): cada foto se registra (etiqueta IA, aparece en todas las paginas), queda confirmada y crea un ejemplo NEGATIVO para el ML. Usa caras de IA (thispersondoesnotexist). Solo rostros: carros/animales no sirven.'}
        </div>
        <input ref={batchInputRef} type="file" accept="image/*" multiple onChange={handleBatchFiles} className="hidden" />
        <button
          onClick={() => batchInputRef.current?.click()}
          disabled={batchRunning}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {batchRunning ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" /> : <Upload size={18} />}
          {batchRunning ? 'Procesando...' : 'Seleccionar imagenes y cargar'}
        </button>

        {batchResults.length > 0 && !batchRunning && (
          <div className="mt-3 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-sm text-green-800 dark:text-green-300">
            <strong>{batchResults.filter((r) => r.ok).length} cargadas</strong>
            {batchResults.filter((r) => !r.ok).length > 0 && `, ${batchResults.filter((r) => !r.ok).length} con problema`}.
            {' '}Aparecen en Historial y 1:N, y como dato en Entrenamiento ML (Positivos / Negativos).
          </div>
        )}
        {batchResults.length > 0 && (
          <div className="mt-3 max-h-72 overflow-y-auto border border-gray-200 dark:border-[var(--border)] rounded-lg divide-y divide-gray-100 dark:divide-[var(--border)]">
            {batchResults.map((r, i) => (
              <div key={i} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                <span className="flex items-center gap-2 text-gray-700 dark:text-[var(--text)] truncate">
                  <Images size={14} className="shrink-0" /> <span className="truncate">{r.name}</span>
                </span>
                <span className={`text-xs font-medium shrink-0 ${r.ok ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Matriz de Permisos">
        <div className="seg-matrix-wrap">
          <table className="seg-matrix">
            <thead><tr><th>Funcion</th><th>Administrador</th><th>Operador</th><th>Analista ML</th></tr></thead>
            <tbody>
              <tr><td>Dashboard</td><td className="perm-yes">Si</td><td className="perm-yes">Si</td><td className="perm-yes">Si</td></tr>
              <tr><td>Registro Facial</td><td className="perm-yes">Si</td><td className="perm-yes">Si</td><td className="perm-no">No</td></tr>
              <tr><td>Reconocimiento</td><td className="perm-yes">Si</td><td className="perm-yes">Si</td><td className="perm-no">No</td></tr>
              <tr><td>Probabilidades</td><td className="perm-yes">Si</td><td className="perm-no">No</td><td className="perm-yes">Si</td></tr>
              <tr><td>Historial</td><td className="perm-yes">Si</td><td className="perm-yes">Si</td><td className="perm-yes">Si</td></tr>
              <tr><td>Entrenamiento ML</td><td className="perm-yes">Si</td><td className="perm-no">No</td><td className="perm-yes">Si</td></tr>
              <tr><td>Seguridad</td><td className="perm-yes">Si</td><td className="perm-no">No</td><td className="perm-no">No</td></tr>
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Log de Auditoria (ultimos 50 registros)">
        {auditLoading ? (
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
          </div>
        ) : auditLogs.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-[var(--text)] py-4">No hay registros de auditoria</p>
        ) : (
          <div className="seg-table-wrap">
            <table className="seg-table">
              <thead><tr><th>Fecha</th><th>Persona</th><th>Similitud</th><th>Distancia</th><th>Umbral</th><th>Resultado</th><th>Confirmado</th></tr></thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="text-xs">{new Date(log.created_at).toLocaleString('es-PE')}</td>
                    <td className="text-sm font-medium">{log.personas?.nombre || '-'}</td>
                    <td className="text-sm font-mono">{(log.similitud * 100).toFixed(1)}%</td>
                    <td className="text-sm font-mono">{log.distancia.toFixed(4)}</td>
                    <td className="text-sm font-mono">{log.umbral}</td>
                    <td>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${log.coincide ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                        {log.coincide ? 'Si' : 'No'}
                      </span>
                    </td>
                    <td>
                      {log.resultado_real != null ? (
                        <span className={`text-xs font-medium ${log.resultado_real ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                          {log.resultado_real ? 'Correcto' : 'Incorrecto'}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400 dark:text-[var(--text)]">Pendiente</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
