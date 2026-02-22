"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";

interface MachineItem {
  id: string;
  name: string;
  machineNumber: string;
  qrCodeUrl: string | null;
  entryCount: number;
}

interface MachineListProps {
  machines: MachineItem[];
  gymSlug: string;
  brandingColor: string;
}

export function MachineList({ machines: initialMachines, gymSlug, brandingColor }: MachineListProps) {
  const router = useRouter();
  const machines = initialMachines;
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({ name: "", machineNumber: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openCreate = () => {
    setEditingId(null);
    setFormData({ name: "", machineNumber: "" });
    setError(null);
    setShowForm(true);
  };

  const openEdit = (machine: MachineItem) => {
    setEditingId(machine.id);
    setFormData({ name: machine.name, machineNumber: machine.machineNumber });
    setError(null);
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const url = editingId ? `/api/machines/${editingId}` : "/api/machines";
      const method = editingId ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json() as { error?: string };
        throw new Error(data.error ?? "Request failed");
      }

      setShowForm(false);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (machineId: string) => {
    if (!confirm("Are you sure you want to delete this machine? All workout entries will be lost.")) {
      return;
    }

    try {
      const response = await fetch(`/api/machines/${machineId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const data = await response.json() as { error?: string };
        throw new Error(data.error ?? "Delete failed");
      }

      router.refresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete machine");
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Machines</h2>
        <button
          onClick={openCreate}
          className="text-white text-sm font-medium px-4 py-2 rounded-lg transition-opacity hover:opacity-90"
          style={{ backgroundColor: brandingColor }}
        >
          + Add Machine
        </button>
      </div>

      {/* Create/Edit Form */}
      {showForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            {editingId ? "Edit Machine" : "New Machine"}
          </h3>
          {error && (
            <p className="text-red-600 text-sm mb-3">{error}</p>
          )}
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Machine Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g. Bench Press"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2"
                  style={{ "--tw-ring-color": brandingColor } as React.CSSProperties}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Machine Number
                </label>
                <input
                  type="text"
                  required
                  value={formData.machineNumber}
                  onChange={(e) => setFormData((prev) => ({ ...prev, machineNumber: e.target.value }))}
                  placeholder="e.g. A1"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2"
                  style={{ "--tw-ring-color": brandingColor } as React.CSSProperties}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50"
                style={{ backgroundColor: brandingColor }}
              >
                {loading ? "Saving..." : editingId ? "Update" : "Create"}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="text-gray-600 text-sm font-medium px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Machine list */}
      {machines.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-3xl mb-2">🏋️</div>
          <p>No machines yet. Add your first machine!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {machines.map((machine) => (
            <div
              key={machine.id}
              className="flex items-center gap-4 p-4 rounded-xl border border-gray-100 hover:border-gray-200 transition-colors"
            >
              {/* QR Code thumbnail */}
              {machine.qrCodeUrl ? (
                <div className="w-12 h-12 relative flex-shrink-0">
                  <Image
                    src={machine.qrCodeUrl}
                    alt={`QR for ${machine.name}`}
                    fill
                    className="object-contain"
                  />
                </div>
              ) : (
                <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-gray-400 text-xs">QR</span>
                </div>
              )}

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900 truncate">{machine.name}</span>
                  <span
                    className="text-white text-xs px-2 py-0.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: brandingColor }}
                  >
                    #{machine.machineNumber}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">{machine.entryCount} entries</p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <Link
                  href={`/g/${gymSlug}/machine/${machine.id}`}
                  target="_blank"
                  className="text-xs text-indigo-600 hover:underline"
                >
                  View
                </Link>
                {machine.qrCodeUrl && (
                  <a
                    href={machine.qrCodeUrl}
                    download={`qr-${machine.machineNumber}.png`}
                    className="text-xs text-green-600 hover:underline"
                  >
                    DL QR
                  </a>
                )}
                <button
                  onClick={() => openEdit(machine)}
                  className="text-xs text-gray-600 hover:text-gray-900"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(machine.id)}
                  className="text-xs text-red-500 hover:text-red-700"
                >
                  Del
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
