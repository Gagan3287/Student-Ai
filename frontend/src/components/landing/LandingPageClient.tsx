"use client";

import Link from "next/link";
import {
  GraduationCap,
  Brain,
  MessageSquare,
  Network,
  FileText,
  BookOpen,
  Upload,
  Zap,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import { motion, type Variants } from "framer-motion";
import HeroIllustration from "@/components/landing/HeroIllustration";
import ThemeToggle from "@/components/layout/ThemeToggle";
import { useTypewriter } from "@/hooks/useTypewriter";

// ─── Animation variants ───────────────────────────────────────────────────────
const fadeUp: Variants = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

const staggerContainer: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const TYPEWRITER_WORDS = [
  "AI Study Companion",
  "Exam Prep Partner",
  "Doubt Solver",
  "Flashcard Engine",
];

const FEATURES = [
  {
    icon: FileText,
    title: "Note Summarization",
    description:
      "Upload dense textbooks, lecture notes, or codebases. Get clean summaries and outlines highlighting core formulas and concepts.",
  },
  {
    icon: Brain,
    title: "Adaptive Spaced-Repetition",
    description:
      "Our self-trained memory regression algorithm predicts when you will forget a concept, scheduling card reviews at optimal intervals.",
  },
  {
    icon: MessageSquare,
    title: "Grounded RAG Chatbot",
    description:
      "Ask doubts and get instant answers with page citations. The chatbot is scoped strictly to your uploads so it never hallucinates facts.",
  },
  {
    icon: Network,
    title: "Concept Knowledge Graph",
    description:
      "Visualize how different topics link across multiple documents. Click on linked concepts to reveal their shared context.",
  },
  {
    icon: BookOpen,
    title: "Syllabus & Quiz Engine",
    description:
      "Generate randomized multiple-choice tests directly from your notes to evaluate your retention and prepare for viva examinations.",
  },
  {
    icon: GraduationCap,
    title: "Placement Skill Gap Roadmap",
    description:
      "Upload your engineering resume alongside a target job description. Instantly identify skill gaps and generate a step-by-step learning path.",
  },
];

const HOW_STEPS = [
  {
    icon: Upload,
    step: "01",
    title: "Upload Your Notes",
    description:
      "Drag in any PDF or text file — textbook chapters, lecture slides, or your own notes.",
  },
  {
    icon: Zap,
    step: "02",
    title: "AI Processes & Indexes",
    description:
      "Gemini embeddings index your content. Groq LLM extracts summaries, flashcards, and concept maps automatically.",
  },
  {
    icon: CheckCircle2,
    step: "03",
    title: "Study Smarter",
    description:
      "Chat with your notes, review spaced flashcards, take quizzes, and track your retention — all in one dashboard.",
  },
];

export default function LandingPageClient() {
  const typedWord = useTypewriter(TYPEWRITER_WORDS, 70, 40, 1800);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col selection:bg-primary/20">

      {/* ── Navbar ──────────────────────────────────────────────────────────── */}
      <header className="border-b border-border/40 bg-background/95 backdrop-blur-md sticky top-0 z-50 transition-all duration-300">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <GraduationCap className="h-7 w-7 text-primary animate-pulse" />
            <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-primary via-indigo-500 to-violet-500 bg-clip-text text-transparent">
              StudyMate AI
            </span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
            <a href="#features" className="hover:text-foreground transition-colors duration-200">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-foreground transition-colors duration-200">
              How it works
            </a>
          </nav>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link
              href="/login"
              className="text-sm font-medium hover:text-primary transition-colors duration-200"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="inline-flex h-9 items-center justify-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground shadow-lg hover:shadow-primary/20 transition-all duration-200 hover:scale-[1.02]"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero Section ────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden pt-20 pb-24 md:pt-28 md:pb-32 bg-gradient-to-b from-primary/5 via-background to-background">
        {/* Decorative blobs */}
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-primary/5 blur-3xl pointer-events-none" />
        <div className="absolute -top-16 -right-24 w-80 h-80 rounded-full bg-violet-500/5 blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-16">
            {/* Left — text */}
            <motion.div
              className="flex-1 flex flex-col items-center lg:items-start text-center lg:text-left"
              initial="hidden"
              animate="visible"
              variants={staggerContainer}
            >
              <motion.div
                variants={fadeUp}
                className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-xs font-semibold text-primary mb-6"
              >
                <Brain className="h-3.5 w-3.5" />
                For Engineering &amp; CSE Students
              </motion.div>

              <motion.h1
                variants={fadeUp}
                className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight max-w-2xl leading-tight"
              >
                Stop Cramming.{" "}
                <span className="block mt-1">Start Retaining.</span>
                <span className="block mt-2">
                  Meet Your{" "}
                  <span className="bg-gradient-to-r from-primary via-indigo-500 to-violet-500 bg-clip-text text-transparent">
                    {typedWord}
                    <span className="inline-block w-0.5 h-[0.85em] ml-0.5 bg-primary align-middle animate-pulse" />
                  </span>
                </span>
              </motion.h1>

              <motion.p
                variants={fadeUp}
                className="mt-6 text-lg sm:text-xl text-muted-foreground max-w-xl font-light leading-relaxed"
              >
                Upload your PDFs, class notes, or syllabus. Get instant auto-summaries,
                custom quizzes, spaced-repetition flashcards, and a dedicated chatbot
                that knows your notes inside-out.
              </motion.p>

              <motion.div
                variants={fadeUp}
                className="mt-10 flex flex-col sm:flex-row gap-4 items-center w-full max-w-md"
              >
                <Link
                  href="/signup"
                  className="w-full sm:w-auto inline-flex h-12 items-center justify-center rounded-xl bg-primary px-8 text-base font-semibold text-primary-foreground shadow-xl hover:shadow-primary/25 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
                >
                  Create Free Account
                </Link>
                <a
                  href="#features"
                  className="w-full sm:w-auto inline-flex h-12 items-center justify-center rounded-xl border border-border bg-card px-8 text-base font-semibold text-foreground hover:bg-accent transition-colors duration-200 gap-2"
                >
                  Explore Features
                  <ArrowRight className="h-4 w-4" />
                </a>
              </motion.div>
            </motion.div>

            {/* Right — illustration */}
            <motion.div
              className="flex-1 flex justify-center lg:justify-end w-full max-w-md lg:max-w-none"
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.65, ease: "easeOut", delay: 0.15 }}
            >
              <div className="relative w-full max-w-[420px]">
                {/* Glow ring */}
                <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-primary/15 via-indigo-500/10 to-violet-500/15 blur-2xl" />
                <HeroIllustration className="relative w-full drop-shadow-2xl" />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── Features Grid ───────────────────────────────────────────────────── */}
      <section id="features" className="py-24 border-y border-border/40 bg-card/20">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            className="text-center max-w-3xl mx-auto mb-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-80px" }}
            variants={fadeUp}
          >
            <h2 className="text-3xl font-bold tracking-tight">
              Everything You Need for Exams &amp; Placements
            </h2>
            <p className="mt-4 text-muted-foreground">
              A comprehensive toolkit that helps you learn faster, test your knowledge, and close your skill gaps.
            </p>
          </motion.div>

          <motion.div
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-8"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-60px" }}
            variants={staggerContainer}
          >
            {FEATURES.map(({ icon: Icon, title, description }) => (
              <motion.div
                key={title}
                variants={fadeUp}
                className="border border-border/50 bg-card rounded-2xl p-8 hover:border-primary/30 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5 group"
              >
                <div className="p-3 bg-primary/10 text-primary w-fit rounded-xl group-hover:scale-110 transition-transform duration-300">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="mt-6 text-xl font-semibold">{title}</h3>
                <p className="mt-3 text-sm text-muted-foreground font-light leading-relaxed">
                  {description}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── How It Works ────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            className="text-center max-w-2xl mx-auto mb-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-80px" }}
            variants={fadeUp}
          >
            <h2 className="text-3xl font-bold tracking-tight">
              Up and Running in 60 Seconds
            </h2>
            <p className="mt-4 text-muted-foreground">
              No complicated setup. Just upload and let the AI do the heavy lifting.
            </p>
          </motion.div>

          <motion.div
            className="grid md:grid-cols-3 gap-8 relative"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-60px" }}
            variants={staggerContainer}
          >
            {HOW_STEPS.map(({ icon: Icon, step, title, description }, i) => (
              <motion.div
                key={step}
                variants={fadeUp}
                className="relative flex flex-col items-center text-center"
              >
                {/* Connector line */}
                {i < HOW_STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-10 left-[calc(50%+52px)] right-[calc(-50%+52px)] h-0.5 bg-gradient-to-r from-primary/30 to-primary/10" />
                )}
                <div className="relative mb-6">
                  <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-primary/15 to-violet-500/15 border border-primary/20 flex items-center justify-center">
                    <Icon className="h-9 w-9 text-primary" />
                  </div>
                  <span className="absolute -top-2 -right-2 h-7 w-7 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center shadow-md">
                    {step}
                  </span>
                </div>
                <h3 className="text-xl font-semibold mb-3">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── CTA Banner ──────────────────────────────────────────────────────── */}
      <motion.section
        className="py-20 bg-gradient-to-br from-primary via-indigo-600 to-violet-600 relative overflow-hidden"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-60px" }}
        variants={fadeUp}
      >
        {/* Dot grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />
        <div className="max-w-3xl mx-auto px-6 text-center relative z-10">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Your notes deserve an AI that actually reads them.
          </h2>
          <p className="text-lg text-white/80 mb-8 font-light">
            Join engineering students studying with an AI that knows your exact syllabus.
          </p>
          <Link
            href="/signup"
            className="inline-flex items-center justify-center rounded-xl bg-white text-primary px-10 py-3.5 text-base font-bold shadow-xl hover:shadow-2xl transition-all duration-200 hover:scale-[1.03] active:scale-[0.98] gap-2"
          >
            Start for Free Today
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </motion.section>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="mt-auto border-t border-border/40 py-12 bg-background">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-primary" />
            <span className="font-semibold text-sm">StudyMate AI © 2026</span>
          </div>
          <div className="flex gap-8 text-sm text-muted-foreground">
            <a
              href="https://aistudio.google.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-foreground transition-colors duration-200"
            >
              Gemini API
            </a>
            <a
              href="https://console.groq.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-foreground transition-colors duration-200"
            >
              Groq API
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
