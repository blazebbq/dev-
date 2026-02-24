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
        // Disable TLS certificate validation in development only (e.g. Ethereal
        // uses a self-signed cert). Never set rejectUnauthorized:false in production.
        tls:
          process.env.NODE_ENV === "development"
            ? { rejectUnauthorized: false }
            : undefined,
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
    // Populate the JWT on first sign-in (user is defined) and leave it untouched
    // on subsequent requests (user is undefined).
    async jwt({ token, user }) {
      if (user) {
        // With PrismaAdapter + EmailProvider, user.id is the DB record id, but
        // NextAuth also sets token.sub to the same value. Using the nullish
        // coalesce ensures we always have a non-undefined userId even in edge
        // cases where user.id arrives as undefined.
        const userId = user.id ?? token.sub;
        if (userId) {
          token.id = userId;
          const dbUser = await prisma.user.findUnique({
            where: { id: userId },
            select: { role: true, gymId: true },
          });
          token.role = (dbUser?.role ?? Role.USER) as Role;
          token.gymId = dbUser?.gymId ?? null;
        }
      }
      return token;
    },
    // Expose token fields on the session object returned to the client.
    // No reference to `user` here — that only exists in the database strategy.
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id ?? token.sub ?? "";
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
