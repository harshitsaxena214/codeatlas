import NextAuth from "next-auth";
import type { Profile } from "next-auth";
import GithubProvider from "next-auth/providers/github";

interface GitHubProfile extends Profile {
  id?: number;
  login?: string;
}

interface BackendUser {
  id: string;
}

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
          const githubProfile = profile as GitHubProfile | undefined;
          const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

          // Sync user to FastAPI backend
          const res = await fetch(`${apiBase}/api/auth/github`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              github_id: githubProfile?.id || 0,
              username: githubProfile?.login || user.name || "unknown",
              email: user.email || "",
              avatar_url: user.image || "",
              access_token: account.access_token || "",
            }),
          });

          if (!res.ok) {
            console.error("Failed to sync user with backend");
            return false;
          }

          const dbUser = (await res.json()) as BackendUser;
          // Attach the backend user ID to the user object for the session
          user.backendId = dbUser.id;
          return true;
        } catch (error) {
          console.error("Error syncing user with backend:", error);
          return false;
        }
      }
      return true;
    },
    async jwt({ token, user, profile }) {
      if (user) {
        const githubProfile = profile as GitHubProfile | undefined;
        token.backendId = user.backendId;
        token.githubId = githubProfile?.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.backendId = token.backendId;
        session.user.githubId = token.githubId;
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
