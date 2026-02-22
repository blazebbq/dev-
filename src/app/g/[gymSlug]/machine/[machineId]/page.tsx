import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { redirect, notFound } from "next/navigation";
import { WorkoutForm } from "@/components/WorkoutForm";
import { WorkoutHistory } from "@/components/WorkoutHistory";
import Image from "next/image";

interface PageProps {
  params: Promise<{
    gymSlug: string;
    machineId: string;
  }>;
}

export default async function MachinePage({ params }: PageProps) {
  const { gymSlug, machineId } = await params;
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    const callbackUrl = `/g/${gymSlug}/machine/${machineId}`;
    redirect(`/auth/signin?callbackUrl=${encodeURIComponent(callbackUrl)}`);
  }

  // Fetch gym by slug
  const gym = await prisma.gym.findUnique({
    where: { slug: gymSlug },
  });

  if (!gym) {
    notFound();
  }

  // Fetch machine by ID, verify it belongs to this gym
  const machine = await prisma.machine.findFirst({
    where: {
      id: machineId,
      gymId: gym.id,
    },
  });

  if (!machine) {
    notFound();
  }

  // Fetch last 5 entries for logged-in user on this machine
  const recentEntries = await prisma.workoutEntry.findMany({
    where: {
      userId: session.user.id,
      machineId: machine.id,
    },
    orderBy: { createdAt: "desc" },
    take: 5,
  });

  return (
    <div
      className="min-h-screen bg-gray-50"
      style={{ "--brand-color": gym.brandingColor } as React.CSSProperties}
    >
      {/* Header with branding */}
      <header
        className="text-white py-6 px-4 shadow-lg"
        style={{ backgroundColor: gym.brandingColor }}
      >
        <div className="max-w-lg mx-auto flex items-center gap-4">
          {gym.logoUrl && (
            <div className="w-12 h-12 relative rounded-full overflow-hidden bg-white/20 flex-shrink-0">
              <Image
                src={gym.logoUrl}
                alt={`${gym.name} logo`}
                fill
                className="object-contain"
              />
            </div>
          )}
          <div>
            <h1 className="text-xl font-bold">{gym.name}</h1>
            <p className="text-white/80 text-sm">Workout Tracker</p>
          </div>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 py-6 space-y-6">
        {/* Machine info */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex items-center gap-3 mb-1">
            <span
              className="text-white text-sm font-bold px-3 py-1 rounded-full"
              style={{ backgroundColor: gym.brandingColor }}
            >
              #{machine.machineNumber}
            </span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mt-2">{machine.name}</h2>
          <p className="text-gray-500 text-sm mt-1">
            Signed in as <strong>{session.user.email}</strong>
          </p>
        </div>

        {/* Workout form */}
        <WorkoutForm
          machineId={machine.id}
          brandingColor={gym.brandingColor}
        />

        {/* Recent entries */}
        <WorkoutHistory entries={recentEntries} brandingColor={gym.brandingColor} />
      </main>
    </div>
  );
}
