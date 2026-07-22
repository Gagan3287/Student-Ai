"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Brain,
  RefreshCw,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Loader2,
  Zap,
  BookOpen,
  Calendar,
  BarChart2,
  Sparkles,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Document, Flashcard } from "@/types";

type Mode = "select" | "browse" | "review" | "done";

const QUALITY_LABELS = [
  { q: 0, label: "Blackout", color: "from-rose-600 to-red-700" },
  { q: 1, label: "Very Hard", color: "from-orange-500 to-red-500" },
  { q: 2, label: "Hard", color: "from-amber-500 to-orange-500" },
  { q: 3, label: "OK", color: "from-yellow-400 to-amber-500" },
  { q: 4, label: "Good", color: "from-emerald-400 to-green-500" },
  { q: 5, label: "Perfect", color: "from-teal-400 to-emerald-500" },
];

export default function FlashcardsPage() {
  const [mode, setMode] = useState<Mode>("select");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [reviewStart, setReviewStart] = useState<number>(0);
  const [sessionStats, setSessionStats] = useState({ correct: 0, total: 0 });

  useEffect(() => {
    api.get<{ documents: Document[] }>("/documents").then((d) =>
      setDocuments(d.documents.filter((doc) => doc.status === "ready"))
    );
  }, []);

  const loadCards = useCallback(async (doc: Document) => {
    setLoading(true);
    setError("");
    try {
      const data = await api.get<Flashcard[]>(`/flashcards?document_id=${doc.id}`);
      if (data.length === 0) {
        // Auto-generate if none exist
        await generateCards(doc, false);
      } else {
        setCards(data);
        setMode("browse");
      }
    } catch (e: any) {
      setError("Failed to load flashcards.");
    } finally {
      setLoading(false);
    }
  }, []);

  const generateCards = async (doc: Document, showLoading = true) => {
    if (showLoading) setGenerating(true);
    setError("");
    try {
      const data = await api.post<Flashcard[]>(`/flashcards/generate/${doc.id}?count=10`);
      setCards(data);
      setMode("browse");
    } catch (e: any) {
      setError(e.detail || "Failed to generate flashcards.");
    } finally {
      setGenerating(false);
    }
  };

  const selectDocument = (doc: Document) => {
    setSelectedDoc(doc);
    setCurrentIdx(0);
    setFlipped(false);
    setSessionStats({ correct: 0, total: 0 });
    loadCards(doc);
  };

  const startReview = () => {
    const dueCards = cards.filter(
      (c) => new Date(c.next_review_at) <= new Date()
    );
    if (dueCards.length === 0) {
      // Review all cards if none are due
      setCurrentIdx(0);
    } else {
      setCards(dueCards);
      setCurrentIdx(0);
    }
    setFlipped(false);
    setSessionStats({ correct: 0, total: 0 });
    setMode("review");
    setReviewStart(Date.now());
  };

  const submitReview = async (quality: number) => {
    const card = cards[currentIdx];
    const responseTime = (Date.now() - reviewStart) / 1000;
    const isCorrect = quality >= 3;

    setSessionStats((s) => ({
      correct: s.correct + (isCorrect ? 1 : 0),
      total: s.total + 1,
    }));

    try {
      await api.post(`/flashcards/${card.id}/review`, {
        quality,
        response_time_s: responseTime,
      });
    } catch {}

    if (currentIdx + 1 >= cards.length) {
      setMode("done");
    } else {
      setCurrentIdx((i) => i + 1);
      setFlipped(false);
      setReviewStart(Date.now());
    }
  };

  const currentCard = cards[currentIdx];
  const dueCount = cards.filter(
    (c) => new Date(c.next_review_at) <= new Date()
  ).length;

  // ── RENDER ─────────────────────────────────────────────────────────────────

  if (mode === "select" || !selectedDoc) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2 flex items-center gap-3">
            <Brain className="h-8 w-8 text-primary" />
            Flashcards
          </h1>
          <p className="text-muted-foreground">
            AI-generated cards with SM-2 spaced repetition scheduling
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm border border-destructive/20 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-3">Select a document to study</h2>
          {documents.length === 0 ? (
            <div className="text-center py-16 rounded-2xl border border-dashed border-border">
              <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">
                No ready documents found. Upload and process a PDF or TXT file first.
              </p>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {documents.map((doc) => (
                <button
                  key={doc.id}
                  onClick={() => selectDocument(doc)}
                  disabled={loading}
                  className="text-left p-5 rounded-2xl border border-border hover:border-primary/50 hover:bg-primary/5 transition-all duration-200 group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-semibold truncate group-hover:text-primary transition-colors">
                        {doc.title}
                      </p>
                      {doc.page_count && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {doc.page_count} pages
                        </p>
                      )}
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary shrink-0 transition-colors" />
                  </div>
                  {doc.summary && (
                    <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                      {doc.summary}
                    </p>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {loading && (
          <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            Loading flashcards…
          </div>
        )}
      </div>
    );
  }

  if (generating) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-muted-foreground">
        <div className="relative">
          <Sparkles className="h-12 w-12 text-primary animate-pulse" />
        </div>
        <p className="text-lg font-medium">Generating flashcards with AI…</p>
        <p className="text-sm">This may take 10–20 seconds</p>
      </div>
    );
  }

  if (mode === "browse") {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <button
              onClick={() => { setMode("select"); setSelectedDoc(null); setCards([]); }}
              className="text-sm text-muted-foreground hover:text-foreground mb-1 flex items-center gap-1"
            >
              ← Back
            </button>
            <h1 className="text-2xl font-bold">{selectedDoc.title}</h1>
            <p className="text-muted-foreground text-sm">
              {cards.length} cards · {dueCount} due for review
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => generateCards(selectedDoc)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-border hover:bg-accent text-sm transition-all"
            >
              <Sparkles className="h-4 w-4" />
              Regenerate
            </button>
            <button
              onClick={startReview}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-all"
            >
              <Zap className="h-4 w-4" />
              Start Review
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {cards.map((card, i) => {
            const isDue = new Date(card.next_review_at) <= new Date();
            return (
              <div
                key={card.id}
                className="p-5 rounded-2xl border border-border bg-card"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground">{card.question}</p>
                    <p className="text-sm text-muted-foreground mt-2 line-clamp-2">{card.answer}</p>
                  </div>
                  <div className="shrink-0 flex flex-col items-end gap-1">
                    {isDue ? (
                      <span className="text-xs bg-amber-500/15 text-amber-600 dark:text-amber-400 px-2 py-0.5 rounded-full font-medium">
                        Due
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">
                        In {card.sm2_interval}d
                      </span>
                    )}
                    {card.retention_probability !== null && (
                      <span className="text-xs text-muted-foreground">
                        {Math.round((card.retention_probability ?? 0) * 100)}% recall
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  if (mode === "done") {
    const pct = sessionStats.total > 0
      ? Math.round((sessionStats.correct / sessionStats.total) * 100)
      : 0;
    return (
      <div className="flex flex-col items-center justify-center h-full gap-6 p-8">
        <div className="text-center">
          <div className="h-24 w-24 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-500/20">
            <CheckCircle2 className="h-12 w-12 text-white" />
          </div>
          <h2 className="text-3xl font-bold mb-2">Session Complete!</h2>
          <p className="text-muted-foreground">
            {sessionStats.correct}/{sessionStats.total} correct · {pct}% accuracy
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => { setMode("browse"); setCurrentIdx(0); }}
            className="px-6 py-2.5 rounded-xl border border-border hover:bg-accent text-sm font-medium transition-all"
          >
            Back to Cards
          </button>
          <button
            onClick={startReview}
            className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-all"
          >
            Review Again
          </button>
        </div>
      </div>
    );
  }

  // REVIEW mode
  if (!currentCard) return null;

  return (
    <div className="flex flex-col items-center justify-center min-h-full p-8 gap-6">
      {/* Progress */}
      <div className="w-full max-w-lg">
        <div className="flex items-center justify-between text-sm text-muted-foreground mb-2">
          <span>Card {currentIdx + 1} of {cards.length}</span>
          <span>{sessionStats.correct} correct</span>
        </div>
        <div className="h-1.5 rounded-full bg-border overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all duration-300"
            style={{ width: `${((currentIdx) / cards.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Card */}
      <div
        className="w-full max-w-lg cursor-pointer select-none"
        onClick={() => setFlipped((f) => !f)}
        style={{ perspective: "1000px" }}
      >
        <div
          className="relative w-full transition-transform duration-500"
          style={{
            transformStyle: "preserve-3d",
            transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
            minHeight: "260px",
          }}
        >
          {/* Front */}
          <div
            className="absolute inset-0 rounded-2xl border border-border bg-card p-8 flex flex-col justify-center"
            style={{ backfaceVisibility: "hidden" }}
          >
            <p className="text-xs font-semibold text-primary uppercase tracking-widest mb-4">Question</p>
            <p className="text-xl font-semibold text-foreground leading-relaxed">
              {currentCard.question}
            </p>
            <p className="text-xs text-muted-foreground mt-6 text-center">
              Tap to reveal answer
            </p>
          </div>
          {/* Back */}
          <div
            className="absolute inset-0 rounded-2xl border border-primary/30 bg-primary/5 p-8 flex flex-col justify-center"
            style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
          >
            <p className="text-xs font-semibold text-primary uppercase tracking-widest mb-4">Answer</p>
            <p className="text-lg text-foreground leading-relaxed">
              {currentCard.answer}
            </p>
          </div>
        </div>
      </div>

      {/* Quality buttons */}
      {flipped && (
        <div className="w-full max-w-lg">
          <p className="text-sm text-center text-muted-foreground mb-3">
            How well did you recall this?
          </p>
          <div className="grid grid-cols-6 gap-2">
            {QUALITY_LABELS.map(({ q, label, color }) => (
              <button
                key={q}
                onClick={() => submitReview(q)}
                className={`flex flex-col items-center gap-1 py-3 px-1 rounded-xl bg-gradient-to-b ${color} text-white font-bold text-lg hover:scale-105 active:scale-95 transition-transform shadow-md`}
                title={label}
              >
                {q}
                <span className="text-[9px] font-normal opacity-80 leading-tight text-center">
                  {label}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
