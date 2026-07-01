"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  BrainCircuit,
  GitFork,
  Home,
  Lightbulb,
  MessageSquare,
  Sparkles,
  Target,
  Timer,
  X,
  GraduationCap,
  Layers,
} from "lucide-react";

interface SidebarProps {
  repoId: string;
  repoName: string;
  repoOwner: string;
  isOpen?: boolean;
  onClose?: () => void;
}

const navItems = [
  { href: "", icon: Home, label: "Dashboard", color: "var(--accent-blue)" },
  {
    href: "/onboarding",
    icon: BookOpen,
    label: "Onboarding",
    color: "var(--accent-green)",
  },
  {
    href: "/find-issue",
    icon: Target,
    label: "Find My First Issue",
    color: "var(--accent-orange)",
  },
  {
    href: "/maintainer-brain",
    icon: BrainCircuit,
    label: "Maintainer Brain",
    color: "var(--accent-purple)",
  },
  {
    href: "/decisions",
    icon: Lightbulb,
    label: "Decision Explorer",
    color: "var(--accent-yellow)",
  },
  {
    href: "/ask",
    icon: MessageSquare,
    label: "Repository Q&A",
    color: "var(--accent-cyan)",
  },
  {
    href: "/architecture",
    icon: Layers,
    label: "Architecture Explorer",
    color: "var(--accent-purple)",
  },
  {
    href: "/graph",
    icon: GitFork,
    label: "Knowledge Graph",
    color: "var(--accent-pink)",
  },
  {
    href: "/timeline",
    icon: Timer,
    label: "Timeline",
    color: "var(--accent-blue)",
  },
  {
    href: "/learn",
    icon: GraduationCap,
    label: "Learning Path",
    color: "var(--accent-green)",
  },
];

export function Sidebar({
  repoId,
  repoName,
  repoOwner,
  isOpen = true,
  onClose,
}: SidebarProps) {
  const pathname = usePathname();
  const basePath = `/repo/${repoId}`;

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 left-0 h-full z-50 flex flex-col transition-transform duration-300
        lg:relative lg:translate-x-0 lg:z-auto
        ${isOpen ? "translate-x-0" : "-translate-x-full"}`}
        style={{
          width: "260px",
          background: "var(--bg-secondary)",
          borderRight: "1px solid var(--border)",
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-4"
          style={{ borderBottom: "1px solid var(--border)" }}
        >
          <Link href="/dashboard" className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: "var(--gradient-primary)" }}
            >
              <Sparkles size={14} color="white" />
            </div>
            <span
              className="font-semibold text-sm"
              style={{ color: "var(--text-primary)" }}
            >
              CodeAtlas
            </span>
          </Link>
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded-md hover:bg-[var(--bg-tertiary)]"
          >
            <X size={18} style={{ color: "var(--text-secondary)" }} />
          </button>
        </div>

        {/* Repo info */}
        <div
          className="px-5 py-3"
          style={{ borderBottom: "1px solid var(--border)" }}
        >
          <div
            className="text-xs font-medium mb-0.5"
            style={{ color: "var(--text-tertiary)" }}
          >
            REPOSITORY
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="text-xs"
              style={{ color: "var(--text-secondary)" }}
            >
              {repoOwner}/
            </span>
            <span
              className="text-sm font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              {repoName}
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-3">
          <div
            className="text-xs font-medium px-2 mb-2"
            style={{ color: "var(--text-tertiary)" }}
          >
            FEATURES
          </div>
          <ul className="flex flex-col gap-0.5">
            {navItems.map((item) => {
              const fullPath = `${basePath}${item.href}`;
              const isActive =
                item.href === ""
                  ? pathname === basePath
                  : pathname === fullPath;

              return (
                <li key={item.href}>
                  <Link
                    href={fullPath}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all"
                    style={{
                      background: isActive
                        ? "var(--bg-tertiary)"
                        : "transparent",
                      color: isActive
                        ? "var(--text-primary)"
                        : "var(--text-secondary)",
                      fontWeight: isActive ? 500 : 400,
                    }}
                    onClick={onClose}
                  >
                    <item.icon
                      size={16}
                      style={{
                        color: isActive ? item.color : "var(--text-tertiary)",
                      }}
                    />
                    {item.label}
                    {isActive && (
                      <div
                        className="ml-auto w-1.5 h-1.5 rounded-full"
                        style={{ background: item.color }}
                      />
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div
          className="px-5 py-3 text-xs"
          style={{
            borderTop: "1px solid var(--border)",
            color: "var(--text-tertiary)",
          }}
        >
          Powered by Cognee
        </div>
      </aside>
    </>
  );
}
