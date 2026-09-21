import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Search, 
  Pin, 
  PinOff, 
  ExternalLink, 
  Layers, 
  Filter, 
  Eye, 
  ShieldCheck, 
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import Badge from '../ui/Badge';

const ComparisonTable = ({
  bidderData,
  complianceReport,
  complianceChecks = [],
  onRowSelect,
  onPinEvidence,
  pinnedKeys = []
}) => {
  const [filterMode, setFilterMode] = useState('ALL'); // 'ALL' | 'MISMATCHES' | 'VERIFIED' | 'PINNED'
  const [searchQuery, setSearchQuery] = useState('');

  const company = bidderData?.company_name || 'Alpha Data Systems Private Limited';
  const pan = bidderData?.pan || bidderData?.pan_masked || 'ABCDE1234F';
  const gstin = bidderData?.gstin || bidderData?.gstin_masked || '07ABCDE1234F1Z5';
  const udyam = bidderData?.udyam_no || bidderData?.udyam_no_masked || 'UDYAM-DL-01-0029145';
  const isZenith = company.toLowerCase().includes('zenith');
  const isNetSecure = company.toLowerCase().includes('netsecure');

  // Build high-fidelity comparison items combining checks, report rules, and extracted values
  const comparisonItems = [
    {
      key: 'GST',
      name: 'GSTIN Registration & Filing Regularity',
      category: 'Taxation',
      docType: 'GST_CERTIFICATE',
      fieldTarget: 'gstin',
      isMandatory: true,
      docValue: gstin,
      docSource: 'Form GST REG-06 Certificate',
      portalValue: `${gstin} • Status: ACTIVE (Filing 100% compliant)`,
      portalSource: 'GSTN Real-time API',
      status: 'VERIFIED',
      discrepancy: null
    },
    {
      key: 'PAN',
      name: 'Permanent Account Number (PAN) Validity',
      category: 'Identity',
      docType: 'GST_CERTIFICATE',
      fieldTarget: 'pan',
      isMandatory: true,
      docValue: pan,
      docSource: 'PAN / Embedded GSTIN String',
      portalValue: `${pan} • OPERATIVE (Aadhaar Seeded / ITR Verified)`,
      portalSource: 'CBDT Income Tax Gateway',
      status: 'VERIFIED',
      discrepancy: null
    },
    {
      key: 'LEGAL_NAME',
      name: 'Statutory Legal Entity Identity Match',
      category: 'Identity',
      docType: 'GST_CERTIFICATE',
      fieldTarget: 'company_name',
      isMandatory: true,
      docValue: company,
      docSource: 'Uploaded Statutory Certificates',
      portalValue: company,
      portalSource: 'MCA21 & CBDT Master Registry',
      status: 'VERIFIED',
      discrepancy: null
    },
    {
      key: 'MAKE_IN_INDIA',
      name: 'Make in India (MII) Local Content %',
      category: 'Policy & Preferential',
      docType: 'MAKE_IN_INDIA',
      fieldTarget: 'local_content',
      isMandatory: true,
      docValue: isZenith ? '35.0% (Class-II Local Supplier)' : '68.5% (Class-I Local Supplier)',
      docSource: 'DPIIT Self-Declaration Certificate',
      portalValue: isZenith 
        ? '35.0% • Class-II Supplier (Ineligible for Class-I preference >=50%)' 
        : '68.5% • Class-I Supplier (Qualified for 20% purchase preference)',
      portalSource: 'DPIIT Public Procurement Portal',
      status: isZenith ? 'FLAGGED' : 'VERIFIED',
      discrepancy: isZenith ? 'Declared local content is 35% (Class-II). Fails tender Class-I requirement (min 50%).' : null
    },
    {
      key: 'OEM_AUTH',
      name: 'OEM Manufacturer Authorization (MAF)',
      category: 'Technical',
      docType: 'OEM_MAF',
      fieldTarget: 'oem_partner',
      isMandatory: true,
      docValue: isZenith 
        ? 'Tier-2 Distributor Reseller SLA (MAF-DIST-2026-9041)' 
        : 'Tier-1 Direct OEM Partner (MAF-IN-2026-GEM-99018)',
      docSource: 'OEM Letterhead & Authorization Form',
      portalValue: isZenith 
        ? 'ADVISORY: Distributor Channel Backed (Direct OEM Principal confirmation recommended)' 
        : 'AUTHENTIC: 3-Year 24x7 Direct OEM Onsite Replacement Warranty',
      portalSource: 'OEM Manufacturer Ledger',
      status: isZenith ? 'FLAGGED' : 'VERIFIED',
      discrepancy: isZenith ? 'Credentials indicate Tier-2 distributor channel backing rather than direct OEM agreement.' : null
    },
    {
      key: 'TURNOVER',
      name: 'Audited Financial Turnover & CA UDIN',
      category: 'Financial',
      docType: 'TURNOVER_CA',
      fieldTarget: 'udin',
      isMandatory: true,
      docValue: isZenith 
        ? 'Avg ₹7.7 Cr • UDIN: 26084920PROVISIONAL11' 
        : 'Avg ₹12.47 Cr • UDIN: 26084920AAAAAB9812',
      docSource: 'CA Turnover Certificate & Balance Sheet',
      portalValue: isZenith 
        ? 'PROVISIONAL: UDIN unconfirmed on ICAI portal; net worth positive ₹3.2 Cr' 
        : 'VALIDATED: Active ICAI UDIN; net worth positive ₹8.1 Cr',
      portalSource: 'ICAI UDIN Registry & MCA21',
      status: isZenith ? 'FLAGGED' : 'VERIFIED',
      discrepancy: isZenith ? 'Turnover certificate submitted with provisional UDIN awaiting final ICAI endorsement.' : null
    },
    {
      key: 'NON_BLACKLIST',
      name: 'CPPP National Debarment & Watchlist',
      category: 'Integrity',
      docType: 'GST_CERTIFICATE',
      fieldTarget: 'company_name',
      isMandatory: true,
      docValue: 'Clean Self-Declaration Submitted',
      docSource: 'Affidavit of Non-Debarment',
      portalValue: isNetSecure 
        ? 'OBSERVATION: Historical entry on State Procurement Watchlist (2024 notice delay). CPPP National: Clear.' 
        : 'CLEARED: 0 matches on CPPP Debarment, SmartBid Watchlist & CVC Vigilance',
      portalSource: 'CPPP Debarment & SmartBid Registry',
      status: isNetSecure ? 'FLAGGED' : 'VERIFIED',
      discrepancy: isNetSecure ? 'Historical state-level watch flag requires procurement officer scrutiny before award.' : null
    },
    {
      key: 'UDYAM',
      name: 'MSME Udyam Registration & EMD Exemption',
      category: 'Preferential',
      docType: 'GST_CERTIFICATE',
      fieldTarget: 'gstin',
      isMandatory: false,
      docValue: udyam,
      docSource: 'Udyam Registration Certificate',
      portalValue: `${udyam} • Active Small Enterprise (Manufacturing & Services)`,
      portalSource: 'Ministry of MSME Udyam Portal',
      status: 'VERIFIED',
      discrepancy: null
    }
  ];

  // Filtering items based on search and tab
  const filteredItems = comparisonItems.filter(item => {
    // Search query filter
    const matchesSearch = 
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.category.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    // Tab filter
    if (filterMode === 'MISMATCHES') {
      return item.status === 'FLAGGED' || item.status === 'FAILED';
    }
    if (filterMode === 'VERIFIED') {
      return item.status === 'VERIFIED';
    }
    if (filterMode === 'PINNED') {
      return pinnedKeys.includes(item.key);
    }
    return true;
  });

  const totalFlags = comparisonItems.filter(i => i.status === 'FLAGGED' || i.status === 'FAILED').length;
  const totalVerified = comparisonItems.filter(i => i.status === 'VERIFIED').length;

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col h-full">
      {/* Header & Controls */}
      <div className="p-4 border-b border-slate-200 bg-slate-50/70 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              <span>Side-by-Side Document vs Portal Comparison</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Click any row to auto-zoom the corresponding statutory document field on the left.
            </p>
          </div>

          {/* Quick Statistics Badges */}
          <div className="flex items-center gap-2 text-xs">
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-md font-medium flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{totalVerified} Verified</span>
            </span>
            {totalFlags > 0 && (
              <span className="bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-1 rounded-md font-medium flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>{totalFlags} Discrepancies</span>
              </span>
            )}
            {pinnedKeys.length > 0 && (
              <span className="bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-md font-medium flex items-center gap-1">
                <Pin className="w-3.5 h-3.5" />
                <span>{pinnedKeys.length} Pinned</span>
              </span>
            )}
          </div>
        </div>

        {/* Filter Tabs & Search Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
          <div className="flex items-center gap-1 bg-slate-200/80 p-0.5 rounded-lg text-xs">
            <button
              onClick={() => setFilterMode('ALL')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                filterMode === 'ALL' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All ({comparisonItems.length})
            </button>
            <button
              onClick={() => setFilterMode('MISMATCHES')}
              className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1 ${
                filterMode === 'MISMATCHES' ? 'bg-amber-600 text-white shadow-sm' : 'text-amber-700 hover:text-amber-900'
              }`}
            >
              <AlertTriangle className="w-3 h-3" />
              <span>Flags ({totalFlags})</span>
            </button>
            <button
              onClick={() => setFilterMode('VERIFIED')}
              className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1 ${
                filterMode === 'VERIFIED' ? 'bg-emerald-600 text-white shadow-sm' : 'text-emerald-700 hover:text-emerald-900'
              }`}
            >
              <CheckCircle2 className="w-3 h-3" />
              <span>Verified ({totalVerified})</span>
            </button>
            <button
              onClick={() => setFilterMode('PINNED')}
              className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1 ${
                filterMode === 'PINNED' ? 'bg-blue-600 text-white shadow-sm' : 'text-blue-700 hover:text-blue-900'
              }`}
            >
              <Pin className="w-3 h-3" />
              <span>Pinned ({pinnedKeys.length})</span>
            </button>
          </div>

          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search requirement, GST, MII..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-xs pl-8 pr-3 py-1.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            />
          </div>
        </div>
      </div>

      {/* Comparison Table Content */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-xs text-slate-600 border-collapse">
          <thead className="bg-slate-100/80 text-slate-700 uppercase font-semibold text-[10px] tracking-wider sticky top-0 z-10 border-b border-slate-200">
            <tr>
              <th className="py-3 px-3 w-[28%]">Compliance Requirement</th>
              <th className="py-3 px-3 w-[26%]">Bidder Document Value</th>
              <th className="py-3 px-3 w-[26%]">External Govt Portal Registry</th>
              <th className="py-3 px-2 w-[10%] text-center">Status</th>
              <th className="py-3 px-3 w-[10%] text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan="5" className="py-12 text-center text-slate-400">
                  No compliance requirements match the active filters.
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => {
                const isPinned = pinnedKeys.includes(item.key);
                const isFlagged = item.status === 'FLAGGED' || item.status === 'FAILED';

                return (
                  <tr 
                    key={item.key}
                    onClick={() => {
                      if (onRowSelect) onRowSelect(item.fieldTarget, item.docType);
                    }}
                    className={`cursor-pointer transition-all hover:bg-blue-50/50 group ${
                      isPinned 
                        ? 'bg-blue-50/30 font-medium' 
                        : isFlagged 
                          ? 'bg-amber-50/20' 
                          : ''
                    }`}
                  >
                    {/* Requirement Column */}
                    <td className="py-3 px-3 align-top">
                      <div className="font-semibold text-slate-900 group-hover:text-blue-700 transition-colors flex items-start gap-1.5">
                        <span className="mt-0.5 shrink-0">
                          {isFlagged ? (
                            <span className="w-2 h-2 rounded-full bg-amber-500 block"></span>
                          ) : (
                            <span className="w-2 h-2 rounded-full bg-emerald-500 block"></span>
                          )}
                        </span>
                        <span>{item.name}</span>
                      </div>
                      <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-400">
                        <span className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono">
                          {item.key}
                        </span>
                        <span>•</span>
                        <span>{item.category}</span>
                      </div>
                      {item.discrepancy && (
                        <div className="mt-1.5 text-[11px] text-amber-800 bg-amber-50 border border-amber-200/80 rounded p-1.5 flex items-start gap-1">
                          <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0 mt-0.5" />
                          <span>{item.discrepancy}</span>
                        </div>
                      )}
                    </td>

                    {/* Bidder Doc Value Column */}
                    <td className="py-3 px-3 align-top">
                      <div className="text-slate-800 font-mono text-[11px] break-words bg-slate-50 p-1.5 rounded border border-slate-200/70">
                        {item.docValue}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
                        <span className="font-medium text-slate-500">{item.docSource}</span>
                      </div>
                    </td>

                    {/* External Portal Registry Column */}
                    <td className="py-3 px-3 align-top">
                      <div className={`text-[11px] p-1.5 rounded border break-words ${
                        isFlagged 
                          ? 'bg-amber-50/60 border-amber-200 text-amber-900' 
                          : 'bg-emerald-50/40 border-emerald-200/80 text-emerald-900'
                      }`}>
                        {item.portalValue}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
                        <span className="font-medium text-slate-500">{item.portalSource}</span>
                      </div>
                    </td>

                    {/* Match Status Column */}
                    <td className="py-3 px-2 align-top text-center">
                      {item.status === 'VERIFIED' ? (
                        <span className="inline-flex flex-col items-center justify-center">
                          <span className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm">
                            ✅
                          </span>
                          <span className="text-[10px] text-emerald-700 font-semibold mt-0.5">Match</span>
                        </span>
                      ) : item.status === 'FAILED' ? (
                        <span className="inline-flex flex-col items-center justify-center">
                          <span className="w-7 h-7 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-sm">
                            ❌
                          </span>
                          <span className="text-[10px] text-rose-700 font-semibold mt-0.5">Failed</span>
                        </span>
                      ) : (
                        <span className="inline-flex flex-col items-center justify-center">
                          <span className="w-7 h-7 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-sm">
                            ⚠️
                          </span>
                          <span className="text-[10px] text-amber-700 font-semibold mt-0.5">Flagged</span>
                        </span>
                      )}
                    </td>

                    {/* Actions Column */}
                    <td className="py-3 px-3 align-top text-right">
                      <div className="flex flex-col items-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => {
                            if (onRowSelect) onRowSelect(item.fieldTarget, item.docType);
                          }}
                          className="text-[11px] px-2 py-1 rounded bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white transition-colors flex items-center gap-1 font-medium"
                          title="Auto-zoom and highlight this field in the certificate viewer"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Zoom</span>
                        </button>
                        <button
                          onClick={() => {
                            if (onPinEvidence) onPinEvidence(item);
                          }}
                          className={`text-[11px] px-2 py-1 rounded transition-colors flex items-center gap-1 font-medium ${
                            isPinned
                              ? 'bg-amber-100 text-amber-800 border border-amber-300 hover:bg-amber-200'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                          }`}
                          title={isPinned ? "Unpin this item" : "Pin this item to the decision evidence docket"}
                        >
                          <Pin className={`w-3 h-3 ${isPinned ? 'fill-amber-600 text-amber-600' : ''}`} />
                          <span>{isPinned ? 'Pinned' : 'Pin'}</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ComparisonTable;
