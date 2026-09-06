import React, { useState, useEffect, useRef } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  RotateCcw, 
  Pin, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldCheck, 
  Award, 
  Stamp, 
  QrCode, 
  Eye, 
  Layers
} from 'lucide-react';

const DOC_TYPES = [
  { id: 'GST_CERTIFICATE', label: 'GST REG-06 Certificate', code: 'REG-06' },
  { id: 'MAKE_IN_INDIA', label: 'DPIIT Local Content (MII)', code: 'MII-DPIIT' },
  { id: 'OEM_MAF', label: 'OEM Authorization (MAF)', code: 'MAF-OEM' },
  { id: 'TURNOVER_CA', label: 'CA Audited Turnover & UDIN', code: 'CA-UDIN' },
  { id: 'PAN_CARD', label: 'Income Tax PAN Card', code: 'ITD-PAN' }
];

const PDFViewer = ({
  bidderData,
  selectedDocType = 'GST_CERTIFICATE',
  onSelectDocType,
  activeFieldHighlight = null,
  onClearHighlight,
  onPinField
}) => {
  const [zoomLevel, setZoomLevel] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  // Field element refs for auto-scroll and focus
  const fieldRefs = {
    company_name: useRef(null),
    gstin: useRef(null),
    pan: useRef(null),
    local_content: useRef(null),
    udin: useRef(null),
    signature: useRef(null),
    oem_partner: useRef(null)
  };

  // Handle auto-zoom and smooth scroll to highlighted field
  useEffect(() => {
    if (activeFieldHighlight && fieldRefs[activeFieldHighlight]?.current) {
      // Temporarily zoom in slightly if at base zoom
      if (zoomLevel < 115) {
        setZoomLevel(115);
      }
      setTimeout(() => {
        fieldRefs[activeFieldHighlight]?.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }, 100);
    }
  }, [activeFieldHighlight]);

  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 15, 175));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 15, 65));
  const handleResetZoom = () => setZoomLevel(100);

  const company = bidderData?.company_name || 'Alpha Data Systems Private Limited';
  const pan = bidderData?.pan || bidderData?.pan_masked || 'ABCDE1234F';
  const gstin = bidderData?.gstin || bidderData?.gstin_masked || '07ABCDE1234F1Z5';
  const udyam = bidderData?.udyam_no || bidderData?.udyam_no_masked || 'UDYAM-DL-01-0029145';
  const isZenith = company.toLowerCase().includes('zenith');

  // Renders the highlight box styling
  const getFieldHighlightStyle = (fieldKey) => {
    const isTarget = activeFieldHighlight === fieldKey;
    if (!isTarget) return "border border-slate-200/80 bg-slate-50/40 hover:bg-blue-50/30 transition-colors";
    return "border-2 border-amber-500 bg-amber-100/60 ring-4 ring-amber-400/40 shadow-md animate-pulse transition-all duration-300";
  };

  return (
    <div 
      ref={containerRef}
      className={`bg-slate-900 border border-slate-800 rounded-xl flex flex-col h-full overflow-hidden shadow-xl ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none' : 'relative'
      }`}
      role="region"
      aria-label="Statutory Document and PDF Viewer"
    >
      {/* Top Toolbar */}
      <div className="bg-slate-850 px-4 py-2.5 border-b border-slate-750 flex flex-wrap items-center justify-between gap-3 text-slate-200">
        {/* Document Switcher Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto py-0.5">
          <Layers className="w-4 h-4 text-blue-400 shrink-0 mr-1" />
          {DOC_TYPES.map((dt) => (
            <button
              key={dt.id}
              onClick={() => {
                if (onSelectDocType) onSelectDocType(dt.id);
                if (onClearHighlight) onClearHighlight();
              }}
              className={`text-xs px-2.5 py-1 rounded-md font-medium whitespace-nowrap transition-all flex items-center gap-1.5 ${
                selectedDocType === dt.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-800/80 text-slate-400 hover:bg-slate-700/80 hover:text-slate-200'
              }`}
            >
              <FileText className="w-3 h-3" />
              <span>{dt.code}</span>
            </button>
          ))}
        </div>

        {/* Zoom and Display Controls */}
        <div className="flex items-center gap-1.5 shrink-0 ml-auto">
          {activeFieldHighlight && (
            <button
              onClick={onClearHighlight}
              className="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded flex items-center gap-1 hover:bg-amber-500/30 transition-colors mr-2"
              title="Clear active field highlight"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span>
              <span>Field: {activeFieldHighlight.toUpperCase()}</span>
              <span className="ml-1 font-bold">×</span>
            </button>
          )}

          <div className="flex items-center bg-slate-800 rounded-lg p-0.5 border border-slate-700">
            <button
              onClick={handleZoomOut}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors"
              title="Zoom Out"
              aria-label="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-xs font-mono px-2 text-slate-300 min-w-[3.2rem] text-center font-medium">
              {zoomLevel}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors"
              title="Zoom In"
              aria-label="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors ml-0.5"
              title="Reset Zoom to 100%"
              aria-label="Reset Zoom"
            >
              <RotateCcw className="w-3 h-3" />
            </button>
          </div>

          <button
            onClick={() => setIsFullscreen(prev => !prev)}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg border border-slate-700 transition-colors"
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Viewer"}
            aria-label="Toggle Fullscreen"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* PDF Viewport Scroll Canvas */}
      <div className="flex-1 overflow-auto bg-slate-950/80 p-4 sm:p-6 flex justify-center items-start">
        <div 
          className="transition-transform duration-200 origin-top shadow-2xl"
          style={{ transform: `scale(${zoomLevel / 100})`, width: '780px' }}
        >
          {/* Certificate Paper Container */}
          <div className="bg-white text-slate-900 rounded-sm p-8 sm:p-10 border-4 border-slate-200 shadow-2xl relative min-h-[960px] font-sans">
            {/* Watermark Pattern */}
            <div className="absolute inset-0 pointer-events-none opacity-[0.03] flex items-center justify-center select-none overflow-hidden">
              <div className="text-7xl font-serif font-black tracking-widest text-slate-900 rotate-[-30deg]">
                GOVERNMENT OF INDIA • GeM VERIFIED
              </div>
            </div>

            {/* Certificate Header Emblem & Title */}
            <div className="border-b-2 border-slate-800 pb-4 mb-6 text-center relative">
              <div className="flex justify-between items-start">
                <div className="text-left text-[10px] text-slate-500 font-mono">
                  <div>DOC REF: GeM-VER-2026-X09</div>
                  <div>SECURE SHA-256 VAULT VERIFIED</div>
                </div>
                {/* National Emblem Ashoka Pillar simulation */}
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 rounded-full border-2 border-blue-900/60 bg-blue-50/50 flex items-center justify-center text-blue-900 mb-1">
                    <ShieldCheck className="w-6 h-6 text-blue-900" />
                  </div>
                  <span className="text-[11px] font-serif font-bold uppercase tracking-wider text-slate-800">
                    Satyameva Jayate
                  </span>
                </div>
                <div className="text-right">
                  <QrCode className="w-12 h-12 text-slate-800" />
                  <span className="text-[9px] font-mono text-slate-500">NIC-QR-AUTH</span>
                </div>
              </div>

              {/* Dynamic Header Based on Certificate Type */}
              {selectedDocType === 'GST_CERTIFICATE' && (
                <div className="mt-2">
                  <h1 className="text-xl font-serif font-extrabold text-blue-950 uppercase tracking-tight">
                    Government of India
                  </h1>
                  <h2 className="text-sm font-semibold text-slate-700">
                    Form GST REG-06 • Registration Certificate
                  </h2>
                  <p className="text-[11px] text-slate-500 italic mt-0.5">
                    Issued under Section 25 of the Central Goods and Services Tax Act, 2017
                  </p>
                </div>
              )}

              {selectedDocType === 'MAKE_IN_INDIA' && (
                <div className="mt-2">
                  <h1 className="text-xl font-serif font-extrabold text-blue-950 uppercase tracking-tight">
                    Department for Promotion of Industry and Internal Trade (DPIIT)
                  </h1>
                  <h2 className="text-sm font-semibold text-slate-700">
                    Make in India (Public Procurement Preference) Local Content Certificate
                  </h2>
                  <p className="text-[11px] text-slate-500 italic mt-0.5">
                    Order P-45021/2/2017-PP (BE-II) • Statutory Local Value Addition Declaration
                  </p>
                </div>
              )}

              {selectedDocType === 'OEM_MAF' && (
                <div className="mt-2">
                  <h1 className="text-xl font-serif font-extrabold text-blue-950 uppercase tracking-tight">
                    Manufacturer Authorization Form (MAF)
                  </h1>
                  <h2 className="text-sm font-semibold text-slate-700">
                    Original Equipment Manufacturer (OEM) Direct Enterprise SLA Letter
                  </h2>
                  <p className="text-[11px] text-slate-500 italic mt-0.5">
                    Tender Reference: GEM/2026/B/1049281 • Server & Compute Hardware
                  </p>
                </div>
              )}

              {selectedDocType === 'TURNOVER_CA' && (
                <div className="mt-2">
                  <h1 className="text-xl font-serif font-extrabold text-blue-950 uppercase tracking-tight">
                    Chartered Accountant Audited Turnover Certificate
                  </h1>
                  <h2 className="text-sm font-semibold text-slate-700">
                    Annual Financial Turnover & Net Worth Attestation with ICAI UDIN
                  </h2>
                  <p className="text-[11px] text-slate-500 italic mt-0.5">
                    Issued by Fellow Member of Institute of Chartered Accountants of India (ICAI)
                  </p>
                </div>
              )}

              {selectedDocType === 'PAN_CARD' && (
                <div className="mt-2">
                  <h1 className="text-xl font-serif font-extrabold text-blue-950 uppercase tracking-tight">
                    Income Tax Department • Government of India
                  </h1>
                  <h2 className="text-sm font-semibold text-slate-700">
                    Permanent Account Number (PAN) Corporate Identity Credential
                  </h2>
                </div>
              )}
            </div>

            {/* Document Body Content with Interactive Highlight Bounding Boxes */}
            <div className="space-y-4 text-xs text-slate-800">
              {/* Field: Legal Entity Name */}
              <div 
                ref={fieldRefs.company_name}
                className={`p-3 rounded-md relative ${getFieldHighlightStyle('company_name')}`}
              >
                <div className="flex justify-between items-start">
                  <div className="space-y-0.5">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                      1. Legal Name of Enterprise
                    </span>
                    <div className="text-sm font-bold text-slate-900 font-serif">
                      {company}
                    </div>
                  </div>
                  {onPinField && (
                    <button
                      onClick={() => onPinField('COMPANY_NAME', company, 'Legal name verified from uploaded statutory certificate.')}
                      className="text-[10px] bg-slate-200/80 hover:bg-blue-600 hover:text-white px-2 py-0.5 rounded text-slate-700 font-medium transition-colors flex items-center gap-1"
                      title="Pin Legal Name as Evidence"
                    >
                      <Pin className="w-2.5 h-2.5" />
                      <span>Pin Evidence</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Field: Registration Number / GSTIN */}
              <div 
                ref={fieldRefs.gstin}
                className={`p-3 rounded-md relative ${getFieldHighlightStyle('gstin')}`}
              >
                <div className="flex justify-between items-start">
                  <div className="space-y-0.5">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                      2. Goods and Services Tax Identification Number (GSTIN)
                    </span>
                    <div className="text-sm font-mono font-bold text-blue-900 tracking-wide">
                      {gstin}
                    </div>
                  </div>
                  {onPinField && (
                    <button
                      onClick={() => onPinField('GSTIN', gstin, 'GSTIN registration extracted and validated against GSTN portal.')}
                      className="text-[10px] bg-slate-200/80 hover:bg-blue-600 hover:text-white px-2 py-0.5 rounded text-slate-700 font-medium transition-colors flex items-center gap-1"
                      title="Pin GSTIN as Evidence"
                    >
                      <Pin className="w-2.5 h-2.5" />
                      <span>Pin Evidence</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Field: Permanent Account Number (PAN) */}
              <div 
                ref={fieldRefs.pan}
                className={`p-3 rounded-md relative ${getFieldHighlightStyle('pan')}`}
              >
                <div className="flex justify-between items-start">
                  <div className="space-y-0.5">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                      3. Permanent Account Number (PAN)
                    </span>
                    <div className="text-sm font-mono font-bold text-slate-900 tracking-wide">
                      {pan}
                    </div>
                  </div>
                  {onPinField && (
                    <button
                      onClick={() => onPinField('PAN', pan, 'PAN verified against CBDT database and embedded GSTIN string.')}
                      className="text-[10px] bg-slate-200/80 hover:bg-blue-600 hover:text-white px-2 py-0.5 rounded text-slate-700 font-medium transition-colors flex items-center gap-1"
                      title="Pin PAN as Evidence"
                    >
                      <Pin className="w-2.5 h-2.5" />
                      <span>Pin Evidence</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Field: Make In India Local Content */}
              {selectedDocType === 'MAKE_IN_INDIA' && (
                <div 
                  ref={fieldRefs.local_content}
                  className={`p-3 rounded-md relative ${getFieldHighlightStyle('local_content')}`}
                >
                  <div className="flex justify-between items-start">
                    <div className="space-y-0.5">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                        4. Declared Local Content & DPIIT Supplier Classification
                      </span>
                      <div className="text-sm font-bold text-slate-900 flex items-center gap-2">
                        <span>{isZenith ? '35.0% Local Content' : '68.5% Local Content'}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                          isZenith 
                            ? 'bg-amber-100 text-amber-800 border border-amber-300' 
                            : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        }`}>
                          {isZenith ? 'Class-II Local Supplier (>=20% & <50%)' : 'Class-I Local Supplier (>=50%)'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-600 mt-1">
                        Manufacturing Site: Plot 18-A, MIDC Electronics Complex, Phase-II. 
                        Local content computed in conformity with Rule 153(iii) of GFR 2017.
                      </p>
                    </div>
                    {onPinField && (
                      <button
                        onClick={() => onPinField(
                          'LOCAL_CONTENT', 
                          isZenith ? '35.0% (Class-II)' : '68.5% (Class-I)',
                          isZenith 
                            ? 'Flagged: 35% local content fails tender Class-I requirement (min 50%).'
                            : 'Verified: 68.5% exceeds Class-I threshold.'
                        )}
                        className="text-[10px] bg-slate-200/80 hover:bg-blue-600 hover:text-white px-2 py-0.5 rounded text-slate-700 font-medium transition-colors flex items-center gap-1"
                      >
                        <Pin className="w-2.5 h-2.5" />
                        <span>Pin Evidence</span>
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Field: CA UDIN & Financial Turnover */}
              {selectedDocType === 'TURNOVER_CA' && (
                <div 
                  ref={fieldRefs.udin}
                  className={`p-3 rounded-md relative ${getFieldHighlightStyle('udin')}`}
                >
                  <div className="flex justify-between items-start">
                    <div className="space-y-0.5">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                        5. ICAI Mandatory Unique Document Identification Number (UDIN)
                      </span>
                      <div className="text-sm font-mono font-bold text-slate-900 flex items-center gap-2">
                        <span>{isZenith ? '26084920PROVISIONAL11' : '26084920AAAAAB9812'}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                          isZenith 
                            ? 'bg-amber-100 text-amber-800 border border-amber-300' 
                            : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        }`}>
                          {isZenith ? 'PROVISIONAL PENDING' : 'ICAI VERIFIED'}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 mt-2 pt-2 border-t border-slate-200 text-[11px]">
                        <div>FY 2024-25: <span className="font-semibold">{isZenith ? '₹8.4 Cr' : '₹14.8 Cr'}</span></div>
                        <div>FY 2023-24: <span className="font-semibold">{isZenith ? '₹7.9 Cr' : '₹12.2 Cr'}</span></div>
                        <div>3-Yr Avg: <span className="font-semibold text-blue-900">{isZenith ? '₹7.7 Cr' : '₹12.47 Cr'}</span></div>
                      </div>
                    </div>
                    {onPinField && (
                      <button
                        onClick={() => onPinField('CA_UDIN', isZenith ? '26084920PROVISIONAL11' : '26084920AAAAAB9812', 'CA turnover certificate with UDIN.')}
                        className="text-[10px] bg-slate-200/80 hover:bg-blue-600 hover:text-white px-2 py-0.5 rounded text-slate-700 font-medium transition-colors flex items-center gap-1"
                      >
                        <Pin className="w-2.5 h-2.5" />
                        <span>Pin Evidence</span>
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Field: OEM Authorization Code */}
              {selectedDocType === 'OEM_MAF' && (
                <div 
                  ref={fieldRefs.oem_partner}
                  className={`p-3 rounded-md relative ${getFieldHighlightStyle('oem_partner')}`}
                >
                  <div className="flex justify-between items-start">
                    <div className="space-y-0.5">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                        6. OEM Principal Authorization Credentials
                      </span>
                      <div className="text-sm font-semibold text-slate-900">
                        OEM Principal: <span className="font-bold text-blue-950">Bharath Tech Computronix India Pvt Ltd</span>
                      </div>
                      <div className="text-[11px] text-slate-600">
                        Tier Level: <span className="font-semibold">{isZenith ? 'Tier-2 Distributor Channel' : 'Tier-1 Master Enterprise Partner'}</span>
                      </div>
                      <div className="text-[11px] text-slate-600">
                        MAF Reference Code: <span className="font-mono font-semibold text-blue-900">{isZenith ? 'MAF-DIST-2026-9041' : 'MAF-IN-2026-GEM-99018'}</span>
                      </div>
                    </div>
                    {onPinField && (
                      <button
                        onClick={() => onPinField('OEM_AUTH', isZenith ? 'Tier-2 Distributor' : 'Tier-1 Partner', 'OEM Authorization status.')}
                        className="text-[10px] bg-slate-200/80 hover:bg-blue-600 hover:text-white px-2 py-0.5 rounded text-slate-700 font-medium transition-colors flex items-center gap-1"
                      >
                        <Pin className="w-2.5 h-2.5" />
                        <span>Pin Evidence</span>
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Static Details Grid */}
              <div className="border border-slate-200 rounded-md p-3 bg-slate-50/50 space-y-1.5 text-[11px]">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-slate-500">Registration Date:</span>{' '}
                    <span className="font-medium text-slate-800">01/07/2017</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Jurisdiction Office:</span>{' '}
                    <span className="font-medium text-slate-800">Ward 42, Central Public Procurement</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Constitution:</span>{' '}
                    <span className="font-medium text-slate-800">Private Limited Company</span>
                  </div>
                  <div>
                    <span className="text-slate-500">MSME Udyam Reference:</span>{' '}
                    <span className="font-mono font-medium text-slate-800">{udyam}</span>
                  </div>
                </div>
              </div>

              {/* Signature, Stamps, and Holographic Verification Seal */}
              <div 
                ref={fieldRefs.signature}
                className={`border-t-2 border-slate-300 pt-4 mt-6 flex justify-between items-end p-2 rounded-md ${getFieldHighlightStyle('signature')}`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-emerald-800">
                    <Stamp className="w-6 h-6 text-blue-900" />
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-900">
                        Official Authorized Seal
                      </div>
                      <div className="text-[10px] text-slate-600">
                        Duly Signed & Affixed by Principal Signatory
                      </div>
                    </div>
                  </div>
                  <div className="text-[9px] font-mono text-slate-400">
                    DIGITAL SIGNATURE ID: NIC-DSIG-2026-981273-PASS
                  </div>
                </div>

                <div className="text-right space-y-1">
                  <div className="h-10 border-b border-slate-400 w-36 ml-auto flex items-end justify-center pb-1">
                    <span className="font-serif italic text-blue-950 font-bold text-sm tracking-wide">
                      R. K. Sharma
                    </span>
                  </div>
                  <div className="text-[10px] font-bold text-slate-800">
                    Authorized Signatory
                  </div>
                  <div className="text-[9px] text-slate-500">
                    For {company}
                  </div>
                </div>
              </div>
            </div>

            {/* Certificate Footer Notice */}
            <div className="mt-8 pt-3 border-t border-slate-200 text-[9px] text-slate-400 text-center font-mono">
              VERIFIED UNDER GOVERNMENT E-MARKETPLACE (GeM) AUTOMATED STATUTORY INTEGRITY GATEWAY • 2026
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFViewer;
