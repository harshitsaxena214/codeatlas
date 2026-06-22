"use client";

import { signIn } from "next-auth/react";
import { Sparkles } from "lucide-react";
import { useState } from "react";
import Link from "next/link";

const GithubIcon = ({ size = 24, style = {} }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={style}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

export default function SignInPage() {
  const [isLoading, setIsLoading] = useState(false);

  const handleSignIn = async () => {
    setIsLoading(true);
    // next-auth signIn will redirect away, so we just set loading to true
    await signIn("github", { callbackUrl: "/dashboard" });
  };

  return (
    <div className="min-h-screen flex flex-col relative" style={{ background: "var(--bg-primary)" }}>
      {/* Background styling to match landing page */}
      <div className="absolute inset-0 bg-grid opacity-30" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-20 blur-3xl" style={{ background: "var(--accent-blue)" }} />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full opacity-15 blur-3xl" style={{ background: "var(--accent-purple)" }} />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-6">
        <Link href="/" className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "var(--gradient-primary)" }}
          >
            <Sparkles size={16} color="white" />
          </div>
          <span className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
            CodeAtlas
          </span>
        </Link>
      </nav>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center relative z-10 px-6">
        <div className="glass-card max-w-md w-full p-8 text-center animate-fade-in-up">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6" style={{ background: "hsla(217, 91%, 60%, 0.1)", border: "1px solid hsla(217, 91%, 60%, 0.2)" }}>
            <GithubIcon size={32} style={{ color: "var(--accent-blue)" }} />
          </div>
          
          <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
            Welcome to CodeAtlas
          </h1>
          <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
            Sign in with GitHub to analyze repositories, explore knowledge graphs, and find your first issue.
          </p>

          <button
            onClick={handleSignIn}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-xl text-sm font-medium transition-all"
            style={{ 
              background: "var(--text-primary)", 
              color: "var(--bg-primary)",
              opacity: isLoading ? 0.7 : 1 
            }}
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <GithubIcon size={20} />
            )}
            {isLoading ? "Connecting to GitHub..." : "Continue with GitHub"}
          </button>

          <div className="mt-6 text-xs text-center" style={{ color: "var(--text-tertiary)" }}>
            <p>By signing in, you agree to our Terms of Service and Privacy Policy.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
