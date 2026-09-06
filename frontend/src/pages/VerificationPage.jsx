import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  Cpu, 
  ShieldCheck, 
  Database, 
  FileSearch, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Sparkles, 
  FileText, 
  Building2, 
  ArrowRight, 
  ShieldAlert, 
  RotateCcw,
  ExternalLink,
  Activity,
  RefreshCw,
  Search,
  Check,
  AlertCircle,
  Upload,
  Stamp,
  Award,
  FileCheck2,
  Fingerprint,
  Layers,
  HelpCircle,
  Maximize2
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';

// Verification Workspace Modular Components
import ComplianceDashboard from '../components/VerificationWorkspace/ComplianceDashboard';
import PDFViewer from '../components/VerificationWorkspace/PDFViewer';
import ComparisonTable from '../components/VerificationWorkspace/ComparisonTable';
import DecisionPanel from '../components/VerificationWorkspace/DecisionPanel';
import PinnedEvidenceDocket from '../components/VerificationWorkspace/PinnedEvidenceDocket';

const VerificationPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, isProcurementOfficer } = useAuth();

  const [bidders, setBidders] = useState([]);
  const [selectedBidderId, setSelectedBidderId] = useState(null);
  const [bidderData, setBidderData] = useState(null);
  const [complianceChecks, setComplianceChecks] = useState([]);
  const [complianceReport, setComplianceReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [submittingDecision, setSubmittingDecision] = useState(false);

  // Split-Screen Interactive State
  const [selectedDocType, setSelectedDocType] = useState('GST_CERTIFICATE');
  const [activeFieldHighlight, setActiveFieldHighlight] = useState(null);
  const [pinnedEvidence, setPinnedEvidence] = useState([]);

  // 15 Govt Portals Inspection State
  const [portals, setPortals] = useState([]);
  const [isPortalsModalOpen, setIsPortalsModalOpen] = useState(false);
  const [selectedPortalForInspection, setSelectedPortalForInspection] = useState(null);
  const [inspectionData, setInspectionData] = useState(null);
  const [inspectionLoading, setInspectionLoading] = useState(false);
  const [inspectionTab, setInspectionTab] = useState('normalized'); // 'normalized' | 'raw' | 'discrepancies'

  // AI Document Intelligence Hub Modal State
  const [isDocHubOpen, setIsDocHubOpen] = useState(false);
  const [docType, setDocType] = useState('GST_CERTIFICATE');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [docExtractLoading, setDocExtractLoading] = useState(false);
  const [docExtractResult, setDocExtractResult] = useState(null);
  const [sampleTemplate, setSampleTemplate] = useState('gst');

  // Dynamic sample document generator based on the currently selected bidder
  const getSampleDocuments = (currentBidder) => {
    const company = currentBidder?.company_name || 'Alpha Data Systems Private Limited';
    const pan = currentBidder?.pan || currentBidder?.pan_masked || 'ABCDE1234F';
    const gstin = currentBidder?.gstin || currentBidder?.gstin_masked || '07ABCDE1234F1Z5';
    const cleanCo = company.replace(/Private Limited|Pvt Ltd|LLP/i, '').trim();
    const isZenith = company.toLowerCase().includes('zenith');

    return {
      gst: {
        name: `${company.replace(/\s+/g, '_')}_GST_REG-06.txt`,
        type: "GST_CERTIFICATE",
        text: `GOVERNMENT OF INDIA - FORM GST REG-06
REGISTRATION CERTIFICATE
Registration Number (GSTIN) : ${gstin}
Legal Name : ${company}
Trade Name : ${cleanCo}
Permanent Account Number (PAN) : ${pan}
Date of Liability : 01/07/2017
Principal Place of Business : Electronics Industrial Area, Phase-II
Authorized Signatory : Executive Director (Authorized Representative)
Round Seal & Digital Signature : Attested and Cryptographically Sealed.`
      },
      mii: {
        name: `${company.replace(/\s+/g, '_')}_MII_Declaration.txt`,
        type: "MAKE_IN_INDIA_DECLARATION",
        text: `DPIIT PUBLIC PROCUREMENT PREFERENCE LOCAL CONTENT DECLARATION
Supplier Legal Name : ${company}
PAN : ${pan}
GSTIN : ${gstin}
Local Content Percentage : ${isZenith ? '35.0% Local Content (Class-II Supplier)' : '68.5% Local Content (Class-I Supplier)'}
Classification : ${isZenith ? 'Class-II Local Supplier (>= 20% & < 50%)' : 'Class-I Local Supplier (>= 50%)'}
Manufacturing Location : Sector 62 Electronics Industrial Zone, Noida
Statutory CA UDIN : ${isZenith ? '26084920PENDING99' : '26084920AAAAAB9812'}
Chartered Accountant Firm : V.K. Singhal & Co. (FRN: 004812N)
Authorized Signatory & Seal : Duly Attested & Certified.`
      },
      oem: {
        name: `${company.replace(/\s+/g, '_')}_OEM_MAF_Letter.txt`,
        type: "OEM_AUTHORIZATION",
        text: `MANUFACTURER AUTHORIZATION FORM (MAF)
OEM Principal : Bharath Tech Computronix India Pvt Ltd
MAF Code : MAF-IN-2026-GEM-${currentBidder?.id || 101}
Target Bidder Partner : ${company}
Authorization Level : Tier-1 Enterprise Partner
Scope of SLA : 3-Year 24x7 Direct Onsite Warranty SLA
Official OEM Header & Logo : Verified Authentic Principal Branding
Signatory : VP Enterprise Public Sector, OEM Division.`
      },
      tampered: {
        name: `Flagged_Mismatched_Certificate.txt`,
        type: "GST_CERTIFICATE",
        text: `CERTIFICATE UNDER GOODS AND SERVICES TAX
Registration Number : 07ZZZZZ9999K1Z5
Legal Name : UNRELATED MOCK FORGERY ENTERPRISES
PAN : ZZZZZ9999K
Status : SUSPENDED`
      }
    };
  };

  const sampleDocuments = getSampleDocuments(bidderData);

  // 1. Initial Data Fetching
  useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      try {
        const [biddersRes, portalsRes] = await Promise.all([
          api.get('/bidders?limit=100'),
          api.get('/integrations/portals')
        ]);

        const list = biddersRes.data.items || [];
        setBidders(list);
        setPortals(portalsRes.data.registered_portals || []);

        const paramId = searchParams.get('bidderId');
        if (paramId && list.some(b => b.id.toString() === paramId)) {
          setSelectedBidderId(paramId);
        } else if (list.length > 0) {
          setSelectedBidderId(list[0].id.toString());
        }
      } catch (err) {
        console.error('Failed to load initial verification workspace data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, [searchParams]);

  // 2. Fetch Selected Bidder Details & Reports
  const fetchSelectedBidderDetails = async (id) => {
    if (!id) return;
    try {
      const [bResp, cResp] = await Promise.all([
        api.get(`/bidders/${id}`),
        api.get(`/bidders/${id}/compliance-checks`)
      ]);
      setBidderData(bResp.data);
      setComplianceChecks(cResp.data.items || []);

      // Fetch latest compliance report
      try {
        const repResp = await api.get(`/compliance/report/${id}`);
        setComplianceReport(repResp.data);
      } catch (e) {
        setComplianceReport(null);
      }
    } catch (err) {
      console.error(`Failed to load details for bidder ${id}:`, err);
    }
  };

  useEffect(() => {
    if (selectedBidderId) {
      fetchSelectedBidderDetails(selectedBidderId);
      // Reset active field highlight when switching bidders
      setActiveFieldHighlight(null);
      setPinnedEvidence([]);
    }
  }, [selectedBidderId]);

  const handleSelectBidder = (id) => {
    setSelectedBidderId(id.toString());
    setSearchParams({ bidderId: id.toString() });
  };

  // 3. Trigger Full 15-Portal AI Verification & Compliance Engine
  const handleRunAiEvaluation = async () => {
    if (!selectedBidderId) return;
    setEvaluating(true);
    try {
      await api.post(`/integrations/verify-bidder/${selectedBidderId}`);
      const evalResp = await api.post(`/compliance/evaluate/${selectedBidderId}`);
      setComplianceReport(evalResp.data);
      await fetchSelectedBidderDetails(selectedBidderId);
    } catch (err) {
      console.error('Failed to run AI statutory evaluation:', err);
      alert('Error running AI statutory verification: ' + (err.response?.data?.detail || err.message));
    } finally {
      setEvaluating(false);
    }
  };

  // 4. Row Click in Comparison Table -> Auto-Zoom Left PDF Viewer
  const handleRowSelect = (fieldTarget, docType) => {
    if (docType) {
      setSelectedDocType(docType);
    }
    setActiveFieldHighlight(fieldTarget);
  };

  // 5. Pin / Unpin Evidence
  const handlePinEvidence = (item) => {
    setPinnedEvidence(prev => {
      const exists = prev.some(p => p.key === item.key);
      if (exists) {
        return prev.filter(p => p.key !== item.key);
      } else {
        return [...prev, item];
      }
    });
  };

  const handlePinFieldFromViewer = (fieldKey, fieldValue, note) => {
    setPinnedEvidence(prev => {
      const exists = prev.some(p => p.key === fieldKey);
      if (exists) return prev;
      return [...prev, {
        key: fieldKey,
        name: fieldKey.replace('_', ' '),
        docValue: fieldValue,
        discrepancy: note,
        status: 'FLAGGED'
      }];
    });
  };

  const handleRemovePin = (key) => {
    setPinnedEvidence(prev => prev.filter(p => p.key !== key));
  };

  const handleClearAllPins = () => {
    setPinnedEvidence([]);
  };

  // 6. Submit Procurement Officer Decision
  const handleSubmitDecision = async (decision, remarks) => {
    if (!selectedBidderId) return;
    setSubmittingDecision(true);
    try {
      const res = await api.post(`/bidders/${selectedBidderId}/decision`, {
        decision: decision,
        notes: remarks
      });
      setBidderData(res.data);
      alert(`Qualification decision recorded successfully! Bidder status updated to ${decision}. Immutable audit log committed.`);
      // Refresh list to update badge counts
      const biddersRes = await api.get('/bidders?limit=100');
      setBidders(biddersRes.data.items || []);
    } catch (err) {
      console.error('Failed to submit officer decision:', err);
      alert('Error submitting decision: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmittingDecision(false);
    }
  };

  // 7. Portal Inspection Logic
  const handleInspectPortal = async (portal) => {
    setSelectedPortalForInspection(portal);
    setInspectionLoading(true);
    setInspectionData(null);
    setInspectionTab('normalized');
    setIsPortalsModalOpen(true);

    try {
      const res = await api.post(`/integrations/fetch/${portal.portal_id}`, {
        company_name: bidderData?.company_name || 'Alpha Data Systems Pvt Ltd',
        pan: bidderData?.pan || bidderData?.pan_masked || 'ABCDE1234F',
        gstin: bidderData?.gstin || bidderData?.gstin_masked || '07ABCDE1234F1Z5',
        udyam_no: bidderData?.udyam_no || bidderData?.udyam_no_masked || 'UDYAM-DL-01-0029145'
      });
      setInspectionData(res.data);
    } catch (err) {
      console.error('Failed to fetch portal response:', err);
      setInspectionData({
        portal_id: portal.portal_id,
        portal_name: portal.portal_name,
        category: portal.category,
        status: 'OFFLINE',
        is_valid: false,
        confidence_score: 0.0,
        discrepancies: [err.response?.data?.detail || 'Portal connection failed.'],
        normalized_data: { error: 'Failed to fetch portal response' },
        raw_data: { error: err.message },
        latency_ms: 0.0
      });
    } finally {
      setInspectionLoading(false);
    }
  };

  // 8. AI Doc Extraction Modal Logic
  const handleRunDocExtraction = async () => {
    setDocExtractLoading(true);
    setDocExtractResult(null);

    try {
      let fileToSend = uploadedFile;
      if (!fileToSend && sampleTemplate) {
        const tmpl = sampleDocuments[sampleTemplate];
        const blob = new Blob([tmpl.text], { type: 'text/plain' });
        fileToSend = new File([blob], tmpl.name, { type: 'text/plain' });
      }

      const formData = new FormData();
      formData.append('file', fileToSend);
      formData.append('doc_type', docType);
      formData.append('expected_bidder_name', bidderData?.company_name || 'Alpha Data Systems Pvt Ltd');
      formData.append('expected_pan', bidderData?.pan || 'ABCDE1234F');
      formData.append('expected_gstin', bidderData?.gstin || '07ABCDE1234F1Z5');

      const res = await api.post('/ai/extract-file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setDocExtractResult(res.data);
    } catch (err) {
      console.error('Document OCR & NLP extraction failed:', err);
      alert('OCR extraction failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDocExtractLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3 text-slate-500">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-mono">Initializing GeM Verification Workspace & Documents...</p>
      </div>
    );
  }

  const pinnedKeys = pinnedEvidence.map(p => p.key);

  return (
    <div className="space-y-5">
      {/* Top Section: Compliance Dashboard (Score Gauge, Risk, Progress Bars, AI Recommendations) */}
      <ComplianceDashboard
        bidderData={bidderData}
        complianceReport={complianceReport}
        bidders={bidders}
        onSelectBidder={handleSelectBidder}
        onTriggerEvaluation={handleRunAiEvaluation}
        evaluating={evaluating}
      />

      {/* Secondary Tools Utility Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-xs text-xs">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-800 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <span>Split-Screen Bid Review Workspace</span>
          </span>
          <span className="text-slate-400">•</span>
          <span className="text-slate-500">
            Interactive document inspection on left; Side-by-side portal comparison on right.
          </span>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          {/* 15 Portals Modal Trigger */}
          <button
            onClick={() => setIsPortalsModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors flex items-center gap-1.5"
          >
            <Database className="w-3.5 h-3.5 text-blue-600" />
            <span>15 Govt APIs ({portals.length})</span>
          </button>

          {/* AI Doc Hub Modal Trigger */}
          <button
            onClick={() => setIsDocHubOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 font-medium transition-colors flex items-center gap-1.5"
          >
            <Cpu className="w-3.5 h-3.5 text-blue-600" />
            <span>OCR & NLP Extraction Hub</span>
          </button>
        </div>
      </div>

      {/* Main Split-Screen Layout (50% Left / 50% Right on Desktop) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Pane: Interactive Document & PDF Viewer (Col 6) */}
        <div className="lg:col-span-6 h-[860px]">
          <PDFViewer
            bidderData={bidderData}
            selectedDocType={selectedDocType}
            onSelectDocType={setSelectedDocType}
            activeFieldHighlight={activeFieldHighlight}
            onClearHighlight={() => setActiveFieldHighlight(null)}
            onPinField={handlePinFieldFromViewer}
          />
        </div>

        {/* Right Pane: Comparison Table + Pinned Evidence + Decision Panel (Col 6) */}
        <div className="lg:col-span-6 space-y-4">
          {/* Comparison Matrix */}
          <div className="h-[480px]">
            <ComparisonTable
              bidderData={bidderData}
              complianceReport={complianceReport}
              complianceChecks={complianceChecks}
              onRowSelect={handleRowSelect}
              onPinEvidence={handlePinEvidence}
              pinnedKeys={pinnedKeys}
            />
          </div>

          {/* Pinned Evidence Docket (Shows when items are pinned) */}
          <PinnedEvidenceDocket
            pinnedItems={pinnedEvidence}
            onRemovePin={handleRemovePin}
            onClearAllPins={handleClearAllPins}
          />

          {/* Mandatory Decision Panel */}
          <DecisionPanel
            bidderData={bidderData}
            complianceReport={complianceReport}
            pinnedEvidence={pinnedEvidence}
            onSubmitDecision={handleSubmitDecision}
            submitting={submittingDecision}
            isOfficer={isProcurementOfficer}
          />
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MODAL 1: 15 Government Portals Registry Inspection Modal */}
      {/* ========================================================================= */}
      <Modal
        isOpen={isPortalsModalOpen}
        onClose={() => setIsPortalsModalOpen(false)}
        title="15 Government Statutory API Portals Registry"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-600">
            Real-time integration status and health across official Indian statutory verification portals.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[420px] overflow-y-auto pr-1">
            {portals.map((portal) => (
              <div
                key={portal.portal_id}
                onClick={() => handleInspectPortal(portal)}
                className="p-3 rounded-lg border border-slate-200 hover:border-blue-400 hover:bg-blue-50/40 cursor-pointer transition-all flex flex-col justify-between"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-bold text-slate-800 text-xs">{portal.portal_name}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-emerald-100 text-emerald-800 font-semibold">
                    ACTIVE
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 mt-2 flex items-center justify-between">
                  <span>Category: {portal.category}</span>
                  <span className="text-blue-600 font-semibold flex items-center gap-0.5">
                    Inspect JSON <ArrowRight className="w-2.5 h-2.5" />
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Inspection Details Sub-Modal / Container */}
          {selectedPortalForInspection && (
            <div className="border-t border-slate-200 pt-3 space-y-2">
              <div className="font-bold text-slate-900 text-xs flex items-center gap-2">
                <span>Inspecting: {selectedPortalForInspection.portal_name}</span>
                {inspectionLoading && (
                  <span className="text-blue-600 text-[10px] animate-pulse">Querying portal...</span>
                )}
              </div>

              {inspectionData && (
                <div className="bg-slate-900 text-slate-200 p-3 rounded-lg font-mono text-[11px] max-h-56 overflow-auto">
                  <pre>{JSON.stringify(inspectionData.normalized_data, null, 2)}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      </Modal>

      {/* ========================================================================= */}
      {/* MODAL 2: AI Document Intelligence & OCR Extraction Hub */}
      {/* ========================================================================= */}
      <Modal
        isOpen={isDocHubOpen}
        onClose={() => setIsDocHubOpen(false)}
        title="AI Document Intelligence & Semantic OCR Hub"
      >
        <div className="space-y-4 text-xs text-slate-700">
          <p className="text-slate-600">
            Extract and validate structured entities from uploaded certificate scans using OpenCV preprocessing, Tesseract OCR, and semantic NLP triangulation.
          </p>

          {/* Template Selection */}
          <div className="space-y-1.5">
            <label className="font-bold text-slate-800">Select Document Scenario to Test:</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {Object.entries(sampleDocuments).map(([key, item]) => (
                <button
                  key={key}
                  onClick={() => {
                    setSampleTemplate(key);
                    setDocType(item.type);
                    setUploadedFile(null);
                  }}
                  className={`p-2 rounded-lg border text-left transition-all ${
                    sampleTemplate === key && !uploadedFile
                      ? 'border-blue-600 bg-blue-50 text-blue-900 font-bold'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="text-[11px] truncate">{item.name}</div>
                  <div className="text-[9px] text-slate-400 uppercase mt-0.5">{key}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={handleRunDocExtraction}
              disabled={docExtractLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2 rounded-lg text-xs transition-colors flex items-center gap-1.5"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>{docExtractLoading ? 'Processing Scan...' : 'Extract Entities & Validate'}</span>
            </button>
          </div>

          {/* Extraction Result Banner */}
          {docExtractResult && (
            <div className="border border-slate-200 rounded-lg p-3 bg-slate-50 space-y-2 mt-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900">Extraction Verdict:</span>
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                  docExtractResult.lifecycle_status === 'AI_VERIFIED'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-rose-100 text-rose-800'
                }`}>
                  {docExtractResult.lifecycle_status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="bg-white p-2 rounded border border-slate-200">
                  <span className="text-slate-500">Scan Readability (OCR):</span>
                  <div className="font-bold text-slate-900 font-mono">
                    {Math.round(docExtractResult.ocr_confidence * 100)}% (Glyph Clarity)
                  </div>
                </div>
                <div className="bg-white p-2 rounded border border-slate-200">
                  <span className="text-slate-500">Document Integrity:</span>
                  <div className={`font-bold font-mono ${
                    (docExtractResult.validation_integrity_score ?? 100) >= 80 
                      ? 'text-emerald-700' 
                      : 'text-rose-700'
                  }`}>
                    {docExtractResult.validation_integrity_score ?? 100}%
                  </div>
                </div>
              </div>

              {docExtractResult.integrity_notes && docExtractResult.integrity_notes.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded p-2 text-[11px] text-amber-900 space-y-1">
                  <span className="font-bold">Observations:</span>
                  <ul className="list-disc pl-4 space-y-0.5">
                    {docExtractResult.integrity_notes.map((note, i) => (
                      <li key={i}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default VerificationPage;
