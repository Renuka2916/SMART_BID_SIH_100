import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  ShieldCheck, 
  ShieldAlert, 
  FileCheck, 
  Pin, 
  Send, 
  Lock, 
  HelpCircle,
  Clock
} from 'lucide-react';
import Modal from '../ui/Modal';
import Button from '../ui/Button';

const MIN_REMARKS_LENGTH = 15;

const DecisionPanel = ({
  bidderData,
  complianceReport,
  pinnedEvidence = [],
  onSubmitDecision,
  submitting = false,
  isOfficer = true
}) => {
  const [selectedDecision, setSelectedDecision] = useState(null); // 'QUALIFIED' | 'DISQUALIFIED'
  const [remarks, setRemarks] = useState('');
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);

  const company = bidderData?.company_name || 'Bidder Enterprise';
  const score = bidderData?.compliance_score ?? 0;
  const currentStatus = bidderData?.composite_status || 'UNDER_REVIEW';

  const isRemarksValid = remarks.trim().length >= MIN_REMARKS_LENGTH;

  const handleOpenConfirm = (decisionType) => {
    if (!isRemarksValid) return;
    setSelectedDecision(decisionType);
    setIsConfirmModalOpen(true);
  };

  const handleExecuteSubmission = async () => {
    if (!selectedDecision || !isRemarksValid) return;
    if (onSubmitDecision) {
      await onSubmitDecision(selectedDecision, remarks.trim());
      setIsConfirmModalOpen(false);
      setRemarks('');
      setSelectedDecision(null);
    }
  };

  const applyRemarkTemplate = (templateText) => {
    setRemarks(templateText);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col">
      {/* Panel Header */}
      <div className="p-4 border-b border-slate-200 bg-slate-50/70 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <span>Procurement Officer Qualification Judgment Panel</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Formal administrative decision under General Financial Rules (GFR) 2017 & GeM Terms.
          </p>
        </div>

        {/* Current State Indicator */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium">Current Status:</span>
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
            currentStatus === 'QUALIFIED' || currentStatus === 'COMPLIANT'
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
              : currentStatus === 'DISQUALIFIED' || currentStatus === 'NON_COMPLIANT'
                ? 'bg-rose-100 text-rose-800 border border-rose-300'
                : 'bg-amber-100 text-amber-800 border border-amber-300'
          }`}>
            {currentStatus}
          </span>
        </div>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        {/* Pinned Evidence Chips Section */}
        {pinnedEvidence.length > 0 && (
          <div className="bg-blue-50/60 border border-blue-200 rounded-lg p-3">
            <div className="text-xs font-semibold text-blue-900 flex items-center gap-1.5 mb-2">
              <Pin className="w-3.5 h-3.5 text-blue-700" />
              <span>Pinned Discrepancies & Evidence Docket ({pinnedEvidence.length} items):</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {pinnedEvidence.map((item, idx) => (
                <span 
                  key={idx}
                  className="text-[11px] bg-white text-slate-700 border border-blue-200 px-2.5 py-1 rounded-md shadow-xs flex items-center gap-1.5"
                >
                  <span className="font-bold text-blue-900">{item.key}:</span>
                  <span className="truncate max-w-[200px]">{item.docValue}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Mandatory Remarks Textarea */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-bold text-slate-800 flex items-center gap-1">
              <span>Mandatory Officer Evaluation Remarks</span>
              <span className="text-rose-500">*</span>
            </label>
            <span className={`text-[11px] font-mono font-medium ${
              isRemarksValid ? 'text-emerald-600' : 'text-amber-600'
            }`}>
              {remarks.trim().length} / {MIN_REMARKS_LENGTH} characters required
            </span>
          </div>

          <textarea
            rows={3}
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            placeholder="Enter substantive reasoning, findings of statutory compliance checks, and formal justification for qualification or rejection..."
            className={`w-full text-xs p-3 rounded-lg border focus:outline-none focus:ring-2 bg-slate-50/50 transition-all ${
              remarks.length > 0 && !isRemarksValid
                ? 'border-amber-400 focus:ring-amber-500 bg-amber-50/20'
                : 'border-slate-300 focus:ring-blue-500 focus:bg-white'
            }`}
          />

          {/* Quick Template Fill Buttons */}
          <div className="flex flex-wrap items-center gap-1.5 mt-2">
            <span className="text-[10px] text-slate-400 font-medium mr-1">Quick Templates:</span>
            <button
              type="button"
              onClick={() => applyRemarkTemplate('All statutory credentials, GST, PAN, and local content criteria verified compliant. Recommended for technical qualification.')}
              className="text-[10px] px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              Qualify (All Clear)
            </button>
            <button
              type="button"
              onClick={() => applyRemarkTemplate('Declared Make in India local content (35%) fails the mandatory Class-I threshold (50%). Disqualified under GFR Rule 153.')}
              className="text-[10px] px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              Disqualify (MII Deficit)
            </button>
            <button
              type="button"
              onClick={() => applyRemarkTemplate('Provisional CA UDIN requires confirmation from ICAI portal prior to contract award. Qualified subject to verification.')}
              className="text-[10px] px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              Conditional (UDIN Pending)
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-slate-400" />
            <span>Decision commits an immutable tamper-proof entry to the GeM Audit Vault.</span>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Disqualify Button */}
            <button
              type="button"
              disabled={!isRemarksValid || submitting || !isOfficer}
              onClick={() => handleOpenConfirm('DISQUALIFIED')}
              className={`text-xs px-4 py-2 rounded-lg font-bold flex items-center gap-1.5 transition-all shadow-sm ${
                isRemarksValid && isOfficer
                  ? 'bg-rose-600 hover:bg-rose-700 text-white cursor-pointer active:scale-95'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed opacity-60'
              }`}
            >
              <XCircle className="w-4 h-4" />
              <span>Disqualify Bidder</span>
            </button>

            {/* Qualify Button */}
            <button
              type="button"
              disabled={!isRemarksValid || submitting || !isOfficer}
              onClick={() => handleOpenConfirm('QUALIFIED')}
              className={`text-xs px-5 py-2 rounded-lg font-bold flex items-center gap-1.5 transition-all shadow-sm ${
                isRemarksValid && isOfficer
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer active:scale-95'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed opacity-60'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Qualify Bidder</span>
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation Modal Dialog */}
      <Modal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        title={selectedDecision === 'QUALIFIED' ? "Confirm Bidder Qualification" : "Confirm Bidder Disqualification"}
      >
        <div className="space-y-4 text-xs text-slate-700">
          <div className={`p-3 rounded-lg border flex items-start gap-3 ${
            selectedDecision === 'QUALIFIED' 
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900' 
              : 'bg-rose-50 border-rose-200 text-rose-900'
          }`}>
            {selectedDecision === 'QUALIFIED' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            )}
            <div>
              <div className="font-bold text-sm">
                You are about to {selectedDecision === 'QUALIFIED' ? 'QUALIFY' : 'DISQUALIFY'} this bidder:
              </div>
              <div className="font-semibold text-slate-900 text-xs mt-0.5">
                {company}
              </div>
              <div className="text-[11px] text-slate-600 mt-1">
                Compliance Score: <span className="font-bold">{score}%</span> • Pinned Evidence: <span className="font-bold">{pinnedEvidence.length} item(s)</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
              Recorded Procurement Officer Remarks:
            </span>
            <p className="text-xs text-slate-800 italic bg-white p-2 rounded border border-slate-200/80">
              "{remarks}"
            </p>
          </div>

          <div className="text-[11px] text-slate-500 bg-amber-50 border border-amber-200 p-2.5 rounded-lg flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span>
              <strong>Statutory Warning:</strong> Once committed, this administrative determination is permanently recorded under GFR Rule 173 and will trigger notifications to the GeM Evaluation Directorate.
            </span>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
            <Button
              variant="outline"
              onClick={() => setIsConfirmModalOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <button
              onClick={handleExecuteSubmission}
              disabled={submitting}
              className={`text-xs px-4 py-2 rounded-lg font-bold text-white transition-all ${
                selectedDecision === 'QUALIFIED'
                  ? 'bg-emerald-600 hover:bg-emerald-700'
                  : 'bg-rose-600 hover:bg-rose-700'
              }`}
            >
              {submitting ? 'Signing & Committing...' : `Confirm & Commit ${selectedDecision}`}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default DecisionPanel;
