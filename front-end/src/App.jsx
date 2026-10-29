import { useCallback, useEffect, useState } from "react";
import Header from "./components/Header";
import ActionButtons from "./components/ActionButtons";
import LoadingScanner from "./components/LoadingScanner";
import ResultCard from "./components/ResultCard";
import ServerFooter from "./components/ServerFooter";
import { getModelInfo, simulateTraffic } from "./api";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [isWakingUp, setIsWakingUp] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [serverStatus, setServerStatus] = useState("connecting"); // connecting | online | offline

  // Ping the backend on page load: it also wakes up a sleeping free-tier server
  useEffect(() => {
    let cancelled = false;
    getModelInfo()
      .then((info) => {
        if (cancelled) return;
        setModelInfo(info);
        setServerStatus("online");
      })
      .catch(() => {
        if (!cancelled) setServerStatus("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleTest = useCallback(async (kind) => {
    setLoading(true);
    setError(null);
    setResult(null);

    // If there is no answer after 4s, the backend is most likely waking up
    const wakeUpTimer = setTimeout(() => setIsWakingUp(true), 4000);

    try {
      const data = await simulateTraffic(kind);
      setResult(data);
      setServerStatus("online");
    } catch (err) {
      console.error(err);
      setServerStatus("offline");
      setError(
        err.response?.data?.detail ||
          "Cannot reach the backend. Make sure the API is running and try again."
      );
    } finally {
      clearTimeout(wakeUpTimer);
      setLoading(false);
      setIsWakingUp(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4 sm:p-6">
      <div className="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-500" />

        <Header />
        <ActionButtons onTest={handleTest} loading={loading} />

        {loading && <LoadingScanner isWakingUp={isWakingUp} inputDim={modelInfo?.input_dim} />}

        {error && !loading && (
          <div
            role="alert"
            className="p-4 rounded-xl border border-amber-800 bg-amber-950/30 text-amber-300 text-sm"
          >
            {error}
          </div>
        )}

        {!loading && <ResultCard result={result} />}

        <ServerFooter status={serverStatus} info={modelInfo} />
      </div>
    </div>
  );
}