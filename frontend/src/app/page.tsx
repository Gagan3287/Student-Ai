import type { Metadata } from "next";
import LandingPageClient from "@/components/landing/LandingPageClient";

export const metadata: Metadata = {
  title: "StudyMate AI | AI Study Companion & Exam Prep",
  description:
    "Upload your notes, textbooks, and syllabus to get instant auto-summaries, custom quizzes, spaced-repetition flashcards, and a dedicated chatbot.",
};

export default function Home() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: "StudyMate AI",
    description:
      "An AI-powered study companion that helps engineering students retain information better through active recall, spaced repetition, and custom knowledge graphs.",
    applicationCategory: "EducationalApplication",
    operatingSystem: "All",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <LandingPageClient />
    </>
  );
}
