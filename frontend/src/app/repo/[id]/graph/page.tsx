"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { GlassCard } from "@/components/GlassCard";

const nodeTypeColors: Record<string, string> = {
  issue: "var(--accent-orange)",
  pr: "var(--accent-green)",
  discussion: "var(--accent-cyan)",
  feature: "var(--accent-yellow)",
  technology: "var(--accent-blue)",
  maintainer: "var(--accent-purple)",
  decision: "var(--accent-pink)",
  opportunity: "var(--accent-green)",
  default: "var(--text-secondary)",
};

function getNodeColor(type: string): string {
  return nodeTypeColors[type.toLowerCase()] || nodeTypeColors.default;
}

function stableOffset(value: string, axis: "x" | "y"): number {
  let hash = axis === "x" ? 17 : 31;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 33 + value.charCodeAt(i)) % 40;
  }
  return hash;
}

export default function KnowledgeGraphPage() {
  const params = useParams();
  const repoId = params.id as string;

  const { data: graphData, isLoading, error } = useQuery({
    queryKey: ["knowledge-graph", repoId],
    queryFn: () => api.getKnowledgeGraph(repoId),
    enabled: !!repoId,
  });

  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const initialNodes: Node[] = useMemo(() => {
    if (!graphData) return [];
    return graphData.nodes.map((n, i) => {
      const cols = Math.ceil(Math.sqrt(graphData.nodes.length));
      const row = Math.floor(i / cols);
      const col = i % cols;
      const color = getNodeColor(n.node_type);

      return {
        id: n.id,
        position: {
          x: col * 220 + stableOffset(n.id, "x"),
          y: row * 150 + stableOffset(n.id, "y"),
        },
        data: {
          label: n.label,
          nodeType: n.node_type,
          metadata: n.metadata,
          color,
        },
        style: {
          background: "var(--bg-secondary)",
          color: "var(--text-primary)",
          border: `2px solid ${color}`,
          borderRadius: "12px",
          padding: "8px 14px",
          fontSize: "12px",
          fontWeight: 500,
          boxShadow: `0 0 12px ${color}30`,
          maxWidth: "180px",
          textAlign: "center" as const,
        },
      };
    });
  }, [graphData]);

  const initialEdges: Edge[] = useMemo(() => {
    if (!graphData) return [];
    return graphData.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      style: { stroke: "var(--border-light)", strokeWidth: 1.5 },
      labelStyle: {
        fontSize: 10,
        fill: "var(--text-tertiary)",
        fontWeight: 400,
      },
      animated: true,
    }));
  }, [graphData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center gap-2" style={{ color: "var(--text-secondary)" }}>
          <Loader2 size={20} className="animate-spin" />
          Building knowledge graph...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <GlassCard>
          <p style={{ color: "var(--accent-red)" }}>{(error as Error).message}</p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
          minZoom={0.2}
          maxZoom={2}
          style={{ background: "var(--bg-primary)" }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="var(--border)" />
          <Controls
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
            }}
          />
          <MiniMap
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
            }}
            nodeColor={(n) => (n.data as Record<string, string>)?.color || "var(--text-secondary)"}
            maskColor="hsla(225, 25%, 6%, 0.8)"
          />
        </ReactFlow>

        {/* Legend */}
        <div
          className="absolute top-4 left-4 glass-card p-3"
          style={{ fontSize: "11px" }}
        >
          <div className="font-medium mb-2" style={{ color: "var(--text-primary)" }}>
            Legend
          </div>
          <div className="flex flex-col gap-1.5">
            {Object.entries(nodeTypeColors)
              .filter(([k]) => k !== "default")
              .map(([type, color]) => (
                <div key={type} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ background: color }}
                  />
                  <span className="capitalize" style={{ color: "var(--text-secondary)" }}>
                    {type}
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* Summary */}
        {graphData?.summary && (
          <div className="absolute bottom-4 left-4 right-4 max-w-md glass-card p-3 text-xs" style={{ color: "var(--text-secondary)" }}>
            {graphData.summary}
          </div>
        )}
      </div>

      {/* Detail panel */}
      {selectedNode && (
        <div
          className="w-72 border-l overflow-auto p-4 animate-slide-in-right"
          style={{
            background: "var(--bg-secondary)",
            borderColor: "var(--border)",
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              {(selectedNode.data as Record<string, string>).label}
            </h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-xs"
              style={{ color: "var(--text-tertiary)" }}
            >
              ✕
            </button>
          </div>
          <span
            className="badge text-xs capitalize"
            style={{
              background: `${(selectedNode.data as Record<string, string>).color}20`,
              color: (selectedNode.data as Record<string, string>).color,
            }}
          >
            {(selectedNode.data as Record<string, string>).nodeType}
          </span>
          {Boolean((selectedNode.data as Record<string, unknown>).metadata) && (
            <div className="mt-3 text-xs" style={{ color: "var(--text-secondary)" }}>
              <pre className="whitespace-pre-wrap">
                {JSON.stringify((selectedNode.data as Record<string, unknown>).metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
