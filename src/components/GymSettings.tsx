"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { HEX_COLOR_REGEX, isValidLogoUrl } from "@/lib/validation";

interface GymSettingsProps {
  gymId: string;
  currentLogoUrl: string | null;
  currentBrandingColor: string;
}

export function GymSettings({
  gymId,
  currentLogoUrl,
  currentBrandingColor,
}: GymSettingsProps) {
  const router = useRouter();
  const [logoUrl, setLogoUrl] = useState(currentLogoUrl ?? "");
  const [brandingColor, setBrandingColor] = useState(currentBrandingColor);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Only render the preview if the URL is a valid HTTPS URL (client-side pre-check)
  const showPreview = logoUrl.trim().length > 0 && isValidLogoUrl(logoUrl.trim());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSaved(false);

    const trimmedLogo = logoUrl.trim() || null;
    if (trimmedLogo && !isValidLogoUrl(trimmedLogo)) {
      setError("Logo URL must be a valid HTTPS URL.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/gym/settings", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gymId,
          logoUrl: trimmedLogo,
          brandingColor,
        }),
      });

      if (!res.ok) {
        const data = (await res.json()) as { error?: string };
        throw new Error(data.error ?? "Failed to save settings");
      }

      setSaved(true);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Gym Settings</h2>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Logo URL */}
        <div>
          <label
            htmlFor="gs-logo"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Logo URL
          </label>
          <input
            id="gs-logo"
            type="url"
            value={logoUrl}
            onChange={(e) => setLogoUrl(e.target.value)}
            placeholder="https://example.com/logo.png"
            className="w-full px-4 py-2.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            A publicly accessible HTTPS image URL (PNG, JPG, SVG). Leave blank
            to remove the logo.
          </p>
          {showPreview && (
            <div className="mt-2 flex items-center gap-3">
              {/* Standard <img> used intentionally for preview — URL is validated as HTTPS above */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={logoUrl}
                alt="Logo preview"
                className="w-12 h-12 object-contain rounded-lg border border-gray-200 bg-gray-50"
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).style.display = "none";
                }}
              />
              <span className="text-xs text-gray-500">Preview</span>
            </div>
          )}
        </div>

        {/* Branding color */}
        <div>
          <label
            htmlFor="gs-color"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Brand Color
          </label>
          <div className="flex items-center gap-3">
            <input
              id="gs-color"
              type="color"
              value={brandingColor}
              onChange={(e) => setBrandingColor(e.target.value)}
              className="w-10 h-10 cursor-pointer rounded-lg border border-gray-300 p-0.5"
            />
            <input
              type="text"
              value={brandingColor}
              onChange={(e) => {
                const v = e.target.value;
                if (HEX_COLOR_REGEX.test(v) || /^#[0-9a-fA-F]{0,5}$/.test(v)) {
                  setBrandingColor(v);
                }
              }}
              maxLength={7}
              className="w-28 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
            />
            <span
              className="text-xs font-medium text-white px-3 py-1.5 rounded-full"
              style={{ backgroundColor: brandingColor }}
            >
              Preview
            </span>
          </div>
        </div>

        {error && (
          <p className="text-red-600 text-sm">{error}</p>
        )}
        {saved && (
          <p className="text-green-600 text-sm">✅ Settings saved!</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-50 transition-opacity hover:opacity-90"
          style={{ backgroundColor: brandingColor }}
        >
          {loading ? "Saving…" : "Save Settings"}
        </button>
      </form>
    </div>
  );
}
