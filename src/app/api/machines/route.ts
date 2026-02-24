import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { generateMachineQRCode } from "@/lib/qrcode";

export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (session.user.role !== "GYM_ADMIN" && session.user.role !== "SUPER_ADMIN") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const body = await req.json() as Record<string, unknown>;
    const { name, machineNumber } = body;

    if (!name || typeof name !== "string" || name.trim().length === 0) {
      return NextResponse.json({ error: "Machine name is required" }, { status: 400 });
    }
    if (!machineNumber || typeof machineNumber !== "string" || machineNumber.trim().length === 0) {
      return NextResponse.json({ error: "Machine number is required" }, { status: 400 });
    }

    // Get gym for this admin
    const gymId = session.user.gymId;
    if (!gymId) {
      return NextResponse.json({ error: "No gym associated with your account" }, { status: 400 });
    }

    const gym = await prisma.gym.findUnique({ where: { id: gymId } });
    if (!gym) {
      return NextResponse.json({ error: "Gym not found" }, { status: 404 });
    }

    // Create machine first (without QR URL)
    const machine = await prisma.machine.create({
      data: {
        gymId,
        name: name.trim(),
        machineNumber: machineNumber.trim(),
      },
    });

    // Generate QR code
    const qrCodeUrl = await generateMachineQRCode(gym.slug, machine.id);

    // Update machine with QR code URL
    const updatedMachine = await prisma.machine.update({
      where: { id: machine.id },
      data: { qrCodeUrl },
    });

    return NextResponse.json(updatedMachine, { status: 201 });
  } catch (error) {
    console.error("Error creating machine:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (session.user.role !== "GYM_ADMIN" && session.user.role !== "SUPER_ADMIN") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const gymId = session.user.gymId;
    if (!gymId) {
      return NextResponse.json({ error: "No gym associated with your account" }, { status: 400 });
    }

    const machines = await prisma.machine.findMany({
      where: { gymId },
      orderBy: { createdAt: "asc" },
      include: {
        _count: {
          select: { workoutEntries: true },
        },
      },
    });

    return NextResponse.json(machines);
  } catch (error) {
    console.error("Error fetching machines:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
