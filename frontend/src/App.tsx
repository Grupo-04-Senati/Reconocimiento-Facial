import React from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, UserPlus, Scan, BarChart3, History } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import RegistroFacial from './pages/RegistroFacial'
import Reconocimiento from './pages/Reconocimiento'
import Probabilidades from './pages/Probabilidades'
import Historial from './pages/Historial'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/registro', icon: UserPlus, label: 'Registro' },
  { to: '/reconocimiento', icon: Scan, label: 'Reconocimiento' },
  { to: '/probabilidades', icon: BarChart3, label: 'Probabilidades' },
  { to: '/historial', icon: History, label: 'Historial' },
]

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-2">
                <Scan className="text-blue-600" size={24} />
                <span className="font-bold text-lg text-gray-800 hidden sm:block">
                  Reconocimiento Facial
                </span>
              </div>
              <div className="flex items-center gap-1">
                {navItems.map(({ to, icon: Icon, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    className={({ isActive }) =>
                      `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-blue-50 text-blue-600'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                      }`
                    }
                  >
                    <Icon size={18} />
                    <span className="hidden md:inline">{label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/registro" element={<RegistroFacial />} />
            <Route path="/reconocimiento" element={<Reconocimiento />} />
            <Route path="/probabilidades" element={<Probabilidades />} />
            <Route path="/historial" element={<Historial />} />
          </Routes>
        </main>

        <footer className="border-t border-gray-200 bg-white mt-8">
          <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
            Sistema de Reconocimiento Facial - Grupo 04 Senati 2026
          </div>
        </footer>
      </div>
    </Router>
  )
}

export default App
