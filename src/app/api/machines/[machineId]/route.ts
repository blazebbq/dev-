import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import path from "path";
import fs from "fs/promises";

export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ machineId: string }> }
) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (session.user.role !== "GYM_ADMIN" && session.user.role !== "SUPER_ADMIN") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const { machineId } = await params;
    const body = await req.json() as Record<string, unknown>;
    const { name, machineNumber } = body;

    if (!name || typeof name !== "string" || name.trim().length === 0) {
      return NextResponse.json({ error: "Machine name is required" }, { status: 400 });
    }
    if (!machineNumber || typeof machineNumber !== "string" || machineNumber.trim().length === 0) {
      return NextResponse.json({ error: "Machine number is required" }, { status: 400 });
    }

    // Verify machine belongs to admin's gym
    const machine = await prisma.machine.findFirst({
      where: {
        id: machineId,
        gymId: session.user.gymId ?? "",
      },
    });

    if (!machine) {
      return NextResponse.json({ error: "Machine not found" }, { status: 404 });
    }

    const updated = await prisma.machine.update({
      where: { id: machineId },
      data: {
        name: name.trim(),
        machineNumber: machineNumber.trim(),
      },
    });

    return NextResponse.json(updated);
  } catch (error) {
    console.error("Error updating machine:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ machineId: string }> }
) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (session.user.role !== "GYM_ADMIN" && session.user.role !== "SUPER_ADMIN") {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const { machineId } = await params;

    // Verify machine belongs to admin's gym
    const machine = await prisma.machine.findFirst({
      where: {
        id: machineId,
        gymId: session.user.gymId ?? "",
      },
    });

    if (!machine) {
      return NextResponse.json({ error: "Machine not found" }, { status: 404 });
    }

    // Delete QR code file if exists
    if (machine.qrCodeUrl) {
      try {
        const filePath = path.join(process.cwd(), "public", machine.qrCodeUrl);
        await fs.unlink(filePath);
      } catch {
        // File might not exist, that's okay
      }
    }

    await prisma.machine.delete({ where: { id: machineId } });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error deleting machine:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
