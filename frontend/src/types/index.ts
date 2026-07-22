export interface User {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface Document {
  id: string;
  title: string;
  file_name: string | null;
  content_type: string | null;
  page_count: number | null;
  summary: string | null;
  status: 'pending' | 'processing' | 'ready' | 'error';
  created_at: string;
}

export interface Flashcard {
  id: string;
  document_id: string;
  question: string;
  answer: string;
  difficulty: number;
  sm2_interval: number;
  next_review_at: string;
  retention_probability: number | null;
  review_count: number;
  correct_count: number;
}

export interface MCQOption {
  index: number;
  text: string;
}

export interface MCQQuestion {
  index: number;
  question: string;
  options: MCQOption[];
}

export interface QuizAttemptResult {
  question_index: number;
  question: string;
  chosen_option: number;
  correct_option: number;
  is_correct: boolean;
}

export interface QuizAttempt {
  id: string;
  score: number;
  total: number;
  percentage: number;
  results: QuizAttemptResult[];
  attempted_at: string;
}

export interface SourceChunk {
  chunk_id: string;
  page_number: number | null;
  excerpt: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  source_chunks: SourceChunk[] | null;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  document_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConceptNode {
  id: string;
  name: string;
  document_id: string;
  document_title: string | null;
}

export interface ConceptEdge {
  source: string;
  target: string;
  label: string | null;
}

export interface GraphData {
  nodes: ConceptNode[];
  edges: ConceptEdge[];
}

export interface DashboardStats {
  revision_streak: number;
  due_cards_count: number;
  total_documents: number;
  average_quiz_score: number | null;
}
