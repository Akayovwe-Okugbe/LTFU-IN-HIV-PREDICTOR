import { Bell, BrainCircuit, ClipboardList, Gauge, LogOut, MessageSquare, Settings, Stethoscope, Users } from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';
import { Brand } from './Brand';
import { useAuth } from '../context/AuthContext';

export function AppShell() {
  const { user, logout } = useAuth();
  const common = [
    { to: '/app', label: 'Overview', icon: Gauge, end: true },
    { to: '/app/messages', label: 'Messages', icon: MessageSquare },
    { to: '/app/settings', label: 'Settings', icon: Settings },
  ];
  const clinician = [
    { to: '/app/patients', label: 'Patients', icon: Stethoscope },
    { to: '/app/predictions', label: 'Predictions', icon: BrainCircuit },
    { to: '/app/change-requests', label: 'Change Requests', icon: ClipboardList },
  ];
  const admin = [{ to: '/app/administration', label: 'Administration', icon: Users }];
  const links = user?.role === 'ADMINISTRATOR' ? [...common, ...admin] : user?.role === 'CLINICIAN' ? [...common, ...clinician] : common;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Brand />
        <nav className="sidebar-nav">
          {links.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Icon size={19} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar">{user?.first_name?.[0]}{user?.last_name?.[0]}</div>
            <div><strong>{user?.first_name} {user?.last_name}</strong><span>{user?.role}</span></div>
          </div>
          <button className="icon-button" onClick={logout} title="Sign out"><LogOut size={18} /></button>
        </div>
      </aside>
      <main className="app-main">
        <header className="topbar">
          <div><span className="eyebrow">MEDISCOPE workspace</span></div>
          <div className="topbar-actions"><button className="icon-button"><Bell size={18} /></button><span className="status-dot" /> Secure session</div>
        </header>
        <div className="app-content"><Outlet /></div>
      </main>
    </div>
  );
}
