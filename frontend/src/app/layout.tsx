import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "./providers";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CodeAtlas — Open Source Mentor",
  description:
    "From first visit to first PR in minutes. AI-powered repository onboarding and contribution intelligence powered by Cognee.",
  keywords: [
    "open source",
    "mentoring",
    "github",
    "contributions",
    "AI",
    "knowledge graph",
  ],
  openGraph: {
    title: "CodeAtlas — Open Source Mentor",
    description:
      "From first visit to first PR in minutes. AI-powered repository intelligence.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
