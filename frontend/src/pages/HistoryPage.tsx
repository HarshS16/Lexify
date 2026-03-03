import { useState, useEffect } from "react";
import { Clock, ArrowRight } from "lucide-react";
import { api } from "../services/api";
import type { HistoryItem } from "../types";

export default function HistoryPage() {
    const [items, setItems] = useState<HistoryItem[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [page, setPage] = useState(0);
    const limit = 20;

    const fetchHistory = async (offset: number) => {
        setLoading(true);
        try {
            const data = await api.getHistory(limit, offset);
            setItems(data.items);
            setTotal(data.total);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to load history");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory(page * limit);
    }, [page]);

    const totalPages = Math.ceil(total / limit);

    return (
        <div className="main-content">
            <div className="page-header">
                <h1>
                    <Clock
                        size={28}
                        style={{ display: "inline", verticalAlign: "middle", marginRight: 8, color: "var(--accent-secondary-light)" }}
                    />
                    Search History
                </h1>
                <p>{total} total searches</p>
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
                    <p className="loading-text">Loading history...</p>
                </div>
            )}

            {!loading && items.length === 0 && (
                <div className="empty-state">
                    <div className="empty-icon">🕐</div>
                    <div className="empty-title">No search history yet</div>
                    <div className="empty-text">
                        Your searches will appear here
                    </div>
                </div>
            )}

            {!loading && items.length > 0 && (
                <>
                    <div className="history-list" id="history-list">
                        {items.map((item, i) => (
                            <div
                                key={item.search_id}
                                className="history-item fade-in"
                                style={{ animationDelay: `${i * 0.03}s`, animationFillMode: "both" }}
                            >
                                <div className="history-input">"{item.input_text}"</div>
                                {item.best_fit_word && (
                                    <>
                                        <ArrowRight size={16} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
                                        <div className="history-result">{item.best_fit_word}</div>
                                    </>
                                )}
                                <div className="history-meta">
                                    {item.tone && item.tone !== "neutral" && (
                                        <span>🎭 {item.tone}</span>
                                    )}
                                </div>
                                <div className="history-date">
                                    {new Date(item.created_at).toLocaleDateString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        hour: "2-digit",
                                        minute: "2-digit",
                                    })}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "center",
                                gap: "var(--space-sm)",
                                marginTop: "var(--space-xl)",
                            }}
                        >
                            <button
                                className="btn btn-secondary btn-sm"
                                disabled={page === 0}
                                onClick={() => setPage((p) => p - 1)}
                            >
                                Previous
                            </button>
                            <span
                                style={{
                                    padding: "var(--space-sm) var(--space-md)",
                                    color: "var(--text-secondary)",
                                    fontSize: "0.85rem",
                                    lineHeight: "2",
                                }}
                            >
                                Page {page + 1} of {totalPages}
                            </span>
                            <button
                                className="btn btn-secondary btn-sm"
                                disabled={page >= totalPages - 1}
                                onClick={() => setPage((p) => p + 1)}
                            >
                                Next
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
