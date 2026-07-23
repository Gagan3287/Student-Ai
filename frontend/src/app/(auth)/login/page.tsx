"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { GraduationCap, Lock, Mail, Loader2, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { useTypewriter } from "@/hooks/useTypewriter";
import HeroIllustration from "@/components/landing/HeroIllustration";

const TYPEWRITER_WORDS = [
  "Study Smarter.",
  "Retain Longer.",
  "Ace Your Exams.",
];

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const typedWord = useTypewriter(TYPEWRITER_WORDS, 60, 40, 2000);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await api.post<{ access_token: string }>("/auth/login", {
        email,
        password,
      });
      setToken(response.access_token);
      router.push(redirect);
      router.refresh();
    } catch (err: any) {
      setError(err.detail || err.message || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col lg:flex-row selection:bg-primary/20">
      {/* ── Left Column: Brand Panel ────────────────────────────────────────── */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-primary via-indigo-600 to-violet-600 flex-col justify-between p-12 text-white">
        {/* Decorative blobs */}
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-white/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-black/10 blur-3xl pointer-events-none" />
        
        {/* Dot pattern overlay */}
        <div
          className="absolute inset-0 opacity-[0.05] pointer-events-none"
          style={{
            backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />

        <div className="relative z-10">
          <Link href="/" className="inline-flex items-center gap-2 mb-12 hover:opacity-90 transition-opacity">
            <GraduationCap className="h-8 w-8 text-white" />
            <span className="font-extrabold text-2xl tracking-tight">
              StudyMate AI
            </span>
          </Link>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-md"
          >
            <h1 className="text-4xl font-bold leading-tight mb-4">
              Welcome back to your study hub.
              <br />
              <span className="text-white/90 font-extrabold h-12 block mt-2">
                {typedWord}
                <span className="inline-block w-0.5 h-[0.8em] ml-1 bg-white align-middle animate-pulse" />
              </span>
            </h1>
            <p className="text-white/80 text-lg font-light leading-relaxed">
              Pick up where you left off. Review your due flashcards and ace your upcoming exams.
            </p>
          </motion.div>
        </div>

        <motion.div 
          className="relative z-10 w-full max-w-sm self-center drop-shadow-2xl opacity-90"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <HeroIllustration />
        </motion.div>

        <div className="relative z-10 text-white/60 text-sm">
          © {new Date().getFullYear()} StudyMate AI. All rights reserved.
        </div>
      </div>

      {/* ── Right Column: Form ────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm lg:max-w-md">
          {/* Mobile Header (Hidden on Desktop) */}
          <div className="lg:hidden flex flex-col items-center mb-10">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <GraduationCap className="h-10 w-10 text-primary animate-pulse" />
              <span className="font-extrabold text-2xl tracking-tight bg-gradient-to-r from-primary via-indigo-500 to-violet-500 bg-clip-text text-transparent">
                StudyMate AI
              </span>
            </Link>
            <h2 className="text-center text-3xl font-extrabold tracking-tight text-foreground">
              Welcome back
            </h2>
            <p className="mt-2 text-center text-sm text-muted-foreground">
              Or{" "}
              <Link href="/signup" className="font-medium text-primary hover:underline">
                create a new account
              </Link>
            </p>
          </div>

          {/* Desktop Header */}
          <div className="hidden lg:block mb-10">
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
              Welcome back
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Don't have an account?{" "}
              <Link href="/signup" className="font-medium text-primary hover:underline">
                Sign up for free
              </Link>
            </p>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="bg-card py-8 px-6 sm:px-10 border border-border/50 shadow-2xl shadow-primary/5 rounded-3xl"
          >
            <form className="space-y-6" onSubmit={handleSubmit}>
              {error && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="rounded-xl bg-destructive/10 p-3.5 text-sm text-destructive border border-destructive/20 font-medium flex items-start gap-2"
                >
                  <svg className="h-5 w-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{error}</span>
                </motion.div>
              )}

              <div className="space-y-4">
                <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
                  <label htmlFor="email" className="block text-sm font-medium text-muted-foreground mb-1.5">
                    Email address
                  </label>
                  <div className="relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-muted-foreground">
                      <Mail className="h-4.5 w-4.5" />
                    </div>
                    <input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="block w-full pl-11 pr-4 py-2.5 border border-border bg-background rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm transition-all duration-200"
                      placeholder="name@university.edu"
                    />
                  </div>
                </motion.div>

                <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}>
                  <label htmlFor="password" className="block text-sm font-medium text-muted-foreground mb-1.5">
                    Password
                  </label>
                  <div className="relative rounded-xl shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-muted-foreground">
                      <Lock className="h-4.5 w-4.5" />
                    </div>
                    <input
                      id="password"
                      name="password"
                      type="password"
                      autoComplete="current-password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="block w-full pl-11 pr-4 py-2.5 border border-border bg-background rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm transition-all duration-200"
                      placeholder="••••••••"
                    />
                  </div>
                </motion.div>
              </div>

              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-primary-foreground bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 transition-all duration-200 group"
                >
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <>
                      Sign In
                      <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-200" />
                    </>
                  )}
                </button>
              </motion.div>
            </form>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-background flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
