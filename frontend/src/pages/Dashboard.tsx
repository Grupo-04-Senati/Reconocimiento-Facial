import { useState, useEffect } from 'react';
import { Users, Scan, AlertCircle, UserCheck, TrendingUp, Brain, Zap, Eye } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts';
import { dashboardStats } from '../services/api';

interface DashboardData {
  resumen: {
    total_personas: number;
    total_embeddings: number;
    total_reconocimientos: number;
    total_coincidencias: number;
    tasa_exito: number;
    confirmados_correctos: number;
    confirmados_incorrectos: number;
  };
  modelo_ml: {
    estado: string;
    clase: string | null;
    registros_totales: number;
    registros_positivos: number;
    registros_negativos: number;
  };
  servicios: {
    face_detection: string;
    probability_model: string;
    supabase: string;
  };
  reconocimientos_por_dia: Array<{
    fecha: string;
    total: number;
    positivos: number;
    negativos: number;
  }>;
}

const COLORS = ['#22c55e', '#ef4444', '#f59e0b', '#3b82f6'];

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await dashboardStats();
      setData(result);
    } catch (err) {
      console.error('Dashboard error:', err);
      setError('Error cargando estadisticas del backend');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <img src="/img/sage.png" alt="Sage" className="w-10 h-10 rounded-xl object-cover" />
          <h1 className="text-3xl font-bold text-gray-800 dark:text-[var(--text-h)]">Dashboard</h1>
        </div>
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="text-yellow-600 dark:text-yellow-400 mt-0.5" size={20} />
          <div>
            <p className="font-medium text-yellow-800 dark:text-yellow-300">Backend no disponible</p>
            <p className="text-sm text-yellow-600 dark:text-yellow-400">{error}</p>
            <button onClick={loadStats} className="mt-2 text-sm text-yellow-700 dark:text-yellow-300 underline">Reintentar</button>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { resumen, modelo_ml, servicios, reconocimientos_por_dia } = data;

  // Chart data: pie for confirmados
  const pieData = [
    { name: 'Correctos', value: resumen.confirmados_correctos || 0 },
    { name: 'Incorrectos', value: resumen.confirmados_incorrectos || 0 },
    { name: 'Sin confirmar', value: Math.max(0, resumen.total_reconocimientos - resumen.confirmados_correctos - resumen.confirmados_incorrectos) },
  ].filter((d) => d.value > 0);

  // Chart data: ML records distribution
  const mlPieData = [
    { name: 'Positivos (TRUE)', value: modelo_ml.registros_positivos },
    { name: 'Negativos (FALSE)', value: modelo_ml.registros_negativos },
  ].filter((d) => d.value > 0);

  const getStatusColor = (status: string) => {
    if (status === 'activo' || status === 'conectado') return 'text-green-600 dark:text-green-400';
    if (status === 'cargando' || status === 'fallback') return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getStatusBg = (status: string) => {
    if (status === 'activo' || status === 'conectado') return 'bg-green-100 dark:bg-green-900/30';
    if (status === 'cargando' || status === 'fallback') return 'bg-yellow-100 dark:bg-yellow-900/30';
    return 'bg-red-100 dark:bg-red-900/30';
  };

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl p-6 md:p-8 text-white">
        <div className="absolute top-0 right-0 w-64 h-64 opacity-10">
          <img src="/img/sage.png" alt="" className="w-full h-full object-contain" />
        </div>
        <div className="relative z-10 flex items-center gap-4">
          <img src="/img/sage.png" alt="Sage" className="w-16 h-16 rounded-2xl object-cover border-2 border-white/30 shadow-lg hidden sm:block" />
          <div>
            <h1 className="text-2xl md:text-3xl font-bold mb-1">Dashboard</h1>
            <p className="text-blue-100 text-sm md:text-base">Monitoreo en tiempo real del sistema de reconocimiento facial</p>
          </div>
        </div>
        <div className="absolute bottom-4 right-6">
          <button onClick={loadStats} className="text-sm text-white/80 hover:text-white underline transition-colors">
            Actualizar datos
          </button>
        </div>
      </div>

      {/* ═══ KPI Cards ═══ */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-5 border border-gray-200 dark:border-[var(--border)] shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
              <UserCheck className="text-blue-600 dark:text-blue-400" size={24} />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-[var(--text)] uppercase tracking-wide">Personas</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-[var(--text-h)]">{resumen.total_personas}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-5 border border-gray-200 dark:border-[var(--border)] shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-indigo-100 dark:bg-indigo-900/30 rounded-xl">
              <Scan className="text-indigo-600 dark:text-indigo-400" size={24} />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-[var(--text)] uppercase tracking-wide">Reconocimientos</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-[var(--text-h)]">{resumen.total_reconocimientos}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-5 border border-gray-200 dark:border-[var(--border)] shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-xl">
              <TrendingUp className="text-green-600 dark:text-green-400" size={24} />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-[var(--text)] uppercase tracking-wide">Tasa de Exito</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-[var(--text-h)]">{(resumen.tasa_exito * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-5 border border-gray-200 dark:border-[var(--border)] shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
              <Users className="text-purple-600 dark:text-purple-400" size={24} />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-[var(--text)] uppercase tracking-wide">Embeddings</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-[var(--text-h)]">{resumen.total_embeddings}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ═══ Model Status ═══ */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className={`rounded-xl p-4 border shadow-sm flex items-center gap-4 ${getStatusBg(servicios.face_detection)} border-gray-200 dark:border-[var(--border)]`}>
          <div className={`p-3 rounded-xl ${getStatusBg(servicios.face_detection)}`}>
            <Eye size={24} className={getStatusColor(servicios.face_detection)} />
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-[var(--text)] uppercase tracking-wide">Face Detection (DL)</p>
            <p className={`text-sm font-bold capitalize ${getStatusColor(servicios.face_detection)}`}>{servicios.face_detection}</p>
            <p className="text-xs text-gray-400">InsightFace buffalo_s</p>
          </div>
        </div>
        <div className={`rounded-xl p-4 border shadow-sm flex items-center gap-4 ${getStatusBg(servicios.probability_model)} border-gray-200 dark:border-[var(--border)]`}>
          <div className={`p-3 rounded-xl ${getStatusBg(servicios.probability_model)}`}>
            <Brain size={24} className={getStatusColor(servicios.probability_model)} />
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-[var(--text)] uppercase tracking-wide">Probability Model (ML)</p>
            <p className={`text-sm font-bold capitalize ${getStatusColor(servicios.probability_model)}`}>{servicios.probability_model}</p>
            <p className="text-xs text-gray-400">{modelo_ml.clase || 'Sin entrenar'}</p>
          </div>
        </div>
        <div className={`rounded-xl p-4 border shadow-sm flex items-center gap-4 ${getStatusBg(servicios.supabase)} border-gray-200 dark:border-[var(--border)]`}>
          <div className={`p-3 rounded-xl ${getStatusBg(servicios.supabase)}`}>
            <Zap size={24} className={getStatusColor(servicios.supabase)} />
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-[var(--text)] uppercase tracking-wide">Database</p>
            <p className={`text-sm font-bold capitalize ${getStatusColor(servicios.supabase)}`}>{servicios.supabase}</p>
            <p className="text-xs text-gray-400">Supabase + pgvector</p>
          </div>
        </div>
      </div>

      {/* ═══ Charts ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Reconocimientos por dia */}
        <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-6 border border-gray-200 dark:border-[var(--border)] shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Scan size={18} className="text-blue-600 dark:text-blue-400" />
            </div>
            <h2 className="text-lg font-bold text-gray-800 dark:text-[var(--text-h)]">Reconocimientos por Dia</h2>
          </div>
          {reconocimientos_por_dia.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={reconocimientos_por_dia}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="fecha" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="positivos" name="Coincidencias" fill="#22c55e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="negativos" name="Sin coincidencia" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-gray-500 text-center py-12">Sin datos de reconocimientos</p>
          )}
        </div>

        {/* Chart 2: Confirmaciones (Pie) */}
        <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-6 border border-gray-200 dark:border-[var(--border)] shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <UserCheck size={18} className="text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-lg font-bold text-gray-800 dark:text-[var(--text-h)]">Confirmaciones</h2>
          </div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }: { name?: string; percent?: number }) => `${name || ''} ${((percent || 0) * 100).toFixed(0)}%`}
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-gray-500 text-center py-12">Sin confirmaciones registradas</p>
          )}
        </div>

        {/* Chart 3: ML Dataset Distribution */}
        <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-6 border border-gray-200 dark:border-[var(--border)] shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Brain size={18} className="text-purple-600 dark:text-purple-400" />
              </div>
              <h2 className="text-lg font-bold text-gray-800 dark:text-[var(--text-h)]">Dataset ML</h2>
            </div>
            <span className={`text-xs px-3 py-1 rounded-full font-medium ${modelo_ml.estado === 'activo' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'}`}>
              {modelo_ml.estado === 'activo' ? 'Entrenado' : 'Sin entrenar'}
            </span>
          </div>
          {mlPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={mlPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }: { name?: string; percent?: number }) => `${name || ''} ${((percent || 0) * 100).toFixed(0)}%`}
                >
                  <Cell fill="#22c55e" />
                  <Cell fill="#ef4444" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-gray-500 text-center py-8">Sin registros de entrenamiento</p>
          )}
          <div className="flex justify-center gap-6 mt-2 text-xs text-gray-600 dark:text-[var(--text)]">
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-green-500" /> Positivos: {modelo_ml.registros_positivos}</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-red-500" /> Negativos: {modelo_ml.registros_negativos}</span>
          </div>
        </div>

        {/* Chart 4: Line chart trend */}
        <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-6 border border-gray-200 dark:border-[var(--border)] shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
              <TrendingUp size={18} className="text-orange-600 dark:text-orange-400" />
            </div>
            <h2 className="text-lg font-bold text-gray-800 dark:text-[var(--text-h)]">Tendencia</h2>
          </div>
          {reconocimientos_por_dia.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={reconocimientos_por_dia}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="fecha" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="total" name="Total" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="positivos" name="Positivos" stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-gray-500 text-center py-12">Sin datos de tendencia</p>
          )}
        </div>
      </div>

      {/* ═══ ML Training Info ═══ */}
      <div className="bg-white dark:bg-[var(--code-bg)] rounded-xl p-6 border border-gray-200 dark:border-[var(--border)] shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
            <Brain size={18} className="text-indigo-600 dark:text-indigo-400" />
          </div>
          <h2 className="text-lg font-bold text-gray-800 dark:text-[var(--text-h)]">Estado del Sistema ML/DL</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="p-3 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
            <span className="text-gray-500 dark:text-[var(--text)] text-xs uppercase tracking-wide">Modelo ML</span>
            <p className={`font-bold mt-1 ${getStatusColor(servicios.probability_model)}`}>{modelo_ml.clase || 'No entrenado'}</p>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
            <span className="text-gray-500 dark:text-[var(--text)] text-xs uppercase tracking-wide">Modelo DL</span>
            <p className={`font-bold mt-1 ${getStatusColor(servicios.face_detection)}`}>InsightFace buffalo_s</p>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
            <span className="text-gray-500 dark:text-[var(--text)] text-xs uppercase tracking-wide">Vectores Faciales</span>
            <p className="font-bold mt-1 text-gray-800 dark:text-[var(--text-h)]">{resumen.total_embeddings} embeddings (512 dim)</p>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-[var(--bg)] rounded-lg">
            <span className="text-gray-500 dark:text-[var(--text)] text-xs uppercase tracking-wide">Indice</span>
            <p className="font-bold mt-1 text-gray-800 dark:text-[var(--text-h)]">HNSW (m=16, ef=64)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
