"use client";

/* eslint-disable @next/next/no-img-element */

import { User } from "lucide-react";
import { MaintainerProfile } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";

interface MaintainerCardProps {
  profile: MaintainerProfile;
  index?: number;
}

/**
 * MaintainerCard — Displays a maintainer's profile with avatar,
 * review count, preferences, and common feedback patterns.
 */
export function MaintainerCard({ profile, index = 0 }: MaintainerCardProps) {
  return (
    <GlassCard
      className="animate-fade-in-up"
      hover
    >
      <div style={{ animationDelay: `${index * 100}ms` }}>
        <div className="flex items-center gap-3 mb-3">
          <div
            className="w-9 h-9 rounded-full flex items-center justify-center overflow-hidden"
            style={{ background: "var(--bg-tertiary)" }}
          >
            {profile.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt={profile.username}
                className="w-full h-full object-cover"
              />
            ) : (
              <User
                size={16}
                style={{ color: "var(--text-secondary)" }}
              />
            )}
          </div>
          <div>
            <div
              className="text-sm font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              @{profile.username}
            </div>
            <div
              className="text-xs"
              style={{ color: "var(--text-tertiary)" }}
            >
              {profile.review_count} reviews
            </div>
          </div>
        </div>

        {profile.preferences.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {profile.preferences.map((p) => (
              <span key={p} className="badge badge-purple text-xs">
                {p}
              </span>
            ))}
          </div>
        )}

        {profile.common_feedback.length > 0 && (
          <ul className="flex flex-col gap-1">
            {profile.common_feedback.slice(0, 3).map((fb, j) => (
              <li
                key={j}
                className="text-xs"
                style={{ color: "var(--text-secondary)" }}
              >
                • {fb}
              </li>
            ))}
          </ul>
        )}
      </div>
    </GlassCard>
  );
}
