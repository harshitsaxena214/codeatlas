"use client";

import { useState } from "react";
import {
  Search,
  ZoomIn,
  ZoomOut,
  Maximize,
  Filter,
} from "lucide-react";

interface GraphControlsProps {
  onSearch?: (query: string) => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onFitView?: () => void;
  nodeTypes?: string[];
  activeFilters?: string[];
  onFilterToggle?: (type: string) => void;
}

const nodeTypeColors: Record<string, string> = {
  issue: "var(--accent-orange)",
  pr: "var(--accent-green)",
  discussion: "var(--accent-cyan)",
  feature: "var(--accent-yellow)",
  technology: "var(--accent-blue)",
  maintainer: "var(--accent-purple)",
  decision: "var(--accent-pink)",
  opportunity: "var(--accent-green)",
};

/**
 * GraphControls — Search, zoom, and filter controls for the knowledge graph.
 * Positioned as an overlay panel on the graph canvas.
 */
export function GraphControls({
  onSearch,
  onZoomIn,
  onZoomOut,
  onFitView,
  nodeTypes = [],
  activeFilters = [],
  onFilterToggle,
}: GraphControlsProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch?.(searchQuery);
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Search */}
      {onSearch && (
        <form onSubmit={handleSearch} className="glass-card p-2">
          <div className="relative">
            <Search
              size={14}
              className="absolute left-2.5 top-1/2 -translate-y-1/2"
              style={{ color: "var(--text-tertiary)" }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search nodes..."
              className="input-field pl-8 py-1.5 text-xs"
              style={{ fontSize: "12px" }}
            />
          </div>
        </form>
      )}

      {/* Zoom controls */}
      <div className="glass-card p-1 flex flex-col gap-0.5">
        {onZoomIn && (
          <button
            onClick={onZoomIn}
            className="p-1.5 rounded-md hover:bg-[var(--bg-tertiary)] transition-colors"
            title="Zoom in"
          >
            <ZoomIn size={14} style={{ color: "var(--text-secondary)" }} />
          </button>
        )}
        {onZoomOut && (
          <button
            onClick={onZoomOut}
            className="p-1.5 rounded-md hover:bg-[var(--bg-tertiary)] transition-colors"
            title="Zoom out"
          >
            <ZoomOut size={14} style={{ color: "var(--text-secondary)" }} />
          </button>
        )}
        {onFitView && (
          <button
            onClick={onFitView}
            className="p-1.5 rounded-md hover:bg-[var(--bg-tertiary)] transition-colors"
            title="Fit to view"
          >
            <Maximize size={14} style={{ color: "var(--text-secondary)" }} />
          </button>
        )}
      </div>

      {/* Filter controls */}
      {nodeTypes.length > 0 && onFilterToggle && (
        <div className="glass-card p-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-1.5 text-xs w-full"
            style={{ color: "var(--text-secondary)" }}
          >
            <Filter size={12} />
            <span>Filter</span>
            <span
              className="ml-auto text-xs"
              style={{ color: "var(--text-tertiary)" }}
            >
              {activeFilters.length}/{nodeTypes.length}
            </span>
          </button>
          {showFilters && (
            <div className="flex flex-col gap-1 mt-2">
              {nodeTypes.map((type) => {
                const isActive = activeFilters.includes(type);
                const color = nodeTypeColors[type] || "var(--text-secondary)";
                return (
                  <button
                    key={type}
                    onClick={() => onFilterToggle(type)}
                    className="flex items-center gap-2 px-1.5 py-1 rounded text-xs transition-all"
                    style={{
                      background: isActive ? `${color}15` : "transparent",
                      color: isActive ? color : "var(--text-tertiary)",
                    }}
                  >
                    <div
                      className="w-2.5 h-2.5 rounded-full"
                      style={{
                        background: isActive ? color : "var(--bg-tertiary)",
                        border: `1px solid ${isActive ? color : "var(--border)"}`,
                      }}
                    />
                    <span className="capitalize">{type}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
