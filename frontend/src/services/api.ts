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

// User-friendly error messages
function friendlyError(status: number, detail: string): string {
    if (status === 429) return "Too many requests. Please wait a moment and try again.";
    if (status === 503) return "AI models are temporarily unavailable. Please try again in a few seconds.";
    if (status === 404) return "Resource not found.";
    if (detail && !detail.includes("indices") && !detail.includes("object") && !detail.includes("NoneType")) {
        return detail;
    }
    return "Something went wrong. Please try again.";
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    let res: Response;
    try {
        res = await fetch(`${API_BASE}${endpoint}`, {
            headers: { "Content-Type": "application/json" },
            ...options,
        });
    } catch {
        throw new Error("Unable to reach the server. Check your internet connection.");
    }

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "" }));
        throw new Error(friendlyError(res.status, error.detail || ""));
    }

    return res.json();
}

export const api = {
    search: (data: SearchRequest) =>
        request<SearchResponse>("/search", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    rewrite: (data: RewriteRequest) =>
        request<RewriteResult>("/rewrite", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    getWordOfTheDay: () => request<WordOfTheDay>("/word-of-the-day"),

    getSavedWords: () => request<SavedWord[]>("/saved-words"),

    saveWord: (data: SaveWordRequest) =>
        request<SavedWord>("/saved-words", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    deleteWord: (id: string) =>
        request<{ message: string }>(`/saved-words/${id}`, { method: "DELETE" }),

    submitFeedback: (data: FeedbackRequest) =>
        request<{ message: string }>("/feedback", {
            method: "POST",
            body: JSON.stringify(data),
        }),

    getHistory: (limit = 20, offset = 0) =>
        request<HistoryResponse>(`/history?limit=${limit}&offset=${offset}`),
};
