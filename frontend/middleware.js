import NextAuth from "next-auth";
import { authConfig } from "./auth.config";

// Middleware runs in the Edge Runtime. Keep Prisma out of this import path;
// the Prisma adapter is used only by the server-side auth setup in auth.js.
export const { auth: middleware } = NextAuth(authConfig);

export const config = {
  matcher: ["/chat/:path*"],
};
