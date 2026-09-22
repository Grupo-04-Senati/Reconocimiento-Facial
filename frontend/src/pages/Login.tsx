import { useState } from 'react';
import { LogIn, UserPlus, AlertCircle, CheckCircle } from 'lucide-react';
import { loginUser, registerUser } from '../store';
import './Login.css';

interface LoginProps {
  onLogin: () => void;
}

export function Login({ onLogin }: LoginProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('operador');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setName('');
    setRole('operador');
    setError('');
    setSuccess('');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('Completa todos los campos');
      return;
    }
    setLoading(true);
    try {
      const session = await loginUser(email, password);
      if (!session) {
        setError('Credenciales incorrectas o usuario inactivo');
        return;
      }
      onLogin();
    } catch {
      setError('Error de conexion con el servidor');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (!name || !email || !password) {
      setError('Completa todos los campos');
      return;
    }
    if (password.length < 6) {
      setError('La contrasena debe tener al menos 6 caracteres');
      return;
    }
    setLoading(true);
    try {
      const result = await registerUser(name, email, password, role);
      if (!result.success) {
        setError(result.error || 'Error al registrar');
        return;
      }
      setSuccess('Cuenta creada correctamente. Ahora puedes iniciar sesion.');
      resetForm();
      setTimeout(() => {
        setMode('login');
        setSuccess('');
      }, 2000);
    } catch {
      setError('Error de conexion con el servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-bg-decoration">
        <img src="/img/sage.png" alt="" className="login-bg-img" />
      </div>
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo-wrap">
            <img src="/logo.png" alt="Badicorp" className="login-logo-img" />
          </div>
          <h1>Badicorp</h1>
          <p>Sistema de Reconocimiento Facial</p>
        </div>

        <div className="login-tabs">
          <button className={`tab ${mode === 'login' ? 'active' : ''}`} onClick={() => { resetForm(); setMode('login'); }} type="button">
            <LogIn size={16} /> Iniciar Sesion
          </button>
          <button className={`tab ${mode === 'register' ? 'active' : ''}`} onClick={() => { resetForm(); setMode('register'); }} type="button">
            <UserPlus size={16} /> Registrarse
          </button>
        </div>

        {mode === 'login' ? (
          <form onSubmit={handleLogin} className="login-form">
            {error && <div className="login-error"><AlertCircle size={16} />{error}</div>}
            {success && <div className="login-success"><CheckCircle size={16} />{success}</div>}
            <div className="field">
              <label htmlFor="email">Correo electronico</label>
              <input id="email" type="email" placeholder="tu@correo.com" value={email} onChange={(e) => setEmail(e.target.value)} autoFocus />
            </div>
            <div className="field">
              <label htmlFor="password">Contrasena</label>
              <input id="password" type="password" placeholder="Ingresa tu contrasena" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <button type="submit" className="login-btn" disabled={loading}>
              <LogIn size={18} />
              {loading ? 'Conectando...' : 'Iniciar Sesion'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegister} className="login-form">
            {error && <div className="login-error"><AlertCircle size={16} />{error}</div>}
            {success && <div className="login-success"><CheckCircle size={16} />{success}</div>}
            <div className="field">
              <label htmlFor="reg-name">Nombre completo</label>
              <input id="reg-name" type="text" placeholder="Tu nombre" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
            </div>
            <div className="field">
              <label htmlFor="reg-email">Correo electronico</label>
              <input id="reg-email" type="email" placeholder="tu@correo.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="reg-password">Contrasena</label>
              <input id="reg-password" type="password" placeholder="Minimo 6 caracteres" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="reg-role">Rol</label>
              <select id="reg-role" value={role} onChange={(e) => setRole(e.target.value)} style={{
                padding: '11px 14px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                background: 'var(--bg)',
                color: 'var(--text-h)',
                fontSize: '14px',
                outline: 'none',
                cursor: 'pointer',
              }}>
                <option value="operador">Operador - Registro y reconocimiento</option>
                <option value="analista">Analista - Probabilidades y entrenamiento</option>
                <option value="admin">Administrador - Acceso total</option>
              </select>
            </div>
            <button type="submit" className="login-btn register" disabled={loading}>
              <UserPlus size={18} />
              {loading ? 'Creando...' : 'Crear Cuenta'}
            </button>
          </form>
        )}

        <div className="login-footer">
          <img src="/logo.png" alt="" style={{ width: 14, height: 14, opacity: 0.6 }} />
          <span>Badicorp - Panel de Administracion</span>
        </div>
      </div>
    </div>
  );
}
