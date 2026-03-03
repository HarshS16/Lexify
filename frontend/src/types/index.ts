// ── AI Output Types ───────────────────────────────────────

export interface EmotionAnalysis {
  primary_emotion: string;
  secondary_emotion: string | null;
  intensity: "low" | "medium" | "high";
  context_summary: string;
}

export interface WordAlternative {
  word: string;
  strength: "low" | "medium" | "high";
  categories: string[];
  explanation: string;
}

export interface WordSuggestionResult {
  best_fit: string;
  best_fit_explanation: string;
  best_fit_categories: string[];
  alternatives: WordAlternative[];
  analysis: EmotionAnalysis;
}

export interface RewriteChange {
  original_word: string;
  new_word: string;
  reason: string;
}

export interface RewriteResult {
  original: string;
  rewritten: string;
  changes: RewriteChange[];
  goal: string;
}

export interface WordOfTheDay {
  date: string;
  word: string;
  meaning: string;
  emotional_range: string;
  example_usage: string;
  when_to_use: string;
  when_to_avoid: string;
}

// ── Request Types ─────────────────────────────────────────

export interface SearchRequest {
  input_text: string;
  tone?: string;
  intent?: string;
}

export interface RewriteRequest {
  input_text: string;
  goal: string;
  tone?: string;
}

export interface SaveWordRequest {
  word: string;
  notes?: string;
  tags?: string[];
}

export interface FeedbackRequest {
  search_id?: string;
  word: string;
  rating: -1 | 0 | 1;
}

// ── Response Types ────────────────────────────────────────

export interface SearchResponse {
  search_id: string;
  result: WordSuggestionResult;
}

export interface SavedWord {
  id: string;
  word: string;
  notes: string | null;
  tags: string[];
  created_at: string;
}

export interface HistoryItem {
  search_id: string;
  input_text: string;
  tone: string | null;
  intent: string | null;
  best_fit_word: string | null;
  created_at: string;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
}

// ── UI Types ──────────────────────────────────────────────

export type ToneOption = "neutral" | "professional" | "casual" | "poetic" | "academic" | "empathetic";
export type IntentOption = "general expression" | "emotional expression" | "writing improvement" | "clarity";
export type RewriteGoal = "more confident" | "more polite" | "more emotionally precise" | "more professional";
export type AppMode = "search" | "rewrite";
