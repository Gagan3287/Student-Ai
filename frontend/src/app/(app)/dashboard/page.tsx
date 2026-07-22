"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Brain,
  MessageSquare,
  TrendingUp,
  Award,
  ChevronRight,
  Upload,
  Calendar,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { DashboardStats } from "@/types";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<DashboardStats>("/dashboard/stats")
      .then((data) => {
        setStats(data);
        setError("");
      })
      .catch((err) => {
        setError(err.detail || "Failed to load dashboard stats");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-10 w-48 bg-muted rounded-lg" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-muted rounded-2xl" />
          ))}
        </div>
        <div className="h-64 bg-muted rounded-2xl" />
      </div>
    );
  }

  const statCards = [
    {
      name: "Revision Streak",
      value: `${stats?.revision_streak || 0} days`,
      desc: "Consecutive study days",
      icon: TrendingUp,
      color: "text-amber-500 bg-amber-500/10",
    },
    {
      name: "Due Flashcards",
      value: stats?.due_cards_count || 0,
      desc: "Ready for SM-2 review",
      icon: Brain,
      color: "text-primary bg-primary/10",
    },
    {
      name: "My Notes",
      value: stats?.total_documents || 0,
      desc: "Uploaded study materials",
      icon: FileText,
      color: "text-indigo-500 bg-indigo-500/10",
    },
    {
      name: "Average Quiz Score",
      value: stats?.average_quiz_score !== null && stats?.average_quiz_score !== undefined
        ? `${Math.round(stats.average_quiz_score)}%`
        : "N/A",
      desc: "Performance across MCQs",
      icon: Award,
      color: "text-emerald-500 bg-emerald-500/10",
    },
  ];

  return (
    <div className="space-y-10">
      {/* Welcome header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1 font-light">Track your learning progress and upcoming reviews.</p>
        </div>
        <Link
          href="/documents"
          className="inline-flex items-center gap-2 h-11 bg-primary text-primary-foreground px-5 rounded-xl font-medium shadow-lg hover:shadow-primary/10 hover:scale-[1.01] active:scale-[0.99] transition-all duration-200"
        >
          <Upload className="h-4 w-4" />
          Upload Notes
        </Link>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl bg-destructive/10 p-4 border border-destructive/20 text-sm text-destructive">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.name}
              className="bg-card border border-border/50 rounded-2xl p-6 shadow-sm flex items-center justify-between"
            >
              <div className="space-y-1">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{card.name}</p>
                <p className="text-2xl font-bold tracking-tight text-foreground">{card.value}</p>
                <p className="text-xs text-muted-foreground font-light">{card.desc}</p>
              </div>
              <div className={`p-3.5 rounded-xl ${card.color} shrink-0`}>
                <Icon className="h-6 w-6" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Action Boards */}
      <div className="grid md:grid-cols-2 gap-8">
        {/* Card 1: Review Flashcards */}
        <div className="border border-border/50 bg-card rounded-2xl p-8 flex flex-col justify-between shadow-sm relative overflow-hidden group">
          <div className="space-y-4 relative z-10">
            <div className="p-3 bg-primary/10 text-primary w-fit rounded-xl">
              <Brain className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold">Review Flashcards</h3>
              <p className="text-sm text-muted-foreground mt-2 font-light leading-relaxed">
                Study vocabulary, core formulas, and key points using our spaced repetition schedule. Predicts your forgetting threshold using Half-Life regression.
              </p>
            </div>
          </div>
          <div className="mt-8 relative z-10">
            <Link
              href="/flashcards"
              className="inline-flex items-center gap-2 text-sm font-semibold text-primary group-hover:gap-3.5 transition-all duration-200"
            >
              Start Studying Due Cards
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        </div>

        {/* Card 2: AI Doubt Solver */}
        <div className="border border-border/50 bg-card rounded-2xl p-8 flex flex-col justify-between shadow-sm relative overflow-hidden group">
          <div className="space-y-4 relative z-10">
            <div className="p-3 bg-primary/10 text-primary w-fit rounded-xl">
              <MessageSquare className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold">RAG Doubt Solver</h3>
              <p className="text-sm text-muted-foreground mt-2 font-light leading-relaxed">
                Connect with our Retrieval-Augmented Generation chatbot to ask questions. Cites sources directly from your notes to ensure accuracy.
              </p>
            </div>
          </div>
          <div className="mt-8 relative z-10">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 text-sm font-semibold text-primary group-hover:gap-3.5 transition-all duration-200"
            >
              Ask a Doubt
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* Spaced repetition algorithm info block */}
      <div className="bg-primary/5 border border-primary/20 rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center gap-6 justify-between">
        <div className="space-y-2">
          <h4 className="font-bold text-lg text-primary flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Spaced Repetition Scheduler Active
          </h4>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-3xl font-light">
            We use Piotr Wozniak&apos;s classic <strong>SM-2 algorithm</strong> combined with a <strong>self-trained Half-Life regression model</strong> to dynamically determine your revision dates. This system optimizes active recall intervals, moving reviewed items to longer frequencies as memory stabilizes.
          </p>
        </div>
      </div>
    </div>
  );
}
