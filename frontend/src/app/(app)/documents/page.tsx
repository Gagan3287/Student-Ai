"use client";

import { useEffect, useState, useRef } from "react";
import {
  Upload,
  FileText,
  Trash2,
  Eye,
  RefreshCw,
  AlertCircle,
  Loader2,
  CheckCircle2,
  FileUp,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { Document } from "@/types";
import { Button } from "@/components/ui/button";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch all documents
  const fetchDocuments = async (showSilent = false) => {
    if (!showSilent) setLoading(true);
    try {
      const data = await api.get<{ documents: Document[]; total: number }>("/documents");
      setDocuments(data.documents);
      setError("");
    } catch (err: any) {
      setError(err.detail || "Failed to load documents.");
    } finally {
      if (!showSilent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    return () => stopPolling();
  }, []);

  // Set up polling if there are pending or processing documents
  useEffect(() => {
    const hasActiveJobs = documents.some(
      (doc) => doc.status === "pending" || doc.status === "processing"
    );

    if (hasActiveJobs) {
      startPolling();
    } else {
      stopPolling();
    }
  }, [documents]);

  const startPolling = () => {
    if (pollingIntervalRef.current) return;
    pollingIntervalRef.current = setInterval(() => {
      fetchDocuments(true);
    }, 3000);
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  // Drag & Drop event handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    const fileExtension = file.name.split(".").pop()?.toLowerCase();
    if (fileExtension !== "pdf" && fileExtension !== "txt") {
      setError("Unsupported file format. Please upload PDF or TXT files only.");
      return;
    }

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      await api.upload<Document>("/documents/upload", file);
      setSuccess(`"${file.name}" uploaded successfully. Processing started...`);
      fetchDocuments(true);
    } catch (err: any) {
      setError(err.detail || "Failed to upload document.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDelete = async (docId: string, docTitle: string) => {
    if (!confirm(`Are you sure you want to delete "${docTitle}"?`)) return;

    try {
      await api.delete(`/documents/${docId}`);
      setSuccess(`"${docTitle}" deleted successfully.`);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      if (selectedDoc?.id === docId) setSelectedDoc(null);
    } catch (err: any) {
      setError(err.detail || "Failed to delete document.");
    }
  };

  const handleReprocess = async (docId: string) => {
    try {
      setError("");
      setSuccess("Reprocessing task scheduled.");
      await api.post(`/documents/${docId}/process`);
      fetchDocuments(true);
    } catch (err: any) {
      setError(err.detail || "Failed to schedule reprocessing.");
    }
  };

  const getStatusBadge = (doc: Document) => {
    const isTruncated = doc.summary?.includes("Large document notice");
    switch (doc.status) {
      case "ready":
        return (
          <div className="flex flex-col gap-1 items-start">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Ready
            </span>
            {isTruncated && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium bg-amber-500/10 text-amber-500 border border-amber-500/20" title="Document exceeded 300 chunks and was truncated for AI indexing">
                <AlertCircle className="h-3 w-3" />
                Truncated (300 max)
              </span>
            )}
          </div>
        );
      case "processing":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 animate-pulse">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Processing
          </span>
        );
      case "pending":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-500 border border-amber-500/20">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Pending
          </span>
        );
      case "error":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-destructive/10 text-destructive border border-destructive/20">
            <AlertCircle className="h-3.5 w-3.5" />
            Error
          </span>
        );
    }
  };

  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground">My Notes</h1>
        <p className="text-muted-foreground mt-1 font-light">
          Upload and manage your study documents. Notes are auto-chunked and embedded for RAG query retrieval.
        </p>
      </div>

      {/* Notifications */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl bg-destructive/10 p-4 border border-destructive/20 text-sm text-destructive">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-3 rounded-xl bg-emerald-500/10 p-4 border border-emerald-500/20 text-sm text-emerald-500">
          <CheckCircle2 className="h-5 w-5 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Main Grid: Upload Area & Documents List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: File Upload Component */}
        <div className="lg:col-span-1 space-y-6">
          <h2 className="text-xl font-bold">Upload Document</h2>
          
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 min-h-[260px] ${
              isDragActive
                ? "border-primary bg-primary/5 scale-[1.02]"
                : "border-border/60 bg-card hover:border-primary/50 hover:bg-accent/5 hover:scale-[1.01]"
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.txt"
              className="hidden"
            />
            
            {uploading ? (
              <div className="space-y-4">
                <Loader2 className="h-12 w-12 text-primary animate-spin mx-auto" />
                <div>
                  <p className="font-semibold">Uploading file...</p>
                  <p className="text-xs text-muted-foreground font-light mt-1">Storing and indexing document chunks.</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-primary/10 text-primary rounded-2xl w-fit mx-auto">
                  <FileUp className="h-8 w-8" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">Drag & drop your files here</p>
                  <p className="text-sm text-muted-foreground font-light mt-1">or click to browse directories</p>
                </div>
                <div className="text-[11px] text-muted-foreground font-light max-w-[200px] mx-auto bg-muted/50 py-1.5 px-3 rounded-lg border border-border/40">
                  Accepts PDF or TXT documents up to 25MB
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Documents List Table */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Documents List</h2>
            <button
              onClick={() => fetchDocuments()}
              disabled={loading}
              className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-accent border border-border/40 transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>

          {loading ? (
            <div className="border border-border/50 bg-card rounded-2xl p-12 text-center flex flex-col items-center justify-center">
              <Loader2 className="h-8 w-8 text-primary animate-spin mb-4" />
              <p className="text-sm text-muted-foreground">Retrieving study database...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="border-2 border-dashed border-border/50 bg-card rounded-2xl p-12 text-center flex flex-col items-center justify-center">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="font-medium text-foreground text-lg">No documents uploaded yet</p>
              <p className="text-sm text-muted-foreground font-light mt-1 max-w-sm">
                Get started by uploading engineering class notes, worksheets, or reference files.
              </p>
            </div>
          ) : (
            <div className="border border-border/50 bg-card rounded-2xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-border/50 bg-muted/30">
                      <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Document Title</th>
                      <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Type & Pages</th>
                      <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Status</th>
                      <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {documents.map((doc) => (
                      <tr key={doc.id} className="hover:bg-accent/10 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-indigo-500/10 text-indigo-500 rounded-lg shrink-0">
                              <FileText className="h-4.5 w-4.5" />
                            </div>
                            <span className="font-semibold text-sm text-foreground truncate max-w-[200px]" title={doc.title}>
                              {doc.title}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-xs text-muted-foreground font-light">
                          <div className="space-y-0.5">
                            <span className="font-medium uppercase bg-muted px-1.5 py-0.5 rounded text-[10px]">
                              {doc.content_type?.split("/")[1] || "doc"}
                            </span>
                            <p>{doc.page_count ? `${doc.page_count} pages` : "Processing..."}</p>
                          </div>
                        </td>
                        <td className="px-6 py-4">{getStatusBadge(doc)}</td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {doc.status === "ready" && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setSelectedDoc(doc)}
                                className="flex items-center gap-1.5 text-xs rounded-xl"
                              >
                                <Eye className="h-3.5 w-3.5" />
                                Summary
                              </Button>
                            )}
                            
                            {doc.status === "error" && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleReprocess(doc.id)}
                                className="flex items-center gap-1.5 text-xs text-amber-500 border-amber-500/20 hover:bg-amber-500/5 rounded-xl"
                              >
                                <RefreshCw className="h-3.5 w-3.5" />
                                Retry
                              </Button>
                            )}

                            <Button
                              variant="destructive"
                              size="icon-sm"
                              onClick={() => handleDelete(doc.id, doc.title)}
                              className="rounded-xl shrink-0"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Summary View Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-card border border-border rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh] animate-in scale-in duration-200">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 bg-muted/20">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 text-primary rounded-xl">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base truncate max-w-[400px]" title={selectedDoc.title}>
                    {selectedDoc.title}
                  </h3>
                  <p className="text-xs text-muted-foreground font-light mt-0.5">
                    AI Course Summary • {selectedDoc.page_count} pages
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-primary">Overview Summary</h4>
              <p className="text-sm leading-relaxed text-foreground/95 font-light bg-muted/30 border border-border/40 p-5 rounded-xl">
                {selectedDoc.summary || "Summary generation in progress."}
              </p>
              
              <div className="text-xs text-muted-foreground border-t border-border/30 pt-4 flex flex-col sm:flex-row justify-between gap-2">
                <span>Uploaded: {new Date(selectedDoc.created_at).toLocaleDateString()}</span>
                <span>Document ID: {selectedDoc.id}</span>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-border/50 bg-muted/10 flex justify-end">
              <Button onClick={() => setSelectedDoc(null)} className="rounded-xl px-5">
                Close Summary
              </Button>
            </div>
            
          </div>
        </div>
      )}
    </div>
  );
}
