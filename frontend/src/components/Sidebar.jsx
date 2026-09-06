import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Layers, 
  Cpu, 
  ShieldCheck, 
  ExternalLink,
  Building2,
  FileCheck2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { user, isProcurementOfficer } = useAuth();
  const location = useLocation();

  const navItems = [
    {
      name: 'Dashboard',
      path: '/dashboard',
      icon: LayoutDashboard,
      badge: null,
      description: 'Executive overview & alerts'
    },
    {
      name: 'Tender Management',
      path: '/tenders',
      icon: FileText,
      badge: 'CRUD',
      description: 'Statutory requirements & tender config'
    },
    {
      name: 'Active Bids',
      path: '/bids',
      icon: Layers,
      badge: 'Live',
      description: 'Submitted bidder submissions'
    },
    {
      name: 'Verification Workspace',
      path: '/verification',
      icon: Cpu,
      badge: 'AI Engine',
      description: 'Portal sync & risk evaluation'
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 min-h-[calc(100vh-89px)] flex flex-col justify-between shrink-0 shadow-sm">
      <div className="p-4 space-y-6">
        <div>
          <p className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
            Main Navigation
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || 
                (item.path === '/dashboard' && location.pathname === '/');

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-blue-50 text-blue-900 font-semibold shadow-sm border border-blue-200/60'
                      : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 transition-colors ${
                      isActive ? 'text-blue-700' : 'text-slate-400 group-hover:text-slate-600'
                    }`} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      isActive 
                        ? 'bg-blue-200 text-blue-900' 
                        : 'bg-slate-100 text-slate-500 group-hover:bg-slate-200'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Portal Integrations Section */}
        <div>
          <p className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
            <span>Linked Portals</span>
            <span className="text-[10px] text-emerald-600 font-bold bg-emerald-50 px-1.5 py-0.5 rounded">
              Ready
            </span>
          </p>
          <div className="px-3 py-2 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1.5 text-slate-600">
            <div className="flex items-center justify-between">
              <span>• GSTN & Income Tax</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            </div>
            <div className="flex items-center justify-between">
              <span>• Udyam / MSME Portal</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            </div>
            <div className="flex items-center justify-between">
              <span>• EPFO & ESIC Services</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            </div>
            <div className="flex items-center justify-between">
              <span>• DigiLocker & MCA21</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            </div>
          </div>
        </div>
      </div>

      {/* Role & RBAC status badge */}
      <div className="p-4 border-t border-slate-200 bg-slate-50/70">
        <div className="p-3 rounded-lg border border-amber-200 bg-amber-50 text-xs text-amber-900">
          <div className="flex items-center gap-2 font-bold mb-1">
            <ShieldCheck className="w-4 h-4 text-amber-700" />
            <span>RBAC Protected</span>
          </div>
          <p className="text-[11px] text-amber-800 leading-relaxed">
            Active Role: <strong className="font-semibold">{user?.role?.name || 'Guest'}</strong>.
            {isProcurementOfficer 
              ? ' You have full authorization to create, configure & manage tenders.'
              : ' View-only access enabled for this session.'}
          </p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
