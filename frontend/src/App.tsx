import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { Sidebar, Header } from './components';
import { ChatBot } from './components/ChatBot';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login, Dashboard, RegistroFacial, Reconocimiento, Probabilidades, Historial, EntrenamientoML, Seguridad } from './pages';
import { getSession } from './store';
import './App.css';

function AppInner() {
  const [, setSessionTick] = useState(0);
  const session = getSession();
  const isLoggedIn = !!session;
  const [showVida, setShowVida] = useState(false);
  const [showG, setShowG] = useState(false);
  const [show0, setShow0] = useState(false);

  const handleAuth = () => setSessionTick((t) => t + 1);

  const handleSecretKey = useCallback((e: KeyboardEvent) => {
    const target = e.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) return;
    if (e.ctrlKey || e.altKey || e.metaKey) return;

    if (e.key === 'f') {
      setShowVida(true);
      setTimeout(() => setShowVida(false), 2000);
    } else if (e.key === 'g') {
      setShowG(true);
      setTimeout(() => setShowG(false), 1000);
    } else if (e.key === '0') {
      setShow0(true);
      setTimeout(() => setShow0(false), 1000);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleSecretKey);
    return () => window.removeEventListener('keydown', handleSecretKey);
  }, [handleSecretKey]);

  if (!isLoggedIn) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLogin={handleAuth} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar onLogout={handleAuth} />
      <div className="main-area">
        <Header />
        <main className="main-content">
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<Dashboard />} />
            </Route>
            <Route element={<ProtectedRoute allowedRoles={['admin', 'operador']} />}>
              <Route path="/registro" element={<RegistroFacial />} />
              <Route path="/reconocimiento" element={<Reconocimiento />} />
            </Route>
            <Route element={<ProtectedRoute allowedRoles={['admin', 'analista']} />}>
              <Route path="/probabilidades" element={<Probabilidades />} />
              <Route path="/entrenamiento" element={<EntrenamientoML />} />
            </Route>
            <Route element={<ProtectedRoute allowedRoles={['admin', 'operador', 'analista']} />}>
              <Route path="/historial" element={<Historial />} />
            </Route>
            <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
              <Route path="/seguridad" element={<Seguridad />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
      <ChatBot />

      {showVida && (
        <div className="vida-overlay">
          <img src="/vida.png" alt="vida" className="vida-img" />
        </div>
      )}
      {showG && (
        <div className="secret-overlay">
          <img src="/img/G.png" alt="G" className="secret-img" />
        </div>
      )}
      {show0 && (
        <div className="secret-overlay">
          <img src="/img/0.png" alt="0" className="secret-img" />
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppInner />
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
