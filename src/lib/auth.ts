import { NextAuthOptions } from "next-auth";
import { PrismaAdapter } from "@auth/prisma-adapter";
import GoogleProvider from "next-auth/providers/google";
import EmailProvider from "next-auth/providers/email";
import { prisma } from "@/lib/prisma";
import { Role } from "@prisma/client";

export const authOptions: NextAuthOptions = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  adapter: PrismaAdapter(prisma) as any,
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),
    EmailProvider({
      server: {
        host: process.env.EMAIL_SERVER_HOST,
        port: Number(process.env.EMAIL_SERVER_PORT ?? 587),
        auth: {
          user: process.env.EMAIL_SERVER_USER,
          pass: process.env.EMAIL_SERVER_PASSWORD,
        },
      },
      from: process.env.EMAIL_FROM ?? "noreply@gymtrackqr.com",
    }),
  ],
  // JWT strategy is required so that next-auth/middleware (withAuth) can read
  // the session from the cookie. The "database" strategy stores an opaque token
  // that the middleware cannot decode, causing a redirect loop after sign-in.
  session: {
    strategy: "jwt",
  },
  callbacks: {
    // Populate the JWT on first sign-in (user is defined) and on subsequent
    // visits (user is undefined — return the existing token unchanged).
    async jwt({ token, user }) {
      if (user) {
        // First sign-in: user is always defined and has an id.
        // Eagerly store the id so subsequent requests don't hit the DB.
        token.id = user.id;
        // Fetch role and gymId — if not found yet use safe defaults.
        const dbUser = await prisma.user.findUnique({
          where: { id: user.id },
          select: { role: true, gymId: true },
        });
        token.role = (dbUser?.role ?? Role.USER) as Role;
        token.gymId = dbUser?.gymId ?? null;
      }
      return token;
    },
    // Expose token fields on the session object that is returned to the client.
    async session({ session, token }) {
      if (session.user) {
        // token.id is set on every sign-in above; fall back to empty string to
        // satisfy the non-optional Session.user.id type if the token is stale.
        session.user.id = token.id ?? "";
        session.user.role = (token.role ?? Role.USER) as Role;
        session.user.gymId = token.gymId ?? null;
      }
      return session;
    },
  },
  pages: {
    signIn: "/auth/signin",
    verifyRequest: "/auth/verify-request",
    error: "/auth/error",
  },
};
