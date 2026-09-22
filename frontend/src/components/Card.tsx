import type { ReactNode } from 'react';
import './Card.css';

interface CardProps {
  title: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function Card({ title, children, action, className = '' }: CardProps) {
  return (
    <div className={`card ${className}`}>
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
        {action && <div className="card-action">{action}</div>}
      </div>
      <div className="card-body">{children}</div>
    </div>
  );
}
