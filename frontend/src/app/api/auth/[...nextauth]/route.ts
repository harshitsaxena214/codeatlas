import NextAuth from "next-auth";
import GithubProvider from "next-auth/providers/github";

const handler = NextAuth({
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_ID || "",
      clientSecret: process.env.GITHUB_SECRET || "",
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      if (account?.provider === "github") {
        try {
          // Sync user to FastAPI backend
          const res = await fetch("http://localhost:8000/api/auth/github", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              github_id: profile?.id || 0,
              username: (profile as any)?.login || user.name || "unknown",
              email: user.email || "",
              avatar_url: user.image || "",
              access_token: account.access_token || "",
            }),
          });

          if (!res.ok) {
            console.error("Failed to sync user with backend");
            return false;
          }

          const dbUser = await res.json();
          // Attach the backend user ID to the user object for the session
          (user as any).backendId = dbUser.id;
          return true;
        } catch (error) {
          console.error("Error syncing user with backend:", error);
          return false;
        }
      }
      return true;
    },
    async jwt({ token, user, account, profile }) {
      if (user) {
        token.backendId = (user as any).backendId;
        token.githubId = (profile as any)?.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).backendId = token.backendId;
        (session.user as any).githubId = token.githubId;
      }
      return session;
    },
  },
  pages: {
    signIn: "/auth/signin",
  },
  secret: process.env.NEXTAUTH_SECRET,
});

export { handler as GET, handler as POST };
