import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await req.json() as Record<string, unknown>;
    const { machineId, weight, reps, notes } = body;

    // Validate inputs
    if (!machineId || typeof machineId !== "string") {
      return NextResponse.json({ error: "Machine ID is required" }, { status: 400 });
    }
    if (typeof weight !== "number" || weight <= 0) {
      return NextResponse.json({ error: "Weight must be a positive number" }, { status: 400 });
    }
    if (typeof reps !== "number" || !Number.isInteger(reps) || reps <= 0) {
      return NextResponse.json({ error: "Reps must be a positive integer" }, { status: 400 });
    }
    if (notes !== undefined && (typeof notes !== "string" || notes.length > 500)) {
      return NextResponse.json({ error: "Notes must be a string under 500 characters" }, { status: 400 });
    }

    // Verify machine exists
    const machine = await prisma.machine.findUnique({
      where: { id: machineId },
    });

    if (!machine) {
      return NextResponse.json({ error: "Machine not found" }, { status: 404 });
    }

    const entry = await prisma.workoutEntry.create({
      data: {
        userId: session.user.id,
        machineId,
        weight,
        reps,
        notes: typeof notes === "string" ? notes : undefined,
      },
    });

    return NextResponse.json(entry, { status: 201 });
  } catch (error) {
    console.error("Error saving workout:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
