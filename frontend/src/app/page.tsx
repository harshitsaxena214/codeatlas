"use client";

/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import {
  BookOpen,
  BrainCircuit,
  GitFork,
  Target,
  Lightbulb,
  MessageSquare,
  Timer,
  GraduationCap,
  ArrowRight,
  Sparkles,
  Zap,
  Code,
} from "lucide-react";

const features = [
  {
    icon: BookOpen,
    title: "Onboarding Guide",
    description:
      "Instantly understand what a project does, its culture, key maintainers, and the best reading path for new contributors.",
    color: "var(--accent-green)",
  },
  {
    icon: Target,
    title: "Find My First Issue",
    description:
      "AI-powered issue matching based on your experience level and interests. Find the perfect first contribution.",
    color: "var(--accent-orange)",
  },
  {
    icon: BrainCircuit,
    title: "Maintainer Brain",
    description:
      "Understand maintainer preferences, review patterns, and what gets PRs accepted vs rejected.",
    color: "var(--accent-purple)",
  },
  {
    icon: Lightbulb,
    title: "Decision Explorer",
    description:
      "Understand WHY decisions were made. Trace architecture choices through discussions, PRs, and reviews.",
    color: "var(--accent-yellow)",
  },
  {
    icon: MessageSquare,
    title: "Repository Q&A",
    description:
      "Ask anything about the repository and get answers backed by real issues, PRs, and discussions.",
    color: "var(--accent-cyan)",
  },
  {
    icon: GitFork,
    title: "Knowledge Graph",
    description:
      "Visualize how issues, PRs, discussions, features, and maintainers are interconnected.",
    color: "var(--accent-pink)",
  },
  {
    icon: Timer,
    title: "Project Timeline",
    description:
      "See the evolution of a project — major milestones, architecture changes, and key decisions.",
    color: "var(--accent-blue)",
  },
  {
    icon: GraduationCap,
    title: "Learning Path",
    description:
      "Personalized learning path that prepares you to contribute, based on the repo's tech stack.",
    color: "var(--accent-green)",
  },
];

import { useSession } from "next-auth/react";

export default function HomePage() {
  const { data: session } = useSession();

  return (
    <div className="min-h-screen" style={{ background: "var(--bg-primary)" }}>
      {/* Nav */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4"
        style={{
          background: "hsla(225, 25%, 6%, 0.8)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <Link href="/" className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "var(--gradient-primary)" }}
          >
            <Sparkles size={16} color="white" />
          </div>
          <span
            className="text-lg font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            CodeAtlas
          </span>
        </Link>
        <div className="flex items-center gap-3">
          {session ? (
            <>
              <Link href="/dashboard" className="btn-ghost text-sm">
                Dashboard
              </Link>
              <Link href="/analyze" className="btn-primary text-sm">
                <Zap size={14} />
                Analyze Repo
              </Link>
              {session.user?.image && (
                <img
                  src={session.user.image} 
                  alt="Avatar" 
                  className="w-8 h-8 rounded-full ml-2 border border-white/10" 
                />
              )}
            </>
          ) : (
            <Link href="/auth/signin" className="btn-primary text-sm">
              <Zap size={14} />
              Get Started
            </Link>
          )}
        </div>
      </nav>

      {/* Hero */}
      <section className="relative flex flex-col items-center text-center pt-40 pb-20 px-6 bg-radial-glow">
        {/* Background grid */}
        <div className="absolute inset-0 bg-grid opacity-30" />

        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="animate-fade-in-up">
            <div
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium mb-8"
              style={{
                background: "hsla(217, 91%, 60%, 0.1)",
                border: "1px solid hsla(217, 91%, 60%, 0.2)",
                color: "var(--accent-blue)",
              }}
            >
              <Sparkles size={12} />
              Powered by Cognee Knowledge Graph
            </div>
          </div>

          <h1
            className="text-5xl md:text-7xl font-bold leading-tight mb-6 animate-fade-in-up delay-100"
            style={{ color: "var(--text-primary)" }}
          >
            From first visit to{" "}
            <span className="gradient-text">first PR</span> in minutes
          </h1>

          <p
            className="text-lg md:text-xl max-w-2xl mx-auto mb-10 animate-fade-in-up delay-200 leading-relaxed"
            style={{ color: "var(--text-secondary)" }}
          >
            Paste any GitHub repo URL. CodeAtlas ingests its entire history into
            an AI knowledge graph, then mentors you through your first
            contribution.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-up delay-300">
            {session ? (
              <>
                <Link
                  href="/analyze"
                  className="btn-primary px-8 py-3 text-base rounded-xl"
                >
                  <Zap size={18} />
                  Analyze a Repository
                </Link>
                <Link
                  href="/dashboard"
                  className="btn-secondary px-8 py-3 text-base rounded-xl"
                >
                  <Code size={18} />
                  View Dashboard
                </Link>
              </>
            ) : (
              <Link
                href="/auth/signin"
                className="btn-primary px-8 py-3 text-base rounded-xl"
              >
                <Zap size={18} />
                Get Started
              </Link>
            )}
          </div>
        </div>

        {/* Floating orbs */}
        <div
          className="absolute top-32 left-16 w-64 h-64 rounded-full opacity-20 blur-3xl animate-float"
          style={{ background: "var(--accent-blue)" }}
        />
        <div
          className="absolute bottom-16 right-16 w-48 h-48 rounded-full opacity-15 blur-3xl animate-float delay-500"
          style={{ background: "var(--accent-purple)" }}
        />
      </section>

      {/* How it works */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2
            className="text-3xl font-bold text-center mb-4"
            style={{ color: "var(--text-primary)" }}
          >
            How it works
          </h2>
          <p
            className="text-center mb-12 text-base"
            style={{ color: "var(--text-secondary)" }}
          >
            Three steps to your first open source contribution
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                step: "01",
                title: "Paste a GitHub URL",
                desc: "Enter any public GitHub repository URL to begin analysis.",
                color: "var(--accent-blue)",
              },
              {
                step: "02",
                title: "AI Ingests History",
                desc: "README, Issues, PRs, Discussions, and Contributors are analyzed and stored in a knowledge graph.",
                color: "var(--accent-purple)",
              },
              {
                step: "03",
                title: "Get Mentored",
                desc: "Receive personalized onboarding, issue recommendations, and contribution intelligence.",
                color: "var(--accent-green)",
              },
            ].map((item, i) => (
              <div
                key={item.step}
                className="glass-card p-6 animate-fade-in-up relative overflow-hidden"
                style={{ animationDelay: `${i * 150}ms` }}
              >
                <div
                  className="text-5xl font-black mb-4 opacity-10"
                  style={{ color: item.color }}
                >
                  {item.step}
                </div>
                <h3
                  className="text-lg font-semibold mb-2"
                  style={{ color: "var(--text-primary)" }}
                >
                  {item.title}
                </h3>
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features grid */}
      <section className="py-20 px-6" style={{ background: "var(--bg-secondary)" }}>
        <div className="max-w-6xl mx-auto">
          <h2
            className="text-3xl font-bold text-center mb-4"
            style={{ color: "var(--text-primary)" }}
          >
            9 AI-Powered Features
          </h2>
          <p
            className="text-center mb-12 text-base"
            style={{ color: "var(--text-secondary)" }}
          >
            Everything you need to go from newcomer to contributor
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className="glass-card-hover p-5 animate-fade-in-up"
                style={{ animationDelay: `${i * 75}ms` }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
                  style={{
                    background: `${feature.color}15`,
                    color: feature.color,
                  }}
                >
                  <feature.icon size={20} />
                </div>
                <h3
                  className="text-sm font-semibold mb-1.5"
                  style={{ color: "var(--text-primary)" }}
                >
                  {feature.title}
                </h3>
                <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2
            className="text-3xl font-bold mb-4"
            style={{ color: "var(--text-primary)" }}
          >
            Ready to contribute?
          </h2>
          <p
            className="mb-8 text-base"
            style={{ color: "var(--text-secondary)" }}
          >
            Start by analyzing a repository you&apos;re interested in.
          </p>
          {session ? (
            <Link
              href="/analyze"
              className="btn-primary px-8 py-3 text-base rounded-xl"
            >
              Analyze a Repository
              <ArrowRight size={18} />
            </Link>
          ) : (
            <Link
              href="/auth/signin"
              className="btn-primary px-8 py-3 text-base rounded-xl"
            >
              Get Started
              <ArrowRight size={18} />
            </Link>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer
        className="py-6 px-6 text-center text-xs"
        style={{
          borderTop: "1px solid var(--border)",
          color: "var(--text-tertiary)",
        }}
      >
        CodeAtlas — Open Source Mentor • Powered by Cognee
      </footer>
    </div>
  );
}
