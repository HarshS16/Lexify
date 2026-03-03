import type {
    SearchRequest,
    SearchResponse,
    RewriteRequest,
    RewriteResult,
    WordOfTheDay,
    SaveWordRequest,
    SavedWord,
    FeedbackRequest,
    HistoryResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Something went wrong" }));
        throw new Error(error.detail || `API Error: ${res.status}`);
    }

    return res.json();
}

export const api = {
    // Word Search
    search: (data: SearchRequest) =>
        request<SearchResponse>("/search", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    // Rewrite
    rewrite: (data: RewriteRequest) =>
        request<RewriteResult>("/rewrite", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    // Word of the Day
    getWordOfTheDay: () => request<WordOfTheDay>("/word-of-the-day"),

    // Saved Words
    getSavedWords: () => request<SavedWord[]>("/saved-words"),
    saveWord: (data: SaveWordRequest) =>
        request<SavedWord>("/saved-words", {
            method: "POST",
            body: JSON.stringify(data),
        }),
    deleteWord: (id: string) =>
        request<{ message: string }>(`/saved-words/${id}`, { method: "DELETE" }),

    // Feedback
    submitFeedback: (data: FeedbackRequest) =>
        request<{ message: string }>("/feedback", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    // History
    getHistory: (limit = 20, offset = 0) =>
        request<HistoryResponse>(`/history?limit=${limit}&offset=${offset}`),
};
