"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Menu } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { api } from "@/lib/api";
import { PageSkeleton } from "@/components/LoadingSkeleton";

export default function RepoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const repoId = params.id as string;
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { data: repo, isLoading } = useQuery({
    queryKey: ["repository", repoId],
    queryFn: () => api.getRepository(repoId),
    enabled: !!repoId,
  });

  if (isLoading) {
    return (
      <div className="flex h-screen">
        <div
          className="hidden lg:block"
          style={{
            width: 260,
            background: "var(--bg-secondary)",
            borderRight: "1px solid var(--border)",
          }}
        />
        <main className="flex-1 overflow-auto p-6">
          <PageSkeleton />
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        repoId={repoId}
        repoName={repo?.name || ""}
        repoOwner={repo?.owner || ""}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile top bar */}
        <div
          className="flex items-center gap-3 px-4 py-3 lg:hidden"
          style={{
            background: "var(--bg-secondary)",
            borderBottom: "1px solid var(--border)",
          }}
        >
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-1.5 rounded-md"
            style={{ color: "var(--text-secondary)" }}
          >
            <Menu size={20} />
          </button>
          <span
            className="text-sm font-medium"
            style={{ color: "var(--text-primary)" }}
          >
            {repo?.owner}/{repo?.name}
          </span>
        </div>

        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
