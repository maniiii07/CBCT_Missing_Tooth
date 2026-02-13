import { Award, AlertTriangle, CheckCircle2, ClipboardEdit } from 'lucide-react';
import { useState } from 'react';

export default function DecisionCard({ decision, currentAnalysis }) {
  if (!decision) return null;

  // Use currentAnalysis if available (from manual edits), otherwise fall back to initial decision
  const analysis = currentAnalysis || decision.final_analysis;

  const [clinicalNotes, setClinicalNotes] = useState('');

  // Helper to get counts
  const getCounts = (field) => {
    let count = 0;
    [1, 2, 3, 4].forEach(q => {
      count += (analysis[`quadrant_${q}`]?.[field]?.length || 0);
    });
    return count;
  };

  const missingCount = getCounts('missing_teeth');
  const presentCount = getCounts('present_teeth');
  const impactedCount = getCounts('impacted_teeth');
  const notVisualizedCount = getCounts('not_visualized_teeth');

  return (
    <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
      {/* Header */}
      <div className="bg-slate-900 text-white p-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-500 rounded-lg">
            <Award className="w-8 h-8 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Radiographic Examination Report</h2>
            <p className="text-indigo-200">Forensic Odontology & Oral Radiology</p>
          </div>
          <div className="ml-auto text-right hidden md:block">
            <div className="text-sm text-gray-400">Date</div>
            <div className="text-xl font-bold text-white">{new Date().toLocaleDateString()}</div>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-8">
        {/* 1. Tooth Count Summary */}
        <section>
          <h3 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-4">
            1. Tooth Count Summary
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-xl border border-blue-100 text-center">
              <div className="text-3xl font-bold text-blue-700">{presentCount}</div>
              <div className="text-sm text-blue-600 font-medium">Present</div>
            </div>
            <div className="bg-red-50 p-4 rounded-xl border border-red-100 text-center">
              <div className="text-3xl font-bold text-red-700">{missingCount}</div>
              <div className="text-sm text-red-600 font-medium">Missing (Proven)</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-xl border border-purple-100 text-center">
              <div className="text-3xl font-bold text-purple-700">{impactedCount}</div>
              <div className="text-sm text-purple-600 font-medium">Impacted</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 text-center">
              <div className="text-3xl font-bold text-gray-700">{notVisualizedCount}</div>
              <div className="text-sm text-gray-600 font-medium">Not Visualized</div>
            </div>
          </div>
        </section>

        {/* 2. Teeth Present */}
        <section>
          <h3 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-4">
            2. Teeth Present
          </h3>
          <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 space-y-4">
            {[1, 2, 3, 4].map(q => {
              const present = analysis[`quadrant_${q}`]?.present_teeth || [];
              const sortedTeeth = [...present].sort((a, b) => a - b);

              if (sortedTeeth.length === 0) return null;

              return (
                <div key={q} className="flex border-b border-gray-200 last:border-0 pb-2 last:pb-0">
                  <span className="font-semibold text-gray-700 w-28">Quadrant {q}:</span>
                  <span className="text-gray-800 font-mono tracking-wide">
                    {sortedTeeth.join(', ')}
                  </span>
                </div>
              );
            })}
            {presentCount === 0 && (
              <p className="text-gray-500 italic">No teeth identified as present.</p>
            )}
          </div>
        </section>

        {/* 3. Teeth Missing */}
        <section>
          <h3 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-4">
            3. Teeth Missing
          </h3>
          <div className="bg-red-50 p-6 rounded-xl border border-red-100 space-y-4">
            {[1, 2, 3, 4].map(q => {
              const missing = analysis[`quadrant_${q}`]?.missing_teeth || [];
              const sortedTeeth = [...missing].sort((a, b) => a - b);

              if (sortedTeeth.length === 0) return null;

              return (
                <div key={q} className="flex border-b border-red-200 last:border-0 pb-2 last:pb-0">
                  <span className="font-semibold text-gray-700 w-28">Quadrant {q}:</span>
                  <span className="text-red-700 font-mono tracking-wide">
                    {sortedTeeth.join(', ')}
                  </span>
                </div>
              );
            })}
            {missingCount === 0 && (
              <p className="text-gray-500 italic">No teeth identified as missing.</p>
            )}
          </div>
        </section>

        {/* 4. Teeth Impacted */}
        <section>
          <h3 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-4">
            4. Teeth Impacted
          </h3>
          <div className="bg-purple-50 p-6 rounded-xl border border-purple-100 space-y-4">
            {[1, 2, 3, 4].map(q => {
              const impacted = analysis[`quadrant_${q}`]?.impacted_teeth || [];
              const sortedTeeth = [...impacted].sort((a, b) => a - b);

              if (sortedTeeth.length === 0) return null;

              return (
                <div key={q} className="flex border-b border-purple-200 last:border-0 pb-2 last:pb-0">
                  <span className="font-semibold text-gray-700 w-28">Quadrant {q}:</span>
                  <span className="text-purple-700 font-mono tracking-wide">
                    {sortedTeeth.join(', ')}
                  </span>
                </div>
              );
            })}
            {impactedCount === 0 && (
              <p className="text-gray-500 italic">No teeth identified as impacted.</p>
            )}
          </div>
        </section>

        {/* 5. Clinical Impression (Manual Input) */}
        <section>
          <div className="flex items-center justify-between border-b border-gray-200 pb-2 mb-4">
            <h3 className="text-lg font-bold text-gray-800">
              5. Clinical Impression
            </h3>
            <ClipboardEdit className="w-5 h-5 text-gray-400" />
          </div>

          <div className="bg-white">
            <textarea
              value={clinicalNotes}
              onChange={(e) => setClinicalNotes(e.target.value)}
              placeholder="Enter clinical impression and notes here..."
              className="w-full min-h-[150px] p-4 rounded-xl border border-gray-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none text-gray-700 resize-y"
            />
          </div>
        </section>

        {/* Disclaimer */}
        <div className="text-xs text-center text-gray-400 mt-8 pt-4 border-t border-gray-100">
          Interpretation is strictly radiographic and subject to clinical correlation.
        </div>
      </div>
    </div>
  );
}
