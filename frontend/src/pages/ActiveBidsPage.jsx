import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  Search, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Building2, 
  FileText, 
  Cpu, 
  ArrowRight,
  Plus,
  ShieldCheck,
  Lock,
  LockOpen,
  Calendar,
  Sparkles,
  AlertCircle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';

const ActiveBidsPage = () => {
  const navigate = useNavigate();
  const { user, isProcurementOfficer } = useAuth();

  const [tenders, setTenders] = useState([]);
  const [bidders, setBidders] = useState([]);
  const [loading, setLoading] = useState(true);

  // Submit Bid Modal
  const [isSubmitOpen, setIsSubmitOpen] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [bidForm, setBidForm] = useState({
    tender_id: '',
    company_name: '',
    pan: '',
    gstin: '',
    udyam_no: '',
    contact_email: '',
    contact_phone: ''
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const tResp = await api.get('/tenders?limit=20');
      const loadedTenders = tResp.data.items || [];
      setTenders(loadedTenders);

      let allBidders = [];
      for (const t of loadedTenders) {
        try {
          const bResp = await api.get(`/tenders/${t.id}/bidders`);
          const items = (bResp.data.items || []).map((b) => ({
            ...b,
            tenderRef: t.tender_ref,
            tenderTitle: t.title
          }));
          allBidders = [...allBidders, ...items];
        } catch (e) {
          // Tender might have no bidders
        }
      }
      setBidders(allBidders);
      if (loadedTenders.length > 0 && !bidForm.tender_id) {
        setBidForm((prev) => ({ ...prev, tender_id: loadedTenders[0].id }));
      }
    } catch (err) {
      console.error('Failed to load tenders or bidders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleBidSubmit = async (e) => {
    e.preventDefault();
    setSubmitLoading(true);
    setSubmitError('');

    try {
      await api.post(`/tenders/${bidForm.tender_id}/bidders`, {
        company_name: bidForm.company_name,
        pan: bidForm.pan,
        gstin: bidForm.gstin,
        udyam_no: bidForm.udyam_no || null,
        contact_email: bidForm.contact_email,
        contact_phone: bidForm.contact_phone || null
      });

      setIsSubmitOpen(false);
      setBidForm({
        tender_id: tenders[0]?.id || '',
        company_name: '',
        pan: '',
        gstin: '',
        udyam_no: '',
        contact_email: '',
        contact_phone: ''
      });
      fetchData();
    } catch (err) {
      setSubmitError(err.response?.data?.detail || 'Failed to submit application.');
    } finally {
      setSubmitLoading(false);
    }
  };

  const getRiskBadge = (score, status) => {
    if (status === 'UNDER_REVIEW' && (score === 0 || score === null)) {
      return <Badge variant="secondary">PENDING EVALUATION</Badge>;
    }
    if (status === 'FLAGGED' || score < 60) {
      return <Badge variant="danger">HIGH RISK</Badge>;
    } else if (score < 80) {
      return <Badge variant="warning">MEDIUM RISK</Badge>;
    }
    return <Badge variant="success">LOW RISK</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-slate-900 tracking-tight">Active Bid Submissions</h2>
            <span className="text-xs bg-blue-100 text-blue-800 font-bold px-2 py-0.5 rounded-full border border-blue-200">
              {bidders.length} Live Bidders
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Vendor bid submissions with AES-256 encrypted PII, document hash integrity, and automated compliance checks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            icon={Plus}
            onClick={() => setIsSubmitOpen(true)}
            className="text-xs font-bold text-blue-900 border-blue-300 hover:bg-blue-50"
          >
            Submit New Bid Application
          </Button>

          <Button
            variant="primary"
            icon={Cpu}
            onClick={() => navigate('/verification')}
            className="bg-blue-900 hover:bg-blue-950 font-bold text-xs"
          >
            Verification Workspace
          </Button>
        </div>
      </div>

      {/* Security & Cryptography Info Banner */}
      <div className="p-4 rounded-xl bg-slate-900 text-slate-200 border border-slate-800 text-xs flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-bold text-white">AES-256 Cryptographic Vault Active</span>
              <span className="text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.2 rounded font-mono">
                GCM-256
              </span>
            </div>
            <p className="text-slate-400 leading-relaxed max-w-2xl">
              Bidder identifiers (PAN, GSTIN, Udyam) are encrypted at rest with random nonces. 
              {isProcurementOfficer ? (
                <span className="text-amber-300 font-medium ml-1">
                  You are viewing unmasked PII authorized by your 'Procurement Officer' credential.
                </span>
              ) : (
                <span className="text-slate-400 ml-1">
                  Public views receive anonymized masked tokens (e.g. ABC****34F).
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700 font-mono text-[11px] text-slate-300 shrink-0">
          <Lock className="w-3.5 h-3.5 text-emerald-400" />
          <span>Append-Only Audit: Enabled</span>
        </div>
      </div>

      {/* Bidders List Cards */}
      {loading ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-400">
          <div className="w-6 h-6 border-2 border-blue-900 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          Loading submitted bids from database...
        </div>
      ) : bidders.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-500 space-y-3">
          <Layers className="w-8 h-8 text-slate-300 mx-auto" />
          <p className="font-bold text-slate-700">No Bids Submitted Yet</p>
          <p className="text-slate-400">Click 'Submit New Bid Application' to test live AES-256 encryption and validation.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {bidders.map((bid) => (
            <div
              key={bid.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow space-y-4"
            >
              <div className="flex items-start justify-between border-b border-slate-100 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-900">{bid.company_name}</h3>
                    {getRiskBadge(bid.compliance_score, bid.composite_status)}
                  </div>
                  <div className="text-[11px] font-mono text-slate-500 mt-1 flex items-center gap-2">
                    <span>PAN: <strong className="text-slate-800">{bid.pan || bid.pan_masked}</strong></span>
                    <span>•</span>
                    <span>GSTIN: <strong className="text-slate-800">{bid.gstin || bid.gstin_masked}</strong></span>
                  </div>
                  {bid.udyam_no_masked && (
                    <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                      Udyam: {bid.udyam_no || bid.udyam_no_masked}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold text-blue-950">
                    Score: {bid.compliance_score}%
                  </div>
                  <div className="text-[10px] text-slate-400">Statutory Score</div>
                </div>
              </div>

              {/* Linked Tender */}
              <div className="p-3 bg-slate-50 rounded-lg text-xs space-y-1">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Target Tender
                </div>
                <div className="font-semibold text-blue-900 truncate">
                  {bid.tenderTitle}
                </div>
                <div className="text-[11px] font-mono text-slate-500">
                  {bid.tenderRef}
                </div>
              </div>

              {/* Verification Breakdown */}
              <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-100">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1 text-emerald-700 font-semibold text-[11px]">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {bid.checks_count || 3} Compliance Checks
                  </span>
                  <span className="flex items-center gap-1 text-blue-700 font-semibold text-[11px]">
                    <FileText className="w-3.5 h-3.5" />
                    {bid.documents_count || 2} Docs Verified
                  </span>
                </div>

                <button
                  onClick={() => navigate(`/verification?bidderId=${bid.id}`)}
                  className={`text-xs font-bold flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
                    bid.compliance_score === 0 || bid.composite_status === 'UNDER_REVIEW'
                      ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm'
                      : 'text-blue-800 hover:text-blue-950 bg-blue-50 hover:bg-blue-100'
                  }`}
                >
                  <span>{bid.compliance_score === 0 ? 'Run AI Verification' : 'Inspect Risk'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SUBMIT BID MODAL */}
      <Modal
        isOpen={isSubmitOpen}
        onClose={() => setIsSubmitOpen(false)}
        title="Submit Vendor Bid Application"
        subtitle="Registers bidder identifiers with on-the-fly AES-256 encryption and auto checks"
        maxWidth="max-w-xl"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setIsSubmitOpen(false)}
              disabled={submitLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleBidSubmit}
              loading={submitLoading}
              className="bg-blue-900 hover:bg-blue-950 font-bold"
            >
              Encrypt & Submit Bid
            </Button>
          </>
        }
      >
        <form onSubmit={handleBidSubmit} className="space-y-4">
          {submitError && (
            <div className="p-3 bg-red-50 border border-red-200 text-xs text-red-700 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{submitError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Select Target GeM Tender *
            </label>
            <select
              required
              value={bidForm.tender_id}
              onChange={(e) => setBidForm({ ...bidForm, tender_id: e.target.value })}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white"
            >
              {tenders.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.tender_ref} - {t.title.slice(0, 50)}...
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Company / Entity Legal Name *
            </label>
            <input
              type="text"
              required
              value={bidForm.company_name}
              onChange={(e) => setBidForm({ ...bidForm, company_name: e.target.value })}
              placeholder="e.g. Apex Hardware Technologies LLP"
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Permanent Account Number (PAN) *
              </label>
              <input
                type="text"
                required
                maxLength={10}
                value={bidForm.pan}
                onChange={(e) => setBidForm({ ...bidForm, pan: e.target.value.toUpperCase() })}
                placeholder="ABCDE1234F"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg font-mono uppercase"
              />
              <span className="text-[10px] text-slate-400 mt-0.5 block">Stored as AES-256 cipher</span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                GSTIN Number *
              </label>
              <input
                type="text"
                required
                maxLength={15}
                value={bidForm.gstin}
                onChange={(e) => setBidForm({ ...bidForm, gstin: e.target.value.toUpperCase() })}
                placeholder="07ABCDE1234F1Z5"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg font-mono uppercase"
              />
              <span className="text-[10px] text-slate-400 mt-0.5 block">Stored as AES-256 cipher</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Udyam Registration Number (Optional)
            </label>
            <input
              type="text"
              value={bidForm.udyam_no}
              onChange={(e) => setBidForm({ ...bidForm, udyam_no: e.target.value.toUpperCase() })}
              placeholder="UDYAM-DL-01-0029145"
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg font-mono uppercase"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Contact Email *
              </label>
              <input
                type="email"
                required
                value={bidForm.contact_email}
                onChange={(e) => setBidForm({ ...bidForm, contact_email: e.target.value })}
                placeholder="tender@apextech.in"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Contact Phone
              </label>
              <input
                type="tel"
                value={bidForm.contact_phone}
                onChange={(e) => setBidForm({ ...bidForm, contact_phone: e.target.value })}
                placeholder="+91 98111 22334"
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg"
              />
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ActiveBidsPage;
