export function AdBanner() {
  return (
    <div className="rounded-2xl border border-dashed border-yellow-300 bg-yellow-50 p-4 text-center">
      <p className="text-xs text-yellow-600 font-medium uppercase tracking-wide mb-1">
        Advertisement
      </p>
      <div className="h-16 flex items-center justify-center bg-yellow-100 rounded-lg">
        <p className="text-yellow-700 text-sm">
          🏋️ Upgrade to PRO to remove ads &amp; unlock advanced analytics
        </p>
      </div>
      <p className="text-xs text-yellow-500 mt-2">
        This ad is shown because you are on the FREE plan.
      </p>
    </div>
  );
}
