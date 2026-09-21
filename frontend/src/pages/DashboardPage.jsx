import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Layers, 
  CheckCircle, 
  AlertTriangle, 
  PlusCircle, 
  ArrowUpRight, 
  TrendingUp,
  Cpu,
  Clock,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import StatCard from '../components/ui/StatCard';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';

const DashboardPage = () => {
  const [tenders, setTenders] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user, isProcurementOfficer } = useAuth();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const res = await api.get('/tenders?limit=5');
        setTenders(res.data.items || []);
        setTotalCount(res.data.total || 0);
      } catch (err) {
        console.error('Failed to load tenders for dashboard:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Published':
        return <Badge variant="success">Published</Badge>;
      case 'Under Evaluation':
        return <Badge variant="warning">Under Evaluation</Badge>;
      case 'Closed':
        return <Badge variant="neutral">Closed</Badge>;
      default:
        return <Badge variant="info">Draft</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-blue-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 bg-blue-800/60 border border-blue-700/60 px-3 py-1 rounded-full text-xs font-semibold text-blue-200">
            <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
            <span>SmartBid PS100 • Automated Verification Platform</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome back, {user?.full_name || 'Procurement Officer'}
          </h2>
          <p className="text-sm text-blue-100/80 leading-relaxed">
            Centralized decision-support hub for SmartBid procurement. Multi-portal integration 
            with <strong>Udyam, GSTN, PAN, EPFO, ESIC, and DigiLocker</strong> empowers you to screen bidders, 
            detect discrepancies, and verify compliance with 60–80% reduced effort.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            {isProcurementOfficer && (
              <Button
                variant="primary"
                icon={PlusCircle}
                onClick={() => navigate('/tenders?create=true')}
                className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold border-none shadow-md"
              >
                Create New Tender
              </Button>
            )}
            <Button
              variant="outline"
              icon={Layers}
              onClick={() => navigate('/bids')}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20"
            >
              Inspect Active Bids
            </Button>
            <Button
              variant="outline"
              icon={Cpu}
              onClick={() => navigate('/verification')}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20"
            >
              Verification Engine
            </Button>
          </div>
        </div>

        {/* Impact stats pill in banner */}
        <div className="absolute -right-6 -bottom-6 w-56 h-56 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatCard
          title="Configured Tenders"
          value={totalCount}
          subtitle="Tenders in procurement system"
          icon={FileText}
          color="blue"
          badge={<span className="text-emerald-600 font-semibold flex items-center gap-1"><TrendingUp className="w-3.5 h-3.5" /> 100% Statutory Compliant</span>}
        />
        <StatCard
          title="Active Bids Submitted"
          value="18"
          subtitle="Across active tenders"
          icon={Layers}
          color="purple"
          badge={<span className="text-slate-500 font-medium">8 pending AI cross-check</span>}
        />
        <StatCard
          title="Avg. Verification Rate"
          value="78.4%"
          subtitle="Automated checks passed"
          icon={CheckCircle}
          color="emerald"
          badge={<span className="text-emerald-600 font-semibold flex items-center gap-1"><TrendingUp className="w-3.5 h-3.5" /> +65% Speed vs Manual</span>}
        />
        <StatCard
          title="Discrepancy Alerts"
          value="3"
          subtitle="Mismatches flagged for review"
          icon={AlertTriangle}
          color="amber"
          badge={<span className="text-amber-700 font-medium">GST & EPFO discrepancy</span>}
        />
      </div>

      {/* SIH Expected Impact Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
          <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-700 font-bold text-lg shrink-0">
            60-80%
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Verification Effort Reduction</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Eliminating tedious manual cross-referencing across 6+ separate government portal databases.
            </p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
          <div className="p-2.5 rounded-lg bg-blue-50 text-blue-700 font-bold text-lg shrink-0">
            100%
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Tamper-Proof Audit Trail</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Every verification check, document retrieval, and officer override is cryptographically logged.
            </p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
          <div className="p-2.5 rounded-lg bg-amber-50 text-amber-700 font-bold text-lg shrink-0">
            AI + HIL
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Officer Decision Support</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              AI provides risk scores and discrepancy detection; final qualification remains with the Procurement Officer.
            </p>
          </div>
        </div>
      </div>

      {/* Recent Tenders Overview Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Recent Tenders & Compliance Criteria</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Latest procurement notices configured with mandatory statutory verification criteria
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/tenders')}
            className="text-xs text-blue-900 border-blue-300 hover:bg-blue-50"
          >
            Manage All Tenders
            <ChevronRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3">Tender Ref No.</th>
                <th className="px-5 py-3">Title & Department</th>
                <th className="px-5 py-3">Category</th>
                <th className="px-5 py-3">Estimated Value</th>
                <th className="px-5 py-3">Mandatory Checks</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-5 py-8 text-center text-slate-400">
                    Loading recent tenders...
                  </td>
                </tr>
              ) : tenders.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-5 py-8 text-center text-slate-400">
                    No tenders found. Click 'Create New Tender' to add the first one.
                  </td>
                </tr>
              ) : (
                tenders.map((tender) => (
                  <tr key={tender.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-mono font-bold text-blue-900">
                      {tender.tender_ref}
                    </td>
                    <td className="px-5 py-3.5 max-w-xs">
                      <div className="font-semibold text-slate-900 truncate" title={tender.title}>
                        {tender.title}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate mt-0.5">
                        {tender.department}
                      </div>
                    </td>
                    <td className="px-5 py-3.5 font-medium text-slate-700">
                      {tender.category}
                    </td>
                    <td className="px-5 py-3.5 font-bold text-slate-900">
                      {formatCurrency(tender.estimated_value)}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 font-semibold text-[11px] border border-blue-200">
                          {tender.mandatory_requirements?.length || 0} Statutory Checks
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      {getStatusBadge(tender.status)}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => navigate('/tenders')}
                          className="text-xs font-semibold text-blue-700 hover:text-blue-900 hover:underline"
                        >
                          View
                        </button>
                        {(tender.status === 'Draft' || tender.status === 'Under Evaluation') ? (
                          <button
                            onClick={() => navigate('/tenders')}
                            className="text-xs font-semibold text-amber-700 hover:text-amber-900 hover:underline"
                            title={`Edit Tender (${tender.status})`}
                          >
                            Edit
                          </button>
                        ) : (
                          <span
                            className="text-[10px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded cursor-not-allowed"
                            title={`${tender.status} tenders are locked and cannot be edited.`}
                          >
                            Locked
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
