import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { redirect } from "next/navigation";
import { MachineList } from "@/components/MachineList";
import { DashboardStats } from "@/components/DashboardStats";
import { AdBanner } from "@/components/AdBanner";
import { SignOutButton } from "@/components/SignOutButton";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    redirect("/auth/signin");
  }

  if (session.user.role !== "GYM_ADMIN" && session.user.role !== "SUPER_ADMIN") {
    redirect("/auth/signin");
  }

  const gymId = session.user.gymId;
  if (!gymId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-xl font-bold text-gray-900">No gym associated</h2>
          <p className="text-gray-600 mt-2">Please contact support to set up your gym.</p>
        </div>
      </div>
    );
  }

  const gym = await prisma.gym.findUnique({
    where: { id: gymId },
    include: {
      machines: {
        include: {
          _count: {
            select: { workoutEntries: true },
          },
        },
        orderBy: { createdAt: "asc" },
      },
    },
  });

  if (!gym) {
    redirect("/auth/signin");
  }

  // Stats
  const totalScans = gym.machines.reduce(
    (acc, m) => acc + m._count.workoutEntries,
    0
  );

  const activeUsersCount = await prisma.workoutEntry.findMany({
    where: { machine: { gymId } },
    select: { userId: true },
    distinct: ["userId"],
  }).then((r) => r.length);

  const mostUsedMachine =
    gym.machines.length > 0
      ? gym.machines.reduce((prev, cur) =>
          cur._count.workoutEntries > prev._count.workoutEntries ? cur : prev
        )
      : null;

  return (
    <div
      className="min-h-screen bg-gray-50"
      style={{ "--brand-color": gym.brandingColor } as React.CSSProperties}
    >
      {/* Header */}
      <header
        className="text-white py-5 px-4 shadow-lg"
        style={{ backgroundColor: gym.brandingColor }}
      >
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">{gym.name}</h1>
            <p className="text-white/80 text-sm">Admin Dashboard</p>
          </div>
          <SignOutButton />
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Ad banner for FREE plan */}
        {gym.planType === "FREE" && <AdBanner />}

        {/* Stats */}
        <DashboardStats
          totalScans={totalScans}
          activeUsers={activeUsersCount}
          mostUsedMachine={mostUsedMachine?.name ?? null}
          planType={gym.planType}
        />

        {/* Machine list with CRUD */}
        <MachineList
          machines={gym.machines.map((m) => ({
            id: m.id,
            name: m.name,
            machineNumber: m.machineNumber,
            qrCodeUrl: m.qrCodeUrl,
            entryCount: m._count.workoutEntries,
          }))}
          gymSlug={gym.slug}
          brandingColor={gym.brandingColor}
        />
      </main>
    </div>
  );
}
