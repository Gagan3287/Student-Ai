"use client";

import { useState } from "react";
import {
  Briefcase,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  MapPin,
  Loader2,
  FileText,
  Target,
  ArrowRight,
  Code,
  Cpu,
  Database,
  Globe,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { api } from "@/lib/api";

interface AnalyzeResult {
  matched_skills: string[];
  missing_skills: string[];
  roadmap: string[];
}

const PREP_TOPICS = [
  {
    title: "Data Structures & Algorithms",
    icon: Code,
    color: "from-violet-500 to-indigo-600",
    items: [
      "Arrays, Strings, Linked Lists",
      "Stacks, Queues, Heaps",
      "Trees (BST, AVL, Trie)",
      "Graphs (BFS, DFS, Dijkstra)",
      "Dynamic Programming patterns",
    ],
    resources: [
      { label: "LeetCode", href: "https://leetcode.com" },
      { label: "NeetCode", href: "https://neetcode.io" },
    ],
  },
  {
    title: "Operating Systems",
    icon: Cpu,
    color: "from-sky-500 to-blue-600",
    items: [
      "Process management & scheduling",
      "Memory management & paging",
      "Deadlock detection & prevention",
      "File systems & I/O",
      "Concurrency & synchronisation",
    ],
    resources: [
      { label: "OSTEP Book", href: "https://pages.cs.wisc.edu/~remzi/OSTEP/" },
    ],
  },
  {
    title: "DBMS",
    icon: Database,
    color: "from-emerald-500 to-teal-600",
    items: [
      "Relational model & SQL",
      "Normalisation (1NF–BCNF)",
      "Transactions & ACID",
      "Indexing & query optimisation",
      "NoSQL overview",
    ],
    resources: [
      { label: "SQLZoo", href: "https://sqlzoo.net" },
    ],
  },
  {
    title: "Computer Networks",
    icon: Globe,
    color: "from-orange-500 to-amber-600",
    items: [
      "OSI & TCP/IP model",
      "HTTP, HTTPS, DNS, DHCP",
      "Routing protocols (OSPF, BGP)",
      "TCP vs UDP",
      "Firewalls & VPN",
    ],
    resources: [
      { label: "Beej's Networking Guide", href: "https://beej.us/guide/bgnet/" },
    ],
  },
];

export default function ResumePage() {
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalyzeResult | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeText.trim() || !jdText.trim() || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await api.post<AnalyzeResult>("/resume/analyze", {
        resume_text: resumeText,
        job_description_text: jdText,
      });
      setResult(res);
    } catch (err: any) {
      const errMsg = typeof err.detail === "string" ? err.detail : err.message || "Failed to analyze skill gap.";
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2 flex items-center gap-3">
          <Briefcase className="h-8 w-8 text-primary" />
          Resume & Skill-Gap Analyzer
        </h1>
        <p className="text-muted-foreground">
          Phase 7 Feature: Compare your resume against target job descriptions using Groq LLM to identify skill overlaps, gaps, and an actionable learning roadmap.
        </p>
      </div>

      {/* Analyzer Card */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <form onSubmit={handleAnalyze} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Resume Input */}
            <div className="space-y-2">
              <label className="text-sm font-semibold flex items-center gap-2 text-foreground">
                <FileText className="h-4 w-4 text-primary" />
                Candidate Resume Text
              </label>
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste your resume text here (skills, education, projects, experience)..."
                rows={7}
                className="w-full p-3.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all resize-y"
                required
              />
            </div>

            {/* Job Description Input */}
            <div className="space-y-2">
              <label className="text-sm font-semibold flex items-center gap-2 text-foreground">
                <Target className="h-4 w-4 text-primary" />
                Target Job Description
              </label>
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the job requirements, duties, and desired skills here..."
                rows={7}
                className="w-full p-3.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all resize-y"
                required
              />
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm font-medium flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !resumeText.trim() || !jdText.trim()}
            className="w-full py-3.5 px-6 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary/90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-md shadow-primary/20"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Analyzing Skill Gap with AI...
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                Analyze Skill Gap & Generate Roadmap
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results Display */}
      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Matched Skills */}
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6 space-y-4">
              <h3 className="text-lg font-bold text-emerald-500 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5" />
                Matched Skills ({result.matched_skills.length})
              </h3>
              {result.matched_skills.length === 0 ? (
                <p className="text-xs text-muted-foreground italic">No clear skill overlaps detected.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {result.matched_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Missing Skills */}
            <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6 space-y-4">
              <h3 className="text-lg font-bold text-amber-500 flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                Missing Skills / Gaps ({result.missing_skills.length})
              </h3>
              {result.missing_skills.length === 0 ? (
                <p className="text-xs text-muted-foreground italic">No critical skill gaps identified!</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {result.missing_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold flex items-center gap-1.5"
                    >
                      <AlertCircle className="h-3.5 w-3.5" />
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Learning Roadmap */}
          <div className="rounded-2xl border border-border bg-card p-6 space-y-4 shadow-sm">
            <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
              <MapPin className="h-5 w-5 text-primary" />
              Recommended Learning & Upskilling Roadmap
            </h3>
            <div className="space-y-3">
              {result.roadmap.map((step, i) => (
                <div
                  key={i}
                  className="flex items-start gap-4 p-4 rounded-xl bg-accent/40 border border-border/50 hover:border-primary/30 transition-all"
                >
                  <span className="h-7 w-7 rounded-lg bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center shrink-0 shadow-sm">
                    {i + 1}
                  </span>
                  <p className="text-sm text-foreground leading-relaxed pt-0.5">{step}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Core Placement Reference Topics */}
      <div className="pt-6 border-t border-border/40">
        <h2 className="text-xl font-bold mb-4">Core CS Placement Reference Topics</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {PREP_TOPICS.map((topic) => {
            const Icon = topic.icon;
            return (
              <div key={topic.title} className="rounded-2xl border border-border bg-card overflow-hidden">
                <div className={`bg-gradient-to-r ${topic.color} p-4 flex items-center gap-3`}>
                  <Icon className="h-6 w-6 text-white" />
                  <h3 className="font-bold text-white">{topic.title}</h3>
                </div>
                <div className="p-4">
                  <ul className="space-y-1.5 mb-4">
                    {topic.items.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <ChevronRight className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                  {topic.resources.map((r) => (
                    <a
                      key={r.label}
                      href={r.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline mr-3"
                    >
                      <ExternalLink className="h-3 w-3" />
                      {r.label}
                    </a>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
