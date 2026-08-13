import Google from "next-auth/providers/google";
import Resend from "next-auth/providers/resend";

/**
 * Auth config shared between the full auth.js (server — has Prisma adapter)
 * and middleware.js (Edge runtime — no Prisma allowed).
 */
export const authConfig = {
  session: { strategy: "jwt" },

  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      allowDangerousEmailAccountLinking: true,
    }),

    Resend({
      apiKey: process.env.AUTH_RESEND_KEY,
      from: process.env.AUTH_EMAIL_FROM || "onboarding@resend.dev",
      allowDangerousEmailAccountLinking: true,
    }),
  ],

  pages: {
    signIn: "/auth/signin",
    verifyRequest: "/auth/verify-request",
    error: "/auth/error",
  },

  callbacks: {
    /** Persist the DB user id into the JWT. */
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },

    /** Expose the user id on the client-side session object. */
    async session({ session, token }) {
      if (token?.id) {
        session.user.id = token.id;
      }
      return session;
    },

    /** Called by middleware to decide access — allow auth pages, block /chat if not signed in. */
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isChat = nextUrl.pathname.startsWith("/chat");

      if (isChat && !isLoggedIn) return false; // triggers redirect to signIn page
      return true;
    },
  },
};
