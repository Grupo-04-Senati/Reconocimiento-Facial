import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface ProbabilityChartProps {
  data: { name: string; value: number }[];
}

const COLORS = ['#2563eb', '#60a5fa', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6'];

export function ProbabilityChart({ data }: ProbabilityChartProps) {
  if (data.length === 0) {
    return (
      <div className="prob-chart-empty">
        <p>Sin datos para mostrar</p>
      </div>
    );
  }

  return (
    <div className="probability-chart">
      <div className="prob-chart-bar">
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="name" stroke="var(--text)" fontSize={12} />
            <YAxis stroke="var(--text)" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: 'var(--code-bg)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-h)' }} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="prob-chart-pie">
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" outerRadius={90} dataKey="value"
              label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ''} ${((percent ?? 0) * 100).toFixed(0)}%`}>
              {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
