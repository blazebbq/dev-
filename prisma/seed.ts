import { PrismaClient, PlanType, Role } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  console.log("🌱 Starting seed...");

  // Create demo gym
  const gym = await prisma.gym.upsert({
    where: { slug: "demo-gym" },
    update: {},
    create: {
      name: "Demo Gym",
      slug: "demo-gym",
      brandingColor: "#6366f1",
      planType: PlanType.FREE,
    },
  });

  console.log(`✅ Created gym: ${gym.name}`);

  // Create 5 demo machines
  const machineData = [
    { name: "Bench Press", machineNumber: "A1" },
    { name: "Squat Rack", machineNumber: "A2" },
    { name: "Leg Press", machineNumber: "B1" },
    { name: "Cable Row", machineNumber: "B2" },
    { name: "Lat Pulldown", machineNumber: "C1" },
  ];

  for (const machine of machineData) {
    await prisma.machine.upsert({
      where: {
        id: `seed-machine-${machine.machineNumber}`,
      },
      update: {},
      create: {
        id: `seed-machine-${machine.machineNumber}`,
        gymId: gym.id,
        name: machine.name,
        machineNumber: machine.machineNumber,
      },
    });
    console.log(`✅ Created machine: ${machine.name}`);
  }

  // Create admin user
  const admin = await prisma.user.upsert({
    where: { email: "admin@demo.com" },
    update: {},
    create: {
      email: "admin@demo.com",
      name: "Demo Admin",
      role: Role.GYM_ADMIN,
      gymId: gym.id,
    },
  });

  console.log(`✅ Created admin user: ${admin.email}`);
  console.log("🎉 Seed complete!");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
