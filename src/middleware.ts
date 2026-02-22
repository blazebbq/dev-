import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

export default withAuth(
  function middleware(req) {
    const { pathname } = req.nextUrl;
    const token = req.nextauth.token;

    // Protect dashboard - require GYM_ADMIN or SUPER_ADMIN
    if (pathname.startsWith("/dashboard")) {
      if (
        token?.role !== "GYM_ADMIN" &&
        token?.role !== "SUPER_ADMIN"
      ) {
        return NextResponse.redirect(new URL("/auth/signin", req.url));
      }
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized({ req, token }) {
        const { pathname } = req.nextUrl;

        // Machine pages require auth
        if (pathname.startsWith("/g/")) {
          return !!token;
        }

        // Dashboard requires auth
        if (pathname.startsWith("/dashboard")) {
          return !!token;
        }

        return true;
      },
    },
  }
);

export const config = {
  matcher: ["/g/:path*", "/dashboard/:path*"],
};
