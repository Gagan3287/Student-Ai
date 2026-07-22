"use client";

import { useEffect, useState } from "react";
import {
  Network,
  Loader2,
  AlertCircle,
  BookOpen,
  Info,
} from "lucide-react";
import { api } from "@/lib/api";
import { Document } from "@/types";

interface GraphNode {
  id: string;
  name: string;
  document_id: string;
}

interface GraphEdge {
  source: string;
  target: string;
  label: string | null;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function GraphPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [graph, setGraph] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const init = async () => {
      try {
        const [docsRes, graphRes] = await Promise.all([
          api.get<{ documents: Document[] }>("/documents"),
          api.get<GraphData>("/concepts/graph"),
        ]);
        setDocuments(docsRes.documents.filter((d) => d.status === "ready"));
        setGraph(graphRes);
      } catch (e: any) {
        setError("Failed to load graph data.");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const readyDocs = documents.filter((d) => d.status === "ready");

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full gap-3 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span>Loading knowledge graph…</span>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2 flex items-center gap-3">
          <Network className="h-8 w-8 text-primary" />
          Knowledge Graph
        </h1>
        <p className="text-muted-foreground">
          Visual map of concepts and their relationships across your notes
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm border border-destructive/20 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Info Banner */}
      <div className="mb-6 p-4 rounded-2xl bg-primary/5 border border-primary/20 flex items-start gap-3">
        <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-foreground">Phase 4 Feature</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            The concept knowledge graph is generated automatically when you process a document.
            Concepts are extracted by the AI and linked based on semantic relationships.
            Graph visualisation requires AI-processed documents.
          </p>
        </div>
      </div>

      {graph.nodes.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border p-16 text-center">
          <Network className="h-16 w-16 text-muted-foreground/30 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">No concepts yet</h3>
          <p className="text-muted-foreground text-sm max-w-md mx-auto">
            Upload and process a document. Once it's ready, AI-extracted concepts and their
            connections will appear here as an interactive graph.
          </p>
        </div>
      ) : (
        <div>
          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
            <div className="p-4 rounded-2xl bg-card border border-border text-center">
              <p className="text-3xl font-bold text-primary">{graph.nodes.length}</p>
              <p className="text-sm text-muted-foreground mt-1">Concepts</p>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border text-center">
              <p className="text-3xl font-bold text-primary">{graph.edges.length}</p>
              <p className="text-sm text-muted-foreground mt-1">Relationships</p>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border text-center">
              <p className="text-3xl font-bold text-primary">{readyDocs.length}</p>
              <p className="text-sm text-muted-foreground mt-1">Documents</p>
            </div>
          </div>

          {/* Concept list */}
          <div className="rounded-2xl border border-border bg-card overflow-hidden">
            <div className="px-5 py-4 border-b border-border/50">
              <h3 className="font-semibold">Concept Nodes</h3>
            </div>
            <div className="p-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {graph.nodes.map((node) => (
                <div
                  key={node.id}
                  className="px-4 py-2.5 rounded-xl bg-primary/5 border border-primary/15 hover:border-primary/40 transition-colors"
                >
                  <p className="text-sm font-medium text-foreground">{node.name}</p>
                  <p className="text-xs text-muted-foreground mt-0.5 truncate">
                    {documents.find((d) => d.id === node.document_id)?.title || "Unknown doc"}
                  </p>
                </div>
              ))}
            </div>
            {graph.edges.length > 0 && (
              <div className="border-t border-border/50 px-5 py-4">
                <h3 className="font-semibold mb-3">Relationships</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {graph.edges.map((edge, i) => {
                    const src = graph.nodes.find((n) => n.id === edge.source);
                    const tgt = graph.nodes.find((n) => n.id === edge.target);
                    return (
                      <div
                        key={i}
                        className="flex items-center gap-2 text-sm text-muted-foreground"
                      >
                        <span className="font-medium text-foreground">{src?.name}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-muted">
                          {edge.label || "relates to"}
                        </span>
                        <span className="font-medium text-foreground">{tgt?.name}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
