export default function ActionButtons({ onTest, loading }) {
  return (
    <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-6 sm:mb-8">
      <button
        onClick={() => onTest(false)}
        disabled={loading}
        className="w-full sm:flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 sm:py-4 px-6 rounded-xl transition-all shadow-lg shadow-emerald-900/20 cursor-pointer disabled:opacity-50 text-sm sm:text-base"
      >
        {loading ? "Analyse..." : "Tester Trafic Normal (BENIGN)"}
      </button>
      
      <button
        onClick={() => onTest(true)}
        disabled={loading}
        className="w-full sm:flex-1 bg-rose-600 hover:bg-rose-500 text-white font-semibold py-3 sm:py-4 px-6 rounded-xl transition-all shadow-lg shadow-rose-900/20 cursor-pointer disabled:opacity-50 text-sm sm:text-base"
      >
        {loading ? "Analyse..." : "Simuler une Attaque 🚨"}
      </button>
    </div>
  );
}