import { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, Stethoscope, Sparkles, Award } from 'lucide-react';
import ImageUpload from './components/ImageUpload';
import DentalChart from './components/DentalChart';
import ModelResultCard from './components/ModelResultCard';
import DecisionCard from './components/DecisionCard';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [error, setError] = useState(null);

  // Handle image selection and preview generation
  const handleImageSelect = (file) => {
    setSelectedImage(file);
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
    // Convert logic to reset analysis when image changes
    if (result) {
      setResult(null);
      setCurrentAnalysis(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedImage) return;

    setIsAnalyzing(true);
    setError(null);
    setResult(null);
    setCurrentAnalysis(null);

    const formData = new FormData();
    formData.append('image', selectedImage);

    const apiUrl = import.meta.env.VITE_API_URL || '';
    try {
      const response = await axios.post(`${apiUrl}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(response.data);
      setCurrentAnalysis(response.data.final_decision.final_analysis);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze image. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setSelectedImage(null);
    setPreviewUrl(null);
    setResult(null);
    setCurrentAnalysis(null);
    setError(null);
  };

  const handleToothUpdate = (quadrant, toothNumber, status) => {
    if (!currentAnalysis) return;

    setCurrentAnalysis(prev => {
      const newAnalysis = JSON.parse(JSON.stringify(prev));
      const quadKey = `quadrant_${quadrant}`;
      const quadData = newAnalysis[quadKey];

      const lists = ['present_teeth', 'missing_teeth', 'impacted_teeth', 'not_visualized_teeth'];
      lists.forEach(listKey => {
        if (!quadData[listKey]) quadData[listKey] = [];
        const index = quadData[listKey].indexOf(toothNumber);
        if (index > -1) {
          quadData[listKey].splice(index, 1);
        }
      });

      let targetList = '';
      if (status === 'present') targetList = 'present_teeth';
      else if (status === 'missing') targetList = 'missing_teeth';
      else if (status === 'impacted') targetList = 'impacted_teeth';
      else if (status === 'unknown') targetList = 'not_visualized_teeth';

      if (targetList) {
        quadData[targetList].push(toothNumber);
        quadData[targetList].sort((a, b) => a - b);
      }

      return newAnalysis;
    });
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans text-gray-900">

      {/* LEFT PANEL - 45% Width (Controls + Report) */}
      <div className="w-[45%] flex flex-col h-full bg-white border-r border-gray-200 shadow-2xl z-20">

        {/* 1. Header (Compact) */}
        <header className="px-6 py-4 border-b border-gray-100 bg-white flex items-center gap-3 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center shadow-md">
            <Stethoscope className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900 tracking-tight leading-none">Dental OPG Analyzer</h1>
            <p className="text-[10px] font-medium text-gray-500 uppercase tracking-wide">Forensic Suite</p>
          </div>
        </header>

        {/* 2. Upload & Controls (Fixed Top) */}
        <div className="px-6 py-4 shrink-0 bg-gray-50/50 border-b border-gray-100">
          <div className="flex gap-4 items-start">
            <div className="flex-1">
              <ImageUpload
                onImageSelect={handleImageSelect}
                disabled={isAnalyzing}
                showPreview={false}
              />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-2 w-48">
              <button
                onClick={handleAnalyze}
                disabled={!selectedImage || isAnalyzing}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold rounded-lg shadow-md shadow-indigo-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 text-sm"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Analyze</span>
                  </>
                )}
              </button>

              {((result || selectedImage) && !isAnalyzing) && (
                <button
                  onClick={handleReset}
                  className="w-full py-2.5 px-4 bg-white border border-gray-200 hover:bg-gray-50 text-gray-600 font-semibold rounded-lg transition-all shadow-sm text-sm"
                >
                  Reset
                </button>
              )}
            </div>
          </div>

          {error && (
            <div className="mt-3 p-2 bg-red-50 border border-red-100 rounded-md text-xs text-red-600 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 block"></span>
              {error}
            </div>
          )}
        </div>

        {/* 3. Report Area (Full Remaining Height) */}
        <div className="flex-1 min-h-0 p-6 bg-gray-50/30 overflow-y-auto custom-scrollbar">
          {result ? (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <DecisionCard
                decision={result.final_decision}
                currentAnalysis={currentAnalysis}
                onAnalysisUpdate={setCurrentAnalysis}
              />
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 border-2 border-dashed border-gray-200 rounded-xl bg-gray-50/50">
              {!selectedImage && (
                <div className="text-center space-y-3">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-50 text-indigo-300">
                    <Stethoscope className="w-6 h-6" />
                  </div>
                  <h3 className="text-gray-900 font-medium">Waiting for Analysis</h3>
                  <p className="text-sm max-w-xs mx-auto">Upload an X-ray to see the comprehensive forensic report here.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-gray-200 text-center bg-white">
          <p className="text-[10px] text-gray-400">© 2026 Forensic Odontology Suite</p>
        </div>
      </div>

      {/* RIGHT PANEL - 55% Width (Visuals) */}
      <div className="w-[55%] bg-gray-900 flex flex-col h-full border-l border-gray-800">

        {/* Top Half: Image View */}
        <div className="h-1/2 relative bg-black flex items-center justify-center overflow-hidden border-b border-gray-800 p-4">
          {previewUrl ? (
            <div className="relative w-full h-full flex items-center justify-center">
              <img
                src={previewUrl}
                alt="Radiograph Analysis"
                className="max-w-full max-h-full object-contain drop-shadow-2xl"
              />
              <div className="absolute top-0 right-0 m-2">
                <span className="bg-black/60 backdrop-blur-md text-white/80 text-[10px] px-2 py-1 rounded-md border border-white/10 uppercase tracking-wider">
                  Native View
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-600">
              <div className="w-16 h-16 bg-gray-800/50 rounded-2xl flex items-center justify-center mx-auto mb-3 border border-gray-700">
                <Sparkles className="w-6 h-6" />
              </div>
              <p className="text-sm">Radiograph View</p>
            </div>
          )}
        </div>

        {/* Bottom Half: Dental Chart */}
        <div className="h-1/2 bg-gray-100 flex flex-col overflow-hidden relative">
          <div className="absolute top-0 left-0 right-0 p-2 bg-white/50 backdrop-blur border-b border-gray-200 z-10 flex items-center justify-between px-4">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
              Dental Chart
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-4 pt-10 custom-scrollbar">
            {result ? (
              <DentalChart
                analysis={currentAnalysis || result.final_decision.final_analysis}
                onToothUpdate={handleToothUpdate}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400 text-sm">
                Chart will appear here after analysis.
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  );
}

export default App;
