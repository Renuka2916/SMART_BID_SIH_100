import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowRight, CheckCircle2, Building, Sparkles } from 'lucide-react';
import Button from '../components/ui/Button';

const LoginPage = () => {
  const [email, setEmail] = useState('officer@smartbid.gov.in');
  const [password, setPassword] = useState('SmartBid@2026!Officer');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isExpired = new URLSearchParams(location.search).get('expired') === 'true';

  const performLogin = async (loginEmail, loginPassword) => {
    setLoading(true);
    setError('');

    const res = await login(loginEmail, loginPassword);
    setLoading(false);

    if (res.success) {
      navigate('/dashboard');
    } else {
      setError(res.error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    await performLogin(email, password);
  };

  const handleQuickLogin = async (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    await performLogin(demoEmail, demoPass);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 flex flex-col justify-between text-slate-100 relative overflow-hidden">
      {/* Background Subtle Graphic */}
      <div className="absolute inset-0 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:24px_24px] opacity-10 pointer-events-none"></div>

      {/* Top Banner */}
      <header className="p-4 sm:p-6 flex items-center justify-between border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md relative z-10">
        <div className="flex items-center gap-3">
          <div className="h-10 px-3 w-auto rounded-xl bg-gradient-to-tr from-amber-500 to-amber-300 flex items-center justify-center text-slate-950 font-black text-xl shadow-lg">
            SmartBid
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-wide">
              GOVERNMENT e-MARKETPLACE (SmartBid)
            </h1>
            <p className="text-[11px] text-slate-400">
              SmartBid Verification Platform • SIH PS100
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-3 py-1.5 rounded-full">
          <ShieldCheck className="w-4 h-4" />
          <span>Statutory Compliance Engine v1.0</span>
        </div>
      </header>

      {/* Main Form Center */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 relative z-10">
        <div className="w-full max-w-md bg-white text-slate-900 rounded-2xl shadow-2xl border border-slate-200/80 p-6 sm:p-8 space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex p-3 rounded-2xl bg-blue-50 text-blue-900 border border-blue-100 shadow-sm mb-1">
              <Lock className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">
              Officer Portal Sign In
            </h2>
            <p className="text-xs text-slate-500">
              Access the automated statutory verification & tender evaluation workspace
            </p>
          </div>

          {isExpired && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
              <span>Your previous session has expired. Please log in again.</span>
            </div>
          )}

          {error && (
            <div className="p-3.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 space-y-1.5 animate-shake">
              <div className="flex items-center gap-2 font-bold text-red-800">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                <span>Authentication Notice</span>
              </div>
              <p className="leading-relaxed">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Official Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@smartbid.gov.in"
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-800 focus:border-blue-800 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-800 focus:border-blue-800 transition-all"
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              loading={loading}
              className="w-full py-2.5 mt-2 text-sm font-bold bg-blue-900 hover:bg-blue-950 text-white shadow-md"
            >
              Sign In to Procurement Workspace
            </Button>
          </form>

          {/* Quick Demo Credentials Box */}
          <div className="pt-4 border-t border-slate-200/80">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider text-center mb-2.5">
              Quick 1-Click Sign-In
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickLogin('officer@smartbid.gov.in', 'SmartBid@2026!Officer')}
                className="p-2.5 bg-amber-50/80 hover:bg-amber-100 border border-amber-300 rounded-lg text-left transition-all hover:shadow-sm group disabled:opacity-60"
              >
                <div className="text-[11px] font-bold text-amber-900 flex items-center justify-between">
                  <span>Procurement Officer</span>
                  <Sparkles className="w-3.5 h-3.5 text-amber-600 group-hover:scale-110 transition-transform" />
                </div>
                <div className="text-[10px] text-amber-700 truncate mt-0.5">officer@smartbid.gov.in</div>
                <div className="text-[9px] text-amber-700/90 font-medium mt-1">Click to sign in instantly →</div>
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickLogin('bidder@techcorp.in', 'Bidder@2026!Pass')}
                className="p-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-300 rounded-lg text-left transition-all hover:shadow-sm group disabled:opacity-60"
              >
                <div className="text-[11px] font-bold text-slate-800 flex items-center justify-between">
                  <span>Bidder Account</span>
                  <Building className="w-3.5 h-3.5 text-slate-500 group-hover:scale-110 transition-transform" />
                </div>
                <div className="text-[10px] text-slate-600 truncate mt-0.5">bidder@techcorp.in</div>
                <div className="text-[9px] text-slate-500 font-medium mt-1">Test RBAC Restrictions →</div>
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-4 text-center text-xs text-slate-500 border-t border-slate-800/80 bg-slate-900/40 relative z-10">
        Smart India Hackathon 2026 • AI-Powered SmartBid Verification Platform (PS100)
      </footer>
    </div>
  );
};

export default LoginPage;
