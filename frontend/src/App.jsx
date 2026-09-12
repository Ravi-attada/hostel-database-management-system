import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Home, Users, LayoutDashboard, Wallet, CreditCard, Building2, Bell, Moon, Sun } from 'lucide-react';
import { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import MonthlyRent from './pages/MonthlyRent';
import Rooms from './pages/Rooms';
import AddStudent from './pages/AddStudent';

function Sidebar() {
  const location = useLocation();
  const isActive = (path) => location.pathname === path || (path === '/rooms' && location.pathname.startsWith('/floor'));

  const linkClass = (path) => `flex items-center px-4 py-3 rounded-xl font-medium transition-all duration-300 ${isActive(path) ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 scale-[1.02]' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-500/10 hover:scale-[1.02]'}`;

  return (
    <aside className="w-64 glass-panel border-r border-white/20 dark:border-slate-700/50 flex flex-col z-20 relative transition-all duration-500">
      <div className="h-20 flex items-center px-6 border-b border-slate-200/50 dark:border-slate-700/50">
        <div className="bg-gradient-to-tr from-blue-600 to-indigo-500 p-2 rounded-lg mr-3 shadow-lg shadow-blue-500/30">
          <Building2 className="text-white w-5 h-5 animate-pulse" />
        </div>
        <h1 className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-slate-800 to-slate-600 dark:from-white dark:to-slate-300">Bhavani Residency</h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        <Link to="/" className={linkClass('/')}>
          <LayoutDashboard className="w-5 h-5 mr-3" /> Dashboard
        </Link>
        <Link to="/rent" className={linkClass('/rent')}>
          <Wallet className="w-5 h-5 mr-3" /> Monthly Rent
        </Link>
        <Link to="/rooms" className={linkClass('/rooms')}>
          <Home className="w-5 h-5 mr-3" /> Rooms
        </Link>
        <Link to="/add-student" className={linkClass('/add-student')}>
          <Users className="w-5 h-5 mr-3" /> Add Student
        </Link>
        <a href="http://localhost:5000/rent-config" className="flex items-center px-4 py-3 text-slate-600 dark:text-slate-300 hover:bg-slate-500/10 hover:scale-[1.02] rounded-xl font-medium transition-all duration-300">
          <CreditCard className="w-5 h-5 mr-3" /> Rent Rates
        </a>
      </nav>
    </aside>
  );
}

export default function App() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <Router>
      <div className={`min-h-screen flex transition-colors duration-500 ${theme === 'dark' ? 'bg-mesh-dark' : 'bg-mesh-light'}`}>
        <Sidebar />

        {/* Main Content */}
        <main className="flex-1 flex flex-col h-screen overflow-y-auto relative z-10 transition-colors duration-500">
          <header className="h-20 glass-panel border-b border-white/20 dark:border-slate-700/50 flex items-center justify-between px-8 sticky top-0 z-10 shadow-sm transition-all duration-500">
            <h2 className="text-xl font-bold text-slate-800 dark:text-white tracking-tight animate-in slide-in-from-left-4 duration-500">Overview</h2>
            <div className="flex items-center space-x-4 animate-in slide-in-from-right-4 duration-500">
              <button onClick={toggleTheme} className="p-2.5 glass-card rounded-full text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-all hover:rotate-12">
                {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
              </button>
              <button className="p-2.5 glass-card rounded-full text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-all hover:rotate-12">
                <Bell className="w-5 h-5" />
              </button>
              <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-indigo-500 text-white rounded-full flex items-center justify-center font-bold shadow-lg shadow-blue-500/30 border-2 border-white dark:border-slate-800 hover:scale-110 transition-transform">
                A
              </div>
            </div>
          </header>
          <div className="p-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/rent" element={<MonthlyRent />} />
              <Route path="/rooms" element={<Rooms />} />
              <Route path="/add-student" element={<AddStudent />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}
