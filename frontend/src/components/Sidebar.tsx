import { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, ScanFace, Fingerprint, BarChart3, History, Brain, Shield, LogOut, Menu, X } from 'lucide-react';
import { getSession, logoutUser, hasPermission } from '../store';
import type { Role } from '../types';
import { ROLE_LABELS } from '../types';
import './Sidebar.css';

const allNavItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, permission: 'dashboard' },
  { to: '/registro', label: 'Registro Facial', icon: ScanFace, permission: 'registro' },
  { to: '/reconocimiento', label: 'Reconocimiento', icon: Fingerprint, permission: 'reconocimiento' },
  { to: '/probabilidades', label: 'Probabilidades', icon: BarChart3, permission: 'probabilidades' },
  { to: '/historial', label: 'Historial', icon: History, permission: 'historial' },
  { to: '/entrenamiento', label: 'Entrenamiento ML', icon: Brain, permission: 'entrenamiento' },
  { to: '/seguridad', label: 'Seguridad', icon: Shield, permission: 'seguridad' },
];

interface SidebarProps {
  onLogout: () => void;
}

export function Sidebar({ onLogout }: SidebarProps) {
  const session = getSession();
  const navigate = useNavigate();
  const role: Role = session?.role ?? 'operador';
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = allNavItems.filter((item) => hasPermission(role, item.permission));

  const handleLogout = () => {
    logoutUser();
    onLogout();
    navigate('/login');
  };

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  return (
    <>
      <button
        className="mobile-menu-btn"
        onClick={() => setMobileOpen(true)}
        style={{
          display: 'none',
          position: 'fixed',
          top: 14,
          left: 14,
          zIndex: 200,
          width: 40,
          height: 40,
          borderRadius: 10,
          border: '1px solid var(--border)',
          background: 'var(--code-bg)',
          color: 'var(--text-h)',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
        }}
      >
        <Menu size={20} />
      </button>

      <div className={`sidebar-overlay ${mobileOpen ? 'visible' : ''}`} onClick={() => setMobileOpen(false)} />

      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo-wrap">
            <img src="/logo.png" alt="Badicorp" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
          </div>
          <div style={{ flex: 1 }}>
            <span className="sidebar-title">Badicorp</span>
            <span className="sidebar-role">{ROLE_LABELS[role]}</span>
          </div>
          <button
            onClick={() => setMobileOpen(false)}
            style={{
              display: 'none',
              background: 'none',
              border: 'none',
              color: 'var(--text)',
              cursor: 'pointer',
              padding: 4,
            }}
            className="sidebar-close-btn"
          >
            <X size={20} />
          </button>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === '/'}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              onClick={() => setMobileOpen(false)}>
              <item.icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="user-avatar-sm">{session?.name?.charAt(0) ?? '?'}</div>
            <div className="user-info">
              <span className="user-name">{session?.name}</span>
              <span className="user-email">{session?.email}</span>
            </div>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            <LogOut size={16} />
            Cerrar Sesion
          </button>
        </div>
      </aside>

      <style>{`
        @media (max-width: 1024px) {
          .mobile-menu-btn { display: flex !important; }
          .sidebar-close-btn { display: block !important; }
        }
      `}</style>
    </>
  );
}
