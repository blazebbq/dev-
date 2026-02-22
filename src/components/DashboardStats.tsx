interface DashboardStatsProps {
  totalScans: number;
  activeUsers: number;
  mostUsedMachine: string | null;
  planType: string;
}

export function DashboardStats({
  totalScans,
  activeUsers,
  mostUsedMachine,
  planType,
}: DashboardStatsProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Overview</h2>
        <span
          className={`text-xs font-bold px-2 py-1 rounded-full ${
            planType === "PRO"
              ? "bg-yellow-100 text-yellow-700"
              : "bg-gray-100 text-gray-600"
          }`}
        >
          {planType} Plan
        </span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-indigo-50 rounded-xl">
          <div className="text-2xl font-bold text-indigo-600">{totalScans}</div>
          <div className="text-xs text-gray-500 mt-1">Total Scans</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-xl">
          <div className="text-2xl font-bold text-green-600">{activeUsers}</div>
          <div className="text-xs text-gray-500 mt-1">Active Users</div>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-xl">
          <div className="text-sm font-bold text-purple-600 truncate">
            {mostUsedMachine ?? "—"}
          </div>
          <div className="text-xs text-gray-500 mt-1">Top Machine</div>
        </div>
      </div>
    </div>
  );
}
