"use client";

import { useEffect, useState } from "react";
import {
  HelpCircle,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Loader2,
  Sparkles,
  AlertCircle,
  BookOpen,
  BarChart2,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { Document, MCQQuestion, QuizAttempt } from "@/types";

type Mode = "select" | "quiz" | "results";

export default function QuizzesPage() {
  const [mode, setMode] = useState<Mode>("select");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [questions, setQuestions] = useState<MCQQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [result, setResult] = useState<QuizAttempt | null>(null);
  const [loadingQuiz, setLoadingQuiz] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const COUNT = 5;

  useEffect(() => {
    api
      .get<{ documents: Document[] }>("/documents")
      .then((d) => setDocuments(d.documents.filter((doc) => doc.status === "ready")));
  }, []);

  const loadQuiz = async (doc: Document) => {
    setSelectedDoc(doc);
    setLoadingQuiz(true);
    setError("");
    setAnswers({});
    setResult(null);
    try {
      const data = await api.get<{ document_id: string; questions: MCQQuestion[] }>(
        `/quizzes/${doc.id}?count=${COUNT}`
      );
      setQuestions(data.questions);
      setMode("quiz");
    } catch (e: any) {
      setError(e.detail || "Failed to load quiz. Please try again.");
    } finally {
      setLoadingQuiz(false);
    }
  };

  const submitQuiz = async () => {
    if (!selectedDoc) return;
    setSubmitting(true);
    setError("");
    try {
      const res = await api.post<QuizAttempt>(
        `/quizzes/${selectedDoc.id}/attempt?count=${COUNT}`,
        {
          answers: Object.entries(answers).map(([qi, chosen]) => ({
            question_index: parseInt(qi),
            chosen_option: chosen,
          })),
        }
      );
      setResult(res);
      setMode("results");
    } catch (e: any) {
      setError(e.detail || "Failed to submit quiz.");
    } finally {
      setSubmitting(false);
    }
  };

  const allAnswered = questions.length > 0 && Object.keys(answers).length === questions.length;

  // ── SELECT MODE ────────────────────────────────────────────────────────────
  if (mode === "select") {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2 flex items-center gap-3">
            <HelpCircle className="h-8 w-8 text-primary" />
            Practice Quizzes
          </h1>
          <p className="text-muted-foreground">
            AI-generated MCQs to test your understanding of study material
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm border border-destructive/20 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {documents.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-dashed border-border">
            <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">
              No ready documents found. Upload and process a file first.
            </p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {documents.map((doc) => (
              <button
                key={doc.id}
                onClick={() => loadQuiz(doc)}
                disabled={loadingQuiz}
                className="text-left p-5 rounded-2xl border border-border hover:border-primary/50 hover:bg-primary/5 transition-all duration-200 group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-semibold truncate group-hover:text-primary transition-colors">
                      {doc.title}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {COUNT} questions · Multiple choice
                    </p>
                  </div>
                  {loadingQuiz ? (
                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground shrink-0" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary shrink-0 transition-colors" />
                  )}
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
    );
  }

  // ── QUIZ MODE ──────────────────────────────────────────────────────────────
  if (mode === "quiz") {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <button
              onClick={() => { setMode("select"); setSelectedDoc(null); }}
              className="text-sm text-muted-foreground hover:text-foreground mb-1"
            >
              ← Back
            </button>
            <h1 className="text-xl font-bold">{selectedDoc?.title}</h1>
            <p className="text-sm text-muted-foreground">
              {questions.length} questions · Answer all to submit
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm border border-destructive/20 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        <div className="space-y-6 mb-8">
          {questions.map((q) => (
            <div key={q.index} className="p-5 rounded-2xl border border-border bg-card">
              <p className="font-semibold mb-4">
                <span className="text-primary mr-2">Q{q.index + 1}.</span>
                {q.question}
              </p>
              <div className="space-y-2">
                {q.options.map((opt) => (
                  <button
                    key={opt.index}
                    onClick={() =>
                      setAnswers((a) => ({ ...a, [q.index]: opt.index }))
                    }
                    className={`w-full text-left px-4 py-3 rounded-xl border text-sm transition-all duration-150 ${
                      answers[q.index] === opt.index
                        ? "border-primary bg-primary/10 text-foreground font-medium"
                        : "border-border hover:border-primary/40 hover:bg-accent/50 text-muted-foreground"
                    }`}
                  >
                    <span className="font-mono font-bold mr-2 text-primary">
                      {String.fromCharCode(65 + opt.index)}.
                    </span>
                    {opt.text}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={submitQuiz}
          disabled={!allAnswered || submitting}
          className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/90 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
        >
          {submitting ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <>
              Submit Quiz
              <ChevronRight className="h-5 w-5" />
            </>
          )}
        </button>
        {!allAnswered && (
          <p className="text-center text-xs text-muted-foreground mt-2">
            Answer all {questions.length} questions to submit
          </p>
        )}
      </div>
    );
  }

  // ── RESULTS MODE ───────────────────────────────────────────────────────────
  if (mode === "results" && result) {
    const pct = result.percentage;
    const grade =
      pct >= 90 ? "Excellent!" : pct >= 70 ? "Good job!" : pct >= 50 ? "Keep practicing!" : "Needs work";
    const gradeColor =
      pct >= 90 ? "text-emerald-500" : pct >= 70 ? "text-blue-500" : pct >= 50 ? "text-amber-500" : "text-rose-500";

    return (
      <div className="p-8 max-w-2xl mx-auto">
        {/* Score card */}
        <div className="rounded-2xl border border-border bg-card p-8 text-center mb-6">
          <p className={`text-5xl font-extrabold mb-2 ${gradeColor}`}>{pct}%</p>
          <p className="text-xl font-semibold mb-1">{grade}</p>
          <p className="text-muted-foreground text-sm">
            {result.score} out of {result.total} correct
          </p>
        </div>

        {/* Per-question breakdown */}
        <div className="space-y-4 mb-6">
          {result.results.map((r) => (
            <div
              key={r.question_index}
              className={`p-4 rounded-2xl border ${
                r.is_correct
                  ? "border-emerald-500/30 bg-emerald-500/5"
                  : "border-rose-500/30 bg-rose-500/5"
              }`}
            >
              <div className="flex items-start gap-3">
                {r.is_correct ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 text-rose-500 shrink-0 mt-0.5" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm">{r.question}</p>
                  {!r.is_correct && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Your answer:{" "}
                      <span className="text-rose-500 font-medium">
                        {String.fromCharCode(65 + r.chosen_option)}
                      </span>{" "}
                      · Correct:{" "}
                      <span className="text-emerald-500 font-medium">
                        {String.fromCharCode(65 + r.correct_option)}
                      </span>
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => { setMode("select"); setSelectedDoc(null); setResult(null); }}
            className="flex-1 py-2.5 rounded-xl border border-border hover:bg-accent text-sm font-medium transition-all"
          >
            Choose Different Doc
          </button>
          <button
            onClick={() => selectedDoc && loadQuiz(selectedDoc)}
            className="flex-1 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return null;
}
