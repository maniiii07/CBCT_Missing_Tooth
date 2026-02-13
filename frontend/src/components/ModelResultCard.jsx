import { Brain, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

const MODEL_COLORS = {
  'GPT-4o': { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', icon: 'text-emerald-500' },
  'Gemini': { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: 'text-blue-500' },
  'Anthropic Claude': { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', icon: 'text-purple-500' },
};

function QuadrantSummary({ quadrant, number }) {
  const missing = quadrant?.missing_teeth || [];
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-gray-600 text-sm">Q{number}</span>
      <span className={`text-sm font-medium ${missing.length > 0 ? 'text-red-600' : 'text-green-600'}`}>
        {missing.length > 0 ? missing.join(', ') : 'None missing'}
      </span>
    </div>
  );
}

export default function ModelResultCard({ result, isSelected = false }) {
  const [expanded, setExpanded] = useState(false);
  const colors = MODEL_COLORS[result.model_name] || MODEL_COLORS['GPT-4o'];
  
  const totalMissing = 
    (result.quadrant_1?.missing_teeth?.length || 0) +
    (result.quadrant_2?.missing_teeth?.length || 0) +
    (result.quadrant_3?.missing_teeth?.length || 0) +
    (result.quadrant_4?.missing_teeth?.length || 0);

  return (
    <div className={`rounded-xl border-2 ${colors.border} ${colors.bg} p-4 transition-all ${isSelected ? 'ring-2 ring-offset-2 ring-indigo-500' : ''}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Brain className={`w-5 h-5 ${colors.icon}`} />
          <h4 className={`font-semibold ${colors.text}`}>{result.model_name}</h4>
          {isSelected && (
            <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full">
              Selected
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">
            Confidence: <span className="font-medium">{(result.confidence * 100).toFixed(0)}%</span>
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 mb-3">
        <QuadrantSummary quadrant={result.quadrant_1} number={1} />
        <QuadrantSummary quadrant={result.quadrant_2} number={2} />
        <QuadrantSummary quadrant={result.quadrant_3} number={3} />
        <QuadrantSummary quadrant={result.quadrant_4} number={4} />
      </div>
      
      <div className="flex items-center justify-between pt-2 border-t border-gray-200">
        <span className="text-sm font-medium text-gray-700">
          Total Missing: <span className={totalMissing > 0 ? 'text-red-600' : 'text-green-600'}>{totalMissing}</span>
        </span>
        <button 
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
        >
          {expanded ? 'Hide details' : 'Show details'}
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>
      
      {expanded && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="space-y-2 text-sm">
            {[1, 2, 3, 4].map((q) => {
              const quadrant = result[`quadrant_${q}`];
              return (
                <div key={q} className="bg-white/50 rounded-lg p-2">
                  <div className="font-medium text-gray-700">Quadrant {q}</div>
                  <div className="text-gray-600">
                    <span className="text-red-600">Missing: </span>
                    {quadrant?.missing_teeth?.length > 0 ? quadrant.missing_teeth.join(', ') : 'None'}
                  </div>
                  {quadrant?.notes && (
                    <div className="text-gray-500 italic mt-1">{quadrant.notes}</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
