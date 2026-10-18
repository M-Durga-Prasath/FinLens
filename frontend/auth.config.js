import Google from "next-auth/providers/google";

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

    // Always return users to the chat page after a successful sign-in.
    async redirect({ url, baseUrl }) {
      if (url.startsWith(baseUrl)) return url;
      if (url.startsWith("/")) return `${baseUrl}${url}`;
      return `${baseUrl}/chat`;
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
