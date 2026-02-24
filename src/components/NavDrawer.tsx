"use client";

import { useState, useRef, useEffect } from "react";
import { signOut } from "next-auth/react";
import Link from "next/link";

interface NavDrawerProps {
  role: string;
  brandingColor: string;
}

const menuItems = [
  { label: "Account Settings", href: "/account", icon: "⚙️" },
  { label: "My Stats", href: "/stats", icon: "📊" },
];

const adminItems = [
  { label: "Admin Dashboard", href: "/dashboard", icon: "🏠" },
];

export function NavDrawer({ role, brandingColor }: NavDrawerProps) {
  const [open, setOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);

  const isAdmin = role === "GYM_ADMIN" || role === "SUPER_ADMIN";

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

  return (
    <div className="relative" ref={drawerRef}>
      {/* Hamburger button */}
      <button
        aria-label="Open menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex flex-col justify-center items-center gap-1.5 w-10 h-10 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
      >
        <span className="w-5 h-0.5 bg-white rounded-full" />
        <span className="w-5 h-0.5 bg-white rounded-full" />
        <span className="w-5 h-0.5 bg-white rounded-full" />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-12 w-52 bg-white rounded-2xl shadow-xl border border-gray-100 py-2 z-50 overflow-hidden">
          {/* Navigation links */}
          {menuItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          ))}

          {/* Admin-only items */}
          {isAdmin &&
            adminItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 px-4 py-3 text-sm hover:bg-gray-50 transition-colors"
                style={{ color: brandingColor }}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            ))}

          <div className="border-t border-gray-100 mt-1 pt-1">
            <button
              onClick={() => {
                setOpen(false);
                signOut({ callbackUrl: "/auth/signin" });
              }}
              className="flex items-center gap-3 w-full px-4 py-3 text-sm text-red-500 hover:bg-red-50 transition-colors"
            >
              <span>🚪</span>
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
