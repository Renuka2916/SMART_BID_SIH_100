import React from 'react';
import { 
  Pin, 
  Trash2, 
  AlertTriangle, 
  CheckCircle2, 
  FileText, 
  X, 
  FileCheck2,
  FolderArchive
} from 'lucide-react';

const PinnedEvidenceDocket = ({
  pinnedItems = [],
  onRemovePin,
  onClearAllPins
}) => {
  if (pinnedItems.length === 0) return null;

  return (
    <div className="bg-amber-50/50 border border-amber-200 rounded-xl p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-950 font-bold text-xs">
          <FolderArchive className="w-4 h-4 text-amber-700" />
          <span>Pinned Evidence & Statutory Findings Docket ({pinnedItems.length} items)</span>
        </div>
        {onClearAllPins && pinnedItems.length > 1 && (
          <button
            onClick={onClearAllPins}
            className="text-[11px] text-slate-500 hover:text-rose-600 transition-colors font-medium flex items-center gap-1"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear All</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {pinnedItems.map((item) => (
          <div 
            key={item.key}
            className="bg-white border border-amber-200/90 rounded-lg p-2.5 shadow-xs flex flex-col justify-between text-xs space-y-1.5 relative group"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="font-bold text-slate-900 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                <span>{item.name || item.key}</span>
              </div>
              {onRemovePin && (
                <button
                  onClick={() => onRemovePin(item.key)}
                  className="text-slate-400 hover:text-rose-600 p-0.5 rounded transition-colors"
                  title="Remove from pinned docket"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            <div className="text-[11px] text-slate-700 bg-slate-50 p-1.5 rounded border border-slate-100 font-mono">
              {item.docValue}
            </div>

            {item.discrepancy && (
              <div className="text-[10px] text-amber-800 italic">
                {item.discrepancy}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default PinnedEvidenceDocket;
