import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { redirect } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { QRScanner } from "@/components/QRScanner";
import { NavDrawer } from "@/components/NavDrawer";

export default async function HomePage() {
  const session = await getServerSession(authOptions);

  // Admins go straight to their dashboard
  if (session?.user?.role === "GYM_ADMIN" || session?.user?.role === "SUPER_ADMIN") {
    redirect("/dashboard");
  }

  // Authenticated regular users — show the personalised welcome + QR scanner
  if (session?.user) {
    // Fetch their gym for branding (if they belong to one)
    const gym = session.user.gymId
      ? await prisma.gym.findUnique({
          where: { id: session.user.gymId },
          select: {
            name: true,
            logoUrl: true,
            brandingColor: true,
          },
        })
      : null;

    const brandingColor = gym?.brandingColor ?? "#6366f1";
    const displayName = session.user.name ?? session.user.email ?? "there";

    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        {/* Branded header */}
        <header
          className="text-white py-4 px-4 shadow-lg flex-shrink-0"
          style={{ backgroundColor: brandingColor }}
        >
          <div className="max-w-lg mx-auto flex items-center justify-between gap-3">
            {/* Gym logo + name */}
            <div className="flex items-center gap-3 min-w-0">
              {gym?.logoUrl && (
                <div className="w-10 h-10 relative rounded-full overflow-hidden bg-white/20 flex-shrink-0">
                  <Image
                    src={gym.logoUrl}
                    alt={`${gym.name} logo`}
                    fill
                    className="object-contain"
                    sizes="40px"
                  />
                </div>
              )}
              <div className="min-w-0">
                {gym && (
                  <p className="text-white/80 text-xs truncate">{gym.name}</p>
                )}
                <h1 className="text-base font-bold leading-tight truncate">
                  Welcome back, {displayName}!
                </h1>
              </div>
            </div>

            {/* Hamburger menu */}
            <NavDrawer
              role={session.user.role}
              brandingColor={brandingColor}
            />
          </div>
        </header>

        {/* Main content: QR scanner */}
        <main className="flex-1 flex flex-col items-center justify-center px-4 py-8 gap-6">
          <div className="w-full max-w-sm">
            <h2 className="text-gray-700 font-semibold text-center mb-4">
              Scan a machine QR code
            </h2>
            <QRScanner brandingColor={brandingColor} />
          </div>
        </main>
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
