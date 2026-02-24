"use client";

import { signOut } from "next-auth/react";

interface SignOutButtonProps {
  // "default" = white text for dark header backgrounds
  // "subtle"  = gray text for light/white backgrounds
  variant?: "default" | "subtle";
}

export function SignOutButton({ variant = "default" }: SignOutButtonProps) {
  const className =
    variant === "subtle"
      ? "text-gray-500 hover:text-gray-700 text-sm font-medium transition-colors border border-gray-200 rounded-lg px-4 py-2 hover:bg-gray-50"
      : "text-white/80 hover:text-white text-sm font-medium transition-colors";

  return (
    <button
      onClick={() => signOut({ callbackUrl: "/auth/signin" })}
      className={className}
    >
      Sign Out
    </button>
  );
}
