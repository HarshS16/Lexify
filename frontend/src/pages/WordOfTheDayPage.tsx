import { useState, useEffect } from "react";
import { Sparkles, RefreshCw } from "lucide-react";
import { api } from "../services/api";
import type { WordOfTheDay } from "../types";

export default function WordOfTheDayPage() {
    const [wotd, setWotd] = useState<WordOfTheDay | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const fetchWotd = async () => {
        setLoading(true);
        setError("");
        try {
            const data = await api.getWordOfTheDay();
            setWotd(data);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to load Word of the Day");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWotd();
    }, []);

    return (
        <div className="main-content">
            <div className="page-header">
                <h1>
                    <Sparkles
                        size={28}
                        style={{ display: "inline", verticalAlign: "middle", marginRight: 8, color: "var(--accent-gold)" }}
                    />
                    Word of the Day
                </h1>
                <p>Expand your vocabulary with a new AI-curated word every day</p>
            </div>

            {loading && (
                <div className="loading-container">
                    <div className="loading-spinner" />
                    <p className="loading-text">Loading today's word...</p>
                </div>
            )}

            {error && (
                <div className="error-banner">
                    <span>⚠️</span>
                    <span>{error}</span>
                    <button className="btn btn-secondary btn-sm" onClick={fetchWotd} style={{ marginLeft: "auto" }}>
                        <RefreshCw size={14} />
                        Retry
                    </button>
                </div>
            )}

            {wotd && !loading && (
                <div className="wotd-card fade-in" id="wotd-card">
                    <div className="wotd-badge">
                        <Sparkles size={12} />
                        {new Date(wotd.date).toLocaleDateString("en-US", {
                            weekday: "long",
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                        })}
                    </div>

                    <div className="wotd-word">{wotd.word}</div>
                    <div className="wotd-meaning">{wotd.meaning}</div>

                    <div className="wotd-details">
                        <div className="wotd-detail">
                            <div className="wotd-detail-label">🎭 Emotional Range</div>
                            <div className="wotd-detail-value">{wotd.emotional_range}</div>
                        </div>
                        <div className="wotd-detail">
                            <div className="wotd-detail-label">💬 Example Usage</div>
                            <div className="wotd-detail-value" style={{ fontStyle: "italic" }}>
                                "{wotd.example_usage}"
                            </div>
                        </div>
                        <div className="wotd-detail">
                            <div className="wotd-detail-label">✅ When to Use</div>
                            <div className="wotd-detail-value">{wotd.when_to_use}</div>
                        </div>
                        <div className="wotd-detail">
                            <div className="wotd-detail-label">⚠️ When to Avoid</div>
                            <div className="wotd-detail-value">{wotd.when_to_avoid}</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
