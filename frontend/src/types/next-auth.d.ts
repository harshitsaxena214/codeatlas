import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user?: DefaultSession["user"] & {
      backendId?: string;
      githubId?: number;
    };
  }

  interface User {
    backendId?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    backendId?: string;
    githubId?: number;
  }
}
