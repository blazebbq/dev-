import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { randomUUID } from "crypto";

// Session lasts 30 days (same as NextAuth default)
const SESSION_EXPIRY_MS = 30 * 24 * 60 * 60 * 1000;

/**
 * POST /api/auth/dev-bypass
 *
 * Development-only route that instantly signs in a user matching DEV_BYPASS_EMAIL
 * without sending or clicking a magic-link email.
 *
 * It creates (or finds) the user in the database, inserts a NextAuth-compatible
 * Session row, sets the session-token cookie, and returns the URL to redirect to.
 *
 * Only works when DEV_BYPASS_EMAIL is set. Returns 404 otherwise.
 */
export async function POST(req: NextRequest) {
  const devBypassEmail = process.env.DEV_BYPASS_EMAIL;

  // Disabled when env var is not configured
  if (!devBypassEmail) {
    return NextResponse.json({ error: "Not available" }, { status: 404 });
  }

  const body = (await req.json()) as Record<string, unknown>;
  const { email, callbackUrl } = body;

  if (
    typeof email !== "string" ||
    email.trim().toLowerCase() !== devBypassEmail.trim().toLowerCase()
  ) {
    return NextResponse.json({ error: "Invalid bypass email" }, { status: 403 });
  }

  // Sanitise redirect target to prevent open-redirect abuse
  const safeCallbackUrl =
    typeof callbackUrl === "string" && callbackUrl.startsWith("/")
      ? callbackUrl
      : "/dashboard";

  // Upsert the dev user — mark email as verified so NextAuth treats it as valid
  const user = await prisma.user.upsert({
    where: { email: devBypassEmail },
    update: {},
    create: {
      email: devBypassEmail,
      name: "Dev Admin",
      emailVerified: new Date(),
    },
  });

  // Create a NextAuth-compatible database session
  const sessionToken = randomUUID();
  const expires = new Date(Date.now() + SESSION_EXPIRY_MS);

  await prisma.session.create({
    data: { sessionToken, userId: user.id, expires },
  });

  // NextAuth uses "__Secure-" prefix on HTTPS. Use the actual request protocol
  // (via x-forwarded-proto for proxied requests) rather than NEXTAUTH_URL alone.
  const proto =
    req.headers.get("x-forwarded-proto") ??
    req.nextUrl.protocol.replace(":", "");
  const isSecure = proto === "https";
  const cookieName = isSecure
    ? "__Secure-next-auth.session-token"
    : "next-auth.session-token";

  const response = NextResponse.json({ url: safeCallbackUrl });
  response.cookies.set(cookieName, sessionToken, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    expires,
    secure: isSecure,
  });

  return response;
}
