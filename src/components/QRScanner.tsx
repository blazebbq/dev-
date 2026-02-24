"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

// Lazy-loaded so Next.js SSR doesn't touch the browser-only html5-qrcode module.
// The import() resolves to { Html5Qrcode } once we're on the client.

interface QRScannerProps {
  brandingColor: string;
}

/** Matches the machine QR URL pattern: /g/{gymSlug}/machine/{machineId} */
function parseMachineUrl(text: string): string | null {
  try {
    // Accept both absolute URLs (as encoded in QR) and relative paths
    const url = new URL(text, window.location.origin);
    const match = url.pathname.match(/^\/g\/[^/]+\/machine\/[^/]+$/);
    if (match) return url.pathname;
  } catch {
    // text wasn't a URL
  }
  return null;
}

export function QRScanner({ brandingColor }: QRScannerProps) {
  const router = useRouter();
  const scannerRef = useRef<{ stop: () => Promise<void> } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<"idle" | "scanning" | "error" | "success">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [scannedPath, setScannedPath] = useState("");

  useEffect(() => {
    let html5QrCode: { stop: () => Promise<void> } | null = null;
    let stopped = false;

    async function startScanner() {
      try {
        const { Html5Qrcode } = await import("html5-qrcode");

        if (stopped || !containerRef.current) return;

        const qr = new Html5Qrcode("qr-scanner-container");
        html5QrCode = qr;
        scannerRef.current = qr;

        const config = {
          fps: 10,
          qrbox: { width: 240, height: 240 },
          aspectRatio: 1.0,
        };

        await qr.start(
          { facingMode: "environment" },
          config,
          (decodedText: string) => {
            const path = parseMachineUrl(decodedText);
            if (path) {
              setScannedPath(path);
              setStatus("success");
              // Stop scanner then navigate
              qr.stop().finally(() => {
                if (!stopped) router.push(path);
              });
            }
            // Non-machine QR codes are silently ignored — keep scanning
          },
          // QR not found frame callback — intentionally ignored
          undefined
        );

        setStatus("scanning");
      } catch (err) {
        if (!stopped) {
          const msg =
            err instanceof Error ? err.message : "Camera access failed";
          setErrorMsg(msg);
          setStatus("error");
        }
      }
    }

    startScanner();

    return () => {
      stopped = true;
      if (html5QrCode) {
        html5QrCode.stop().catch((err: unknown) => {
          // Stopping on unmount can fail if the camera was never started; log
          // at debug level so it's visible in dev without polluting production.
          console.debug("[QRScanner] stop on unmount:", err);
        });
      }
    };
  }, [router]);

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Camera viewfinder */}
      <div className="relative w-full max-w-sm rounded-2xl overflow-hidden shadow-lg bg-black">
        {/* The html5-qrcode library injects the video element here */}
        <div
          id="qr-scanner-container"
          ref={containerRef}
          className="w-full"
          style={{ minHeight: 280 }}
        />

        {/* Scanning overlay — corner brackets */}
        {status === "scanning" && (
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
            <div className="relative w-48 h-48">
              {/* Top-left */}
              <span
                className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 rounded-tl-lg"
                style={{ borderColor: brandingColor }}
              />
              {/* Top-right */}
              <span
                className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 rounded-tr-lg"
                style={{ borderColor: brandingColor }}
              />
              {/* Bottom-left */}
              <span
                className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 rounded-bl-lg"
                style={{ borderColor: brandingColor }}
              />
              {/* Bottom-right */}
              <span
                className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 rounded-br-lg"
                style={{ borderColor: brandingColor }}
              />
            </div>
          </div>
        )}

        {/* Success overlay */}
        {status === "success" && (
          <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2">
            <div className="text-4xl">✅</div>
            <p className="text-white text-sm font-medium">QR code detected!</p>
            <p className="text-white/70 text-xs">Redirecting…</p>
          </div>
        )}

        {/* Loading placeholder (before camera starts) */}
        {status === "idle" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-gray-900">
            <div
              className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
              style={{ borderColor: brandingColor }}
            />
            <p className="text-white/70 text-xs">Starting camera…</p>
          </div>
        )}
      </div>

      {/* Error state */}
      {status === "error" && (
        <div className="w-full max-w-sm bg-red-50 border border-red-200 rounded-2xl p-4 text-center">
          <div className="text-2xl mb-2">📷</div>
          <p className="text-red-700 text-sm font-medium">Camera unavailable</p>
          <p className="text-red-500 text-xs mt-1">{errorMsg}</p>
          <p className="text-gray-500 text-xs mt-3">
            Please allow camera access in your browser settings, then reload the
            page.
          </p>
        </div>
      )}

      {/* Instruction */}
      {status === "scanning" && (
        <p className="text-gray-500 text-sm text-center">
          Point your camera at a machine&apos;s QR code to begin
        </p>
      )}

      {/* Debug: manual URL entry for environments without a camera */}
      {scannedPath && (
        <p className="text-xs text-gray-400">Detected: {scannedPath}</p>
      )}
    </div>
  );
}
