import { useState } from 'react';
import { CheckCircle, XCircle, HelpCircle, ArrowDownCircle, MousePointer2 } from 'lucide-react';

const QUADRANT_TEETH = {
  1: [18, 17, 16, 15, 14, 13, 12, 11],
  2: [21, 22, 23, 24, 25, 26, 27, 28],
  3: [31, 32, 33, 34, 35, 36, 37, 38],
  4: [48, 47, 46, 45, 44, 43, 42, 41],
};

const QUADRANT_LABELS = {
  1: 'Upper Right (Q1)',
  2: 'Upper Left (Q2)',
  3: 'Lower Left (Q3)',
  4: 'Lower Right (Q4)',
};

function ToothIcon({ number, isMissing, isPresent, isImpacted, onClick, activeTool }) {
  const baseClasses = 'w-10 h-12 rounded-lg flex flex-col items-center justify-center text-xs font-medium transition-all cursor-pointer hover:opacity-80 active:scale-95 select-none';

  let content = null;
  let styleClasses = `${baseClasses} bg-gray-100 border-2 border-gray-300 text-gray-500 hover:bg-gray-200`;

  if (isMissing) {
    styleClasses = `${baseClasses} bg-red-100 border-2 border-red-400 text-red-700 hover:bg-red-200`;
    content = <XCircle className="w-4 h-4 mb-0.5" />;
  } else if (isPresent) {
    styleClasses = `${baseClasses} bg-green-100 border-2 border-green-400 text-green-700 hover:bg-green-200`;
    content = <CheckCircle className="w-4 h-4 mb-0.5" />;
  } else if (isImpacted) {
    styleClasses = `${baseClasses} bg-purple-100 border-2 border-purple-400 text-purple-700 hover:bg-purple-200`;
    content = <ArrowDownCircle className="w-4 h-4 mb-0.5" />;
  } else {
    content = <HelpCircle className="w-4 h-4 mb-0.5" />;
  }

  return (
    <div
      onClick={() => onClick(number)}
      className={styleClasses}
      title={`Click to mark as ${activeTool}`}
    >
      {content}
      <span>{number}</span>
    </div>
  );
}

function QuadrantRow({ quadrant, missingTeeth = [], presentTeeth = [], impactedTeeth = [], reverse = false, onToothClick, activeTool }) {
  const teeth = QUADRANT_TEETH[quadrant];
  const displayTeeth = reverse ? [...teeth].reverse() : teeth;

  return (
    <div className="flex gap-1">
      {displayTeeth.map((tooth) => (
        <ToothIcon
          key={tooth}
          number={tooth}
          isMissing={missingTeeth.includes(tooth)}
          isPresent={presentTeeth.includes(tooth)}
          isImpacted={impactedTeeth.includes(tooth)}
          onClick={(toothNum) => onToothClick(quadrant, toothNum)}
          activeTool={activeTool}
        />
      ))}
    </div>
  );
}

export default function DentalChart({ analysis, onToothUpdate }) {
  if (!analysis) return null;

  const [activeTool, setActiveTool] = useState('present'); // 'present', 'missing', 'impacted'

  const { quadrant_1, quadrant_2, quadrant_3, quadrant_4 } = analysis;

  const handleToothClick = (quadrant, number) => {
    onToothUpdate(quadrant, number, activeTool);
  };

  const tools = [
    { id: 'present', label: 'Present', icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', border: 'border-green-300' },
    { id: 'missing', label: 'Missing', icon: XCircle, color: 'text-red-600', bg: 'bg-red-100', border: 'border-red-300' },
    { id: 'impacted', label: 'Impacted', icon: ArrowDownCircle, color: 'text-purple-600', bg: 'bg-purple-100', border: 'border-purple-300' },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-800">Dental Chart</h3>

        {/* Toolbar */}
        <div className="flex bg-gray-100 p-1 rounded-lg gap-1">
          {tools.map((tool) => {
            const Icon = tool.icon;
            const isActive = activeTool === tool.id;
            return (
              <button
                key={tool.id}
                onClick={() => setActiveTool(tool.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${isActive
                    ? 'bg-white shadow-sm text-gray-900 border border-gray-200'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
                  }`}
              >
                <div className={`w-2 h-2 rounded-full ${isActive ? tool.color.replace('text', 'bg') : 'bg-gray-400'}`} />
                {tool.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex flex-col items-center gap-2">
        {/* Upper jaw */}
        <div className="text-xs text-gray-500 mb-1">UPPER JAW</div>
        <div className="flex gap-4">
          <div className="text-right">
            <div className="text-xs text-gray-400 mb-1">{QUADRANT_LABELS[1]}</div>
            <QuadrantRow
              quadrant={1}
              missingTeeth={quadrant_1?.missing_teeth || []}
              presentTeeth={quadrant_1?.present_teeth || []}
              impactedTeeth={quadrant_1?.impacted_teeth || []}
              onToothClick={handleToothClick}
              activeTool={activeTool}
            />
          </div>
          <div className="w-px bg-gray-300"></div>
          <div>
            <div className="text-xs text-gray-400 mb-1">{QUADRANT_LABELS[2]}</div>
            <QuadrantRow
              quadrant={2}
              missingTeeth={quadrant_2?.missing_teeth || []}
              presentTeeth={quadrant_2?.present_teeth || []}
              impactedTeeth={quadrant_2?.impacted_teeth || []}
              onToothClick={handleToothClick}
              activeTool={activeTool}
            />
          </div>
        </div>

        {/* Divider */}
        <div className="w-full max-w-xl h-px bg-gray-300 my-2"></div>

        {/* Lower jaw */}
        <div className="flex gap-4">
          <div className="text-right">
            <QuadrantRow
              quadrant={4}
              missingTeeth={quadrant_4?.missing_teeth || []}
              presentTeeth={quadrant_4?.present_teeth || []}
              impactedTeeth={quadrant_4?.impacted_teeth || []}
              onToothClick={handleToothClick}
              activeTool={activeTool}
            />
            <div className="text-xs text-gray-400 mt-1">{QUADRANT_LABELS[4]}</div>
          </div>
          <div className="w-px bg-gray-300"></div>
          <div>
            <QuadrantRow
              quadrant={3}
              missingTeeth={quadrant_3?.missing_teeth || []}
              presentTeeth={quadrant_3?.present_teeth || []}
              impactedTeeth={quadrant_3?.impacted_teeth || []}
              onToothClick={handleToothClick}
              activeTool={activeTool}
            />
            <div className="text-xs text-gray-400 mt-1">{QUADRANT_LABELS[3]}</div>
          </div>
        </div>
        <div className="text-xs text-gray-500 mt-1">LOWER JAW</div>
      </div>

      {/* Instructions */}
      <div className="flex justify-center gap-2 mt-6 text-sm text-gray-500 border-t border-gray-100 pt-4">
        <MousePointer2 className="w-4 h-4" />
        <span>Select a tool from the top right, then click teeth to update.</span>
      </div>
    </div>
  );
}
