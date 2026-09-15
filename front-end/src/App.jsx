import { useState } from 'react';
import axios from 'axios';
import Header from './components/Header';
import ActionButtons from './components/ActionButtons';
import ResultCard from './components/ResultCard';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleTestTraffic = async (isAttack) => {
    setLoading(true);

    const benignTraffic = new Array(78).fill(0).map((_, i) => {
      return (i % 5 === 0) ? 0.05 : 0.01; 
    });

    const attackTraffic = new Array(78).fill(0).map((_, i) => {
      if (i === 12 || i === 34 || i === 56) return 4.5;
      if (i % 7 === 0) return 2.8;
      return 0.1;
    });

    const payloadFeatures = isAttack ? attackTraffic : benignTraffic;

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      
      const response = await axios.post(`${apiUrl}/predict`, {
        features: payloadFeatures
      });
      setResult(response.data);
    } catch (err) {
      console.error(err);
      alert("Erreur de connexion au backend ! Vérifiez que FastAPI est lancé.");
    } finally {
      setLoading(false);
    }
  };

  return (
    // Changed padding (p-4 instead of p-6) for better mobile display
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4 sm:p-6">
      {/* Changed inner padding (p-5 on mobile, sm:p-8 on desktop) */}
      <div className="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-8 shadow-2xl">
        <Header />
        <ActionButtons onTest={handleTestTraffic} loading={loading} />
        <ResultCard result={result} />
      </div>
    </div>
  );
}