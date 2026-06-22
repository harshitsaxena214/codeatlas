export { default } from "next-auth/middleware";

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/analyze/:path*",
    "/repo/:path*",
  ],
};
