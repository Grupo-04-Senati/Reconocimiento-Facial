import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { getSession } from '../store';
import { ROLE_LABELS } from '../types';
import './Header.css';

export function Header() {
  const { theme, toggleTheme } = useTheme();
  const session = getSession();

  return (
    <header className="header">
      <div className="header-title">
        <h2>Panel de Administracion</h2>
      </div>
      <div className="header-actions">
        <button className="theme-toggle" onClick={toggleTheme} title={theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}>
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <div className="header-user-info">
          <img src="/logo.png" alt="" className="header-user-avatar" />
          <span className="header-user-badge">
            {ROLE_LABELS[session?.role ?? 'operador']}
          </span>
        </div>
      </div>
    </header>
  );
}
