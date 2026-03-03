import { useState, useEffect } from "react";
import { BookOpen, Trash2, Tag } from "lucide-react";
import { api } from "../services/api";
import type { SavedWord } from "../types";
import { useToast, ToastContainer } from "../components/Toast";

export default function VocabularyPage() {
    const [words, setWords] = useState<SavedWord[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const { toasts, addToast, removeToast } = useToast();

    const fetchWords = async () => {
        setLoading(true);
        try {
            const data = await api.getSavedWords();
            setWords(data);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to load words");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWords();
    }, []);

    const handleDelete = async (id: string, word: string) => {
        try {
            await api.deleteWord(id);
            setWords((prev) => prev.filter((w) => w.id !== id));
            addToast(`"${word}" removed from vocabulary`, "success");
        } catch {
            addToast("Failed to delete word", "error");
        }
    };

    return (
        <div className="main-content">
            <div className="vocab-header">
                <div>
                    <h1>
                        <BookOpen
                            size={28}
                            style={{ display: "inline", verticalAlign: "middle", marginRight: 8, color: "var(--accent-primary-light)" }}
                        />
                        Vocabulary Bank
                    </h1>
                    <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>
                        Your personal collection of discovered words
                    </p>
                </div>
                <span style={{ color: "var(--text-tertiary)", fontSize: "0.85rem" }}>
                    {words.length} word{words.length !== 1 ? "s" : ""} saved
                </span>
            </div>

            {error && (
                <div className="error-banner">
                    <span>⚠️</span>
                    <span>{error}</span>
                </div>
            )}

            {loading && (
                <div className="loading-container">
                    <div className="loading-spinner" />
                    <p className="loading-text">Loading your vocabulary...</p>
                </div>
            )}

            {!loading && words.length === 0 && (
                <div className="empty-state" id="empty-vocabulary">
                    <div className="empty-icon">📚</div>
                    <div className="empty-title">No saved words yet</div>
                    <div className="empty-text">
                        Search for better words and save your favorites here
                    </div>
                </div>
            )}

            {!loading && words.length > 0 && (
                <div className="vocab-grid" id="vocabulary-grid">
                    {words.map((w, i) => (
                        <div
                            key={w.id}
                            className="vocab-card fade-in"
                            style={{ animationDelay: `${i * 0.05}s`, animationFillMode: "both" }}
                        >
                            <div className="vocab-word">{w.word}</div>
                            {w.notes && <div className="vocab-notes">{w.notes}</div>}
                            {w.tags && w.tags.length > 0 && (
                                <div className="vocab-tags">
                                    {w.tags.map((tag) => (
                                        <span key={tag} className="vocab-tag">
                                            <Tag size={10} style={{ marginRight: 2 }} />
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            )}
                            <div className="vocab-date">
                                Saved {new Date(w.created_at).toLocaleDateString()}
                            </div>
                            <div className="vocab-actions">
                                <button
                                    className="btn btn-ghost btn-sm"
                                    onClick={() => handleDelete(w.id, w.word)}
                                    style={{ color: "var(--accent-warm)" }}
                                >
                                    <Trash2 size={13} />
                                    Remove
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </div>
    );
}
