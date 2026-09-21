import React from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, LogOut, User as UserIcon, Bell, ExternalLink, Cpu } from 'lucide-react';

const Navbar = () => {
  const { user, logout, isProcurementOfficer } = useAuth();

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-sm">
      {/* Top Gov/SmartBid Bar */}
      <div className="bg-slate-900 text-slate-300 text-[11px] px-4 sm:px-6 py-1 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-amber-400 tracking-wide flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            GOVERNMENT OF INDIA • SmartBid PORTAL
          </span>
          <span className="hidden md:inline text-slate-500">|</span>
          <span className="hidden md:inline text-slate-400">
            Smart India Hackathon 2026 • Problem Statement PS100
          </span>
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-emerald-400 font-medium">AI Verification Engine: Active</span>
          </div>
        </div>
      </div>

      {/* Main Navbar */}
      <div className="px-4 sm:px-6 py-3 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-900 flex items-center justify-center text-white font-black text-xl shadow-md tracking-tighter">
            SB
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold text-slate-900 tracking-tight leading-none">
                SmartBid Verification
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-200">
                v1.0 (PS100)
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Automated Statutory, Regulatory & Eligibility Verification System
            </p>
          </div>
        </div>

        {/* User profile & Actions */}
        <div className="flex items-center gap-3 sm:gap-4">
          {user && (
            <div className="flex items-center gap-3 pl-3 sm:pl-4 border-l border-slate-200">
              <div className="hidden sm:block text-right">
                <div className="text-xs font-bold text-slate-800 flex items-center justify-end gap-1.5">
                  <span>{user.full_name}</span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    isProcurementOfficer 
                      ? 'bg-amber-100 text-amber-900 border border-amber-300' 
                      : 'bg-slate-100 text-slate-700'
                  }`}>
                    {user.role?.name}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 max-w-[200px] truncate">
                  {user.department || 'SmartBid Procurement Cell'}
                </div>
              </div>

              <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-700 font-bold text-sm">
                {user.full_name?.charAt(0) || 'U'}
              </div>

              <button
                onClick={logout}
                title="Sign Out"
                className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-200"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
