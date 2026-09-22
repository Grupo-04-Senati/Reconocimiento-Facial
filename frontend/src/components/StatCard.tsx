import type { ReactNode } from 'react';
import './StatCard.css';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  color?: string;
  trend?: string;
}

export function StatCard({ title, value, icon, color = 'var(--accent)', trend }: StatCardProps) {
  return (
    <div className="stat-card" style={{ '--card-accent': color } as React.CSSProperties}>
      <div className="stat-card-icon">{icon}</div>
      <div className="stat-card-content">
        <span className="stat-card-value">{value}</span>
        <span className="stat-card-title">{title}</span>
        {trend && <span className="stat-card-trend">{trend}</span>}
      </div>
    </div>
  );
}
