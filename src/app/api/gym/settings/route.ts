import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { HEX_COLOR_REGEX, isValidLogoUrl } from "@/lib/validation";

/**
 * PATCH /api/gym/settings
 * Updates the logoUrl and brandingColor for the admin's gym.
 * Only GYM_ADMIN or SUPER_ADMIN may call this endpoint.
 */
export async function PATCH(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (
      session.user.role !== "GYM_ADMIN" &&
      session.user.role !== "SUPER_ADMIN"
    ) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const gymId = session.user.gymId;
    if (!gymId) {
      return NextResponse.json(
        { error: "No gym associated with your account" },
        { status: 400 }
      );
    }

    const body = (await req.json()) as Record<string, unknown>;
    const { logoUrl, brandingColor } = body;

    // Validate brandingColor
    if (
      brandingColor !== undefined &&
      (typeof brandingColor !== "string" || !HEX_COLOR_REGEX.test(brandingColor))
    ) {
      return NextResponse.json(
        { error: "brandingColor must be a valid 6-digit hex color (e.g. #6366f1)" },
        { status: 400 }
      );
    }

    // logoUrl must be null (to remove) or a valid HTTPS URL
    if (logoUrl !== undefined && logoUrl !== null) {
      if (typeof logoUrl !== "string" || !isValidLogoUrl(logoUrl)) {
        return NextResponse.json(
          { error: "logoUrl must be a valid HTTPS URL or null" },
          { status: 400 }
        );
      }
    }

    // Build update payload with only the fields that were provided
    const data: Record<string, string | null> = {};
    if (brandingColor !== undefined) data.brandingColor = brandingColor as string;
    if (logoUrl !== undefined) data.logoUrl = logoUrl as string | null;

    if (Object.keys(data).length === 0) {
      return NextResponse.json({ error: "No fields to update" }, { status: 400 });
    }

    const updated = await prisma.gym.update({
      where: { id: gymId },
      data,
      select: { id: true, logoUrl: true, brandingColor: true },
    });

    return NextResponse.json(updated);
  } catch (error) {
    console.error("Error updating gym settings:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
