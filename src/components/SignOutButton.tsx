"use client";

import { signOut } from "next-auth/react";

export function SignOutButton() {
  return (
    <button
      onClick={() => signOut({ callbackUrl: "/auth/signin" })}
      className="text-white/80 hover:text-white text-sm font-medium transition-colors"
    >
      Sign Out
    </button>
  );
}
