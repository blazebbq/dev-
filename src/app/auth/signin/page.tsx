"use client";

import { signIn, getProviders } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { useState, useEffect, Suspense } from "react";

const KNOWN_ERRORS = [
  "OAuthSignin","OAuthCallback","OAuthCreateAccount","EmailCreateAccount",
  "Callback","OAuthAccountNotLinked","EmailSignin","CredentialsSignin","SessionRequired",
];

interface Provider {
  id: string;
  name: string;
  type: string;
  signinUrl: string;
  callbackUrl: string;
}

// devBypassEmail is injected server-side so the value never leaks into the
// client bundle as a raw process.env reference.
function SignInContent({ devBypassEmail }: { devBypassEmail: string | null }) {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/dashboard";
  const error = searchParams.get("error");

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingLabel, setLoadingLabel] = useState("Sending...");
  const [emailSent, setEmailSent] = useState(false);
  const [providers, setProviders] = useState<Record<string, Provider> | null>(null);

  useEffect(() => {
    getProviders().then(setProviders);
  }, []);

  const handleEmailSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Dev bypass: if the email matches DEV_BYPASS_EMAIL, skip the real magic-link
      // flow and sign in instantly via the server-side bypass route.
      if (
        devBypassEmail &&
        email.trim().toLowerCase() === devBypassEmail.trim().toLowerCase()
      ) {
        setLoadingLabel("Signing in...");
        const res = await fetch("/api/auth/dev-bypass", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, callbackUrl }),
        });
        if (res.ok) {
          const data = (await res.json()) as { url?: string };
          window.location.href = data.url ?? callbackUrl;
          return;
        }
      }

      // Normal magic-link flow
      setLoadingLabel("Sending...");
      const result = await signIn("email", {
        email,
        callbackUrl,
        redirect: false,
      });
      if (result?.ok) {
        setEmailSent(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    signIn("google", { callbackUrl });
  };

  const handleGuestContinue = () => {
    // Only follow callbackUrl if it's a guest-accessible machine page (/g/…).
    // Any other destination (e.g. /dashboard) is auth-protected and will trigger
    // a NextAuth "Configuration" error for unauthenticated users.
    const guestUrl = callbackUrl.startsWith("/g/") ? callbackUrl : "/";
    window.location.href = guestUrl;
  };

  if (emailSent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="text-5xl mb-4">📧</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Check your email</h2>
          <p className="text-gray-600">
            A sign-in link has been sent to <strong>{email}</strong>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">🏋️</div>
          <h1 className="text-3xl font-bold text-gray-900">GymTrackQR</h1>
          <p className="text-gray-500 mt-2">Sign in to track your workouts</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error === "OAuthSignin" && "Error signing in with OAuth provider."}
            {error === "OAuthCallback" && "Error during OAuth callback."}
            {error === "OAuthCreateAccount" && "Could not create OAuth account."}
            {error === "EmailCreateAccount" && "Could not create email account."}
            {error === "Callback" && "Error during callback."}
            {error === "OAuthAccountNotLinked" && "Email already used with another provider."}
            {error === "EmailSignin" && "Error sending sign-in email."}
            {error === "CredentialsSignin" && "Invalid credentials."}
            {error === "SessionRequired" && "Please sign in to continue."}
            {!KNOWN_ERRORS.includes(error) && "An error occurred. Please try again."}
          </div>
        )}

        <form onSubmit={handleEmailSignIn} className="space-y-4 mb-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={devBypassEmail ?? "you@example.com"}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            {devBypassEmail && (
              <p className="mt-1.5 text-xs text-amber-600">
                🐛 Use <button
                  type="button"
                  className="font-mono underline"
                  onClick={() => setEmail(devBypassEmail)}
                >
                  {devBypassEmail}
                </button> to sign in instantly (no email needed)
              </p>
            )}
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            {loading ? loadingLabel : "Send Magic Link"}
          </button>
        </form>

        {providers?.google && (
          <>
            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or continue with</span>
              </div>
            </div>

            <button
              onClick={handleGoogleSignIn}
              className="w-full py-3 px-4 border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium rounded-lg transition-colors flex items-center justify-center gap-3"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Sign in with Google
            </button>
          </>
        )}

        {/* Guest browsing is always available */}
        <div className="relative mt-6 mb-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-400">or</span>
          </div>
        </div>
        <button
          onClick={handleGuestContinue}
          className="w-full py-2.5 px-4 border border-dashed border-gray-300 hover:bg-gray-50 text-gray-500 text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <span>👁️</span>
          Continue as Guest
        </button>
        <p className="mt-2 text-center text-xs text-gray-400">
          Browse without logging in — workout logging is disabled
        </p>
      </div>
    </div>
  );
}

// Server component wrapper — reads server-only env vars and passes them as props
// so they never appear as raw process.env references in the client bundle.
export default function SignInPage() {
  const devBypassEmail = process.env.DEV_BYPASS_EMAIL ?? null;
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <SignInContent devBypassEmail={devBypassEmail} />
    </Suspense>
  );
}

