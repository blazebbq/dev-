import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { redirect } from "next/navigation";
import Link from "next/link";
import { SignOutButton } from "@/components/SignOutButton";

export default async function HomePage() {
  const session = await getServerSession(authOptions);

  // Admins go straight to their dashboard
  if (session?.user?.role === "GYM_ADMIN" || session?.user?.role === "SUPER_ADMIN") {
    redirect("/dashboard");
  }

  // Authenticated regular users — show a personalised landing page
  if (session?.user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex flex-col items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <div className="text-6xl mb-6">🏋️</div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">GymTrackQR</h1>
          <p className="text-gray-500 mb-8 text-sm">
            Signed in as <strong>{session.user.email}</strong>
          </p>

          <div className="space-y-4">
            <div className="bg-white rounded-2xl shadow-sm p-6 text-left">
              <h2 className="font-semibold text-gray-900 mb-3">Ready to track</h2>
              <p className="text-gray-600 text-sm">
                Scan a QR code on any gym machine to log your workout. Your
                progress will be saved automatically.
              </p>
            </div>

            <div className="bg-white rounded-2xl shadow-sm p-4">
              <ol className="space-y-2 text-gray-600 text-sm text-left">
                <li className="flex gap-2">
                  <span className="text-indigo-600 font-bold">1.</span>
                  Open your gym&apos;s app on your phone
                </li>
                <li className="flex gap-2">
                  <span className="text-indigo-600 font-bold">2.</span>
                  Scan the QR code on a machine
                </li>
                <li className="flex gap-2">
                  <span className="text-indigo-600 font-bold">3.</span>
                  Log weight, reps, and notes
                </li>
              </ol>
            </div>

            <div className="pt-2">
              <SignOutButton variant="subtle" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Unauthenticated — show the marketing landing page
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex flex-col items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="text-6xl mb-6">🏋️</div>
        <h1 className="text-4xl font-bold text-gray-900 mb-3">GymTrackQR</h1>
        <p className="text-lg text-gray-600 mb-8">
          Scan a QR code on any gym machine to start tracking your workouts
        </p>

        <div className="space-y-4">
          <div className="bg-white rounded-2xl shadow-sm p-6 text-left">
            <h2 className="font-semibold text-gray-900 mb-3">How it works</h2>
            <ol className="space-y-2 text-gray-600 text-sm">
              <li className="flex gap-2">
                <span className="text-indigo-600 font-bold">1.</span>
                Scan QR code on a gym machine
              </li>
              <li className="flex gap-2">
                <span className="text-indigo-600 font-bold">2.</span>
                Sign in with your email or Google
              </li>
              <li className="flex gap-2">
                <span className="text-indigo-600 font-bold">3.</span>
                Log your weight, reps, and notes
              </li>
              <li className="flex gap-2">
                <span className="text-indigo-600 font-bold">4.</span>
                Track your progress over time
              </li>
            </ol>
          </div>

          <Link
            href="/auth/signin"
            className="block w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors text-center"
          >
            Get Started
          </Link>
        </div>
      </div>
    </div>
  );
}
