import { useState } from 'react';
import axios from 'axios';
import { Loader2, Stethoscope, Sparkles } from 'lucide-react';
import ImageUpload from './components/ImageUpload';
import DentalChart from './components/DentalChart';
import ModelResultCard from './components/ModelResultCard';
import DecisionCard from './components/DecisionCard';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!selectedImage) return;

    setIsAnalyzing(true);
    setError(null);
    setResult(null);
    setCurrentAnalysis(null);

    const formData = new FormData();
    formData.append('image', selectedImage);

    try {
      const response = await axios.post('/api/analyze', formData, {
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

      // Remove from all lists first
      const lists = ['present_teeth', 'missing_teeth', 'impacted_teeth', 'not_visualized_teeth'];
      lists.forEach(listKey => {
        if (!quadData[listKey]) quadData[listKey] = [];
        const index = quadData[listKey].indexOf(toothNumber);
        if (index > -1) {
          quadData[listKey].splice(index, 1);
        }
      });

      // Add to the target list
      // status can be 'present', 'missing', 'impacted', 'unknown' (not_visualized)
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Stethoscope className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">Dental OPG Analyzer</h1>
              <p className="text-sm text-gray-500">Forensic Odontology & Oral Radiology Suite</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Upload Section */}
        <section className="mb-8">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-indigo-500" />
              <h2 className="text-lg font-semibold text-gray-800">Upload OPG Image</h2>
            </div>

            <ImageUpload
              onImageSelect={setSelectedImage}
              disabled={isAnalyzing}
            />

            <div className="mt-6 flex gap-3">
              <button
                onClick={handleAnalyze}
                disabled={!selectedImage || isAnalyzing}
                className="flex-1 py-3 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating Report...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Analyze Radiograph
                  </>
                )}
              </button>

              {(result || selectedImage) && !isAnalyzing && (
                <button
                  onClick={handleReset}
                  className="py-3 px-6 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-xl transition-all"
                >
                  Reset
                </button>
              )}
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
                {error}
              </div>
            )}
          </div>
        </section>

        {/* Results Section */}
        {result && (
          <div className="space-y-8 animate-in fade-in duration-500">
            {/* Final Decision */}
            <section>
              <DecisionCard
                decision={result.final_decision}
                currentAnalysis={currentAnalysis}
                onAnalysisUpdate={setCurrentAnalysis}
              />
            </section>

            {/* Dental Chart */}
            <section>
              <DentalChart
                analysis={currentAnalysis || result.final_decision.final_analysis}
                onToothUpdate={handleToothUpdate}
              />
            </section>
          </div>
        )}

        {/* How it works section */}
        {!result && (
          <section className="mt-8">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Process Workflow</h2>
              <div className="grid md:grid-cols-4 gap-4">
                {[
                  { step: 1, title: 'Upload', desc: 'Securely upload the dental OPG X-ray' },
                  { step: 2, title: 'Analysis', desc: 'Advanced algorithms scan for dental structures' },
                  { step: 3, title: 'Verification', desc: 'Cross-verification against forensic standards' },
                  { step: 4, title: 'Report', desc: 'Generate comprehensive radiographic report' },
                ].map((item) => (
                  <div key={item.step} className="text-center p-4">
                    <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-600 font-bold flex items-center justify-center mx-auto mb-2">
                      {item.step}
                    </div>
                    <h3 className="font-semibold text-gray-800">{item.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-gray-500">
          <p>© {new Date().getFullYear()} Forensic Odontology & Oral Radiology Suite. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
