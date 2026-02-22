import { WorkoutEntry } from "@prisma/client";

interface WorkoutHistoryProps {
  entries: WorkoutEntry[];
  brandingColor: string;
}

export function WorkoutHistory({ entries, brandingColor }: WorkoutHistoryProps) {
  if (entries.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-sm p-6 text-center text-gray-500">
        <div className="text-3xl mb-2">📊</div>
        <p>No workout history yet. Log your first set!</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Entries</h3>
      <div className="space-y-3">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="flex items-center justify-between p-3 rounded-lg bg-gray-50"
          >
            <div>
              <div className="flex items-center gap-2">
                <span
                  className="font-bold text-white text-sm px-2 py-0.5 rounded"
                  style={{ backgroundColor: brandingColor }}
                >
                  {entry.weight}kg × {entry.reps}
                </span>
              </div>
              {entry.notes && (
                <p className="text-xs text-gray-500 mt-1">{entry.notes}</p>
              )}
            </div>
            <div className="text-xs text-gray-400 text-right">
              {new Date(entry.createdAt).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
