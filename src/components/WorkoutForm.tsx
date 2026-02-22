"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface WorkoutFormProps {
  machineId: string;
  brandingColor: string;
}

export function WorkoutForm({ machineId, brandingColor }: WorkoutFormProps) {
  const router = useRouter();
  const [weight, setWeight] = useState("");
  const [reps, setReps] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    // Validate
    const weightNum = parseFloat(weight);
    const repsNum = parseInt(reps, 10);

    if (isNaN(weightNum) || weightNum <= 0) {
      setError("Please enter a valid weight.");
      return;
    }
    if (isNaN(repsNum) || repsNum <= 0) {
      setError("Please enter a valid number of reps.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/workout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          machineId,
          weight: weightNum,
          reps: repsNum,
          notes: notes.trim() || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json() as { error?: string };
        throw new Error(data.error ?? "Failed to save workout entry.");
      }

      // Reset form
      setWeight("");
      setReps("");
      setNotes("");
      setSuccess(true);

      // Refresh server data
      router.refresh();

      // Hide success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Log Workout</h3>

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
          ✅ Workout logged successfully!
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Weight (kg)
            </label>
            <input
              type="number"
              step="0.5"
              min="0"
              required
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              placeholder="e.g. 80"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reps
            </label>
            <input
              type="number"
              min="1"
              required
              value={reps}
              onChange={(e) => setReps(e.target.value)}
              placeholder="e.g. 10"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notes (optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Felt strong today!"
            rows={2}
            maxLength={500}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent resize-none"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 text-white font-semibold rounded-lg transition-opacity disabled:opacity-50"
          style={{ backgroundColor: brandingColor }}
        >
          {loading ? "Saving..." : "Log Workout"}
        </button>
      </form>
    </div>
  );
}
