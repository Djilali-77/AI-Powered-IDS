const STATUS_STYLES = {
  online: { dot: "bg-emerald-500", text: "API online" },
  connecting: { dot: "bg-amber-400 animate-pulse", text: "Connecting to API..." },
  offline: { dot: "bg-rose-500", text: "API offline" },
};

export default function ServerFooter({ status, info }) {
  const style = STATUS_STYLES[status];
  const auc = info?.metrics?.roc_auc;

  return (
    <div className="mt-6 pt-4 border-t border-slate-800 flex flex-col sm:flex-row gap-2 sm:justify-between text-xs text-slate-500">
      <span className="flex items-center gap-2">
        <span className={`inline-block w-2 h-2 rounded-full ${style.dot}`} />
        {style.text}
      </span>
      {info && (
        <span className="font-mono">
          {info.input_dim} features
          {auc !== undefined && ` · ROC AUC ${auc.toFixed(3)}`}
        </span>
      )}
    </div>
  );
}