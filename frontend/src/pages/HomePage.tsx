import { useState, useCallback } from "react";
import { Search, RefreshCw, Mic, MicOff } from "lucide-react";
import { api } from "../services/api";
import { addToHistory } from "../services/history";
import type {
    AppMode,
    ToneOption,
    IntentOption,
    RewriteGoal,
    SearchResponse,
    RewriteResult as RewriteResultType,
} from "../types";
import SearchResults from "../components/SearchResults";
import RewriteResultComp from "../components/RewriteResult";
import LoadingOverlay from "../components/LoadingOverlay";
import SaveWordModal from "../components/SaveWordModal";
import { useToast, ToastContainer } from "../components/Toast";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";

const toneOptions: ToneOption[] = [
    "neutral",
    "professional",
    "casual",
    "poetic",
    "academic",
    "empathetic",
];

const intentOptions: IntentOption[] = [
    "general expression",
    "emotional expression",
    "writing improvement",
    "clarity",
];

const rewriteGoals: RewriteGoal[] = [
    "more confident",
    "more polite",
    "more emotionally precise",
    "more professional",
];

export default function HomePage() {
    const [mode, setMode] = useState<AppMode>("search");
    const [input, setInput] = useState("");
    const [tone, setTone] = useState<ToneOption>("neutral");
    const [intent, setIntent] = useState<IntentOption>("general expression");
    const [rewriteGoal, setRewriteGoal] = useState<RewriteGoal>("more confident");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
    const [rewriteResult, setRewriteResult] = useState<RewriteResultType | null>(null);
    const [saveModal, setSaveModal] = useState<string | null>(null);
    const { toasts, addToast, removeToast } = useToast();

    const onSpeechResult = useCallback((text: string) => {
        setInput(text);
        addToast(`🎤 "${text}"`, "success");
    }, [addToast]);

    const onSpeechError = useCallback((error: string) => {
        addToast(error, "error");
    }, [addToast]);

    const { isSupported: micSupported, isListening, toggleListening } = useSpeechRecognition({
        onResult: onSpeechResult,
        onError: onSpeechError,
    });

    const handleSearch = async () => {
        if (!input.trim()) return;
        setLoading(true);
        setError("");
        setSearchResult(null);
        setRewriteResult(null);

        try {
            if (mode === "search") {
                const result = await api.search({
                    input_text: input.trim(),
                    tone,
                    intent,
                });
                setSearchResult(result);
                addToHistory({
                    input_text: input.trim(),
                    tone,
                    intent,
                    best_fit_word: result.result?.best_fit || null,
                });
            } else {
                const result = await api.rewrite({
                    input_text: input.trim(),
                    goal: rewriteGoal,
                    tone,
                });
                setRewriteResult(result);
            }
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Something went wrong. Please try again.";
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    };

    const handleSaveWord = (word: string) => {
        setSaveModal(word);
    };

    const handleConfirmSave = async (word: string, notes: string, tags: string[]) => {
        try {
            await api.saveWord({ word, notes, tags });
            addToast(`"${word}" saved to vocabulary!`, "success");
        } catch {
            addToast("Failed to save word", "error");
        }
        setSaveModal(null);
    };

    const handleFeedback = async (word: string, rating: -1 | 1) => {
        try {
            await api.submitFeedback({
                search_id: searchResult?.search_id,
                word,
                rating,
            });
            addToast(rating === 1 ? "Thanks for the feedback! 👍" : "Noted! We'll improve 👎", "success");
        } catch {
            addToast("Failed to submit feedback", "error");
        }
    };

    return (
        <div className="main-content">
            {/* Hero Section */}
            <section className="hero-section" id="hero-section">
                <h1 className="hero-title">
                    Find the <span className="gradient-text">Perfect Word</span>
                </h1>
                <p className="hero-subtitle">
                    AI-powered contextual word suggestions. Go beyond synonyms — find words that
                    capture the exact emotion, tone, and intent you need.
                </p>

                {/* Mode Toggle */}
                <div className="mode-toggle" id="mode-toggle">
                    <button
                        className={`mode-btn ${mode === "search" ? "active" : ""}`}
                        onClick={() => { setMode("search"); setSearchResult(null); setRewriteResult(null); }}
                    >
                        <Search size={15} />
                        Find Words
                    </button>
                    <button
                        className={`mode-btn ${mode === "rewrite" ? "active" : ""}`}
                        onClick={() => { setMode("rewrite"); setSearchResult(null); setRewriteResult(null); }}
                    >
                        <RefreshCw size={15} />
                        Rewrite
                    </button>
                </div>

                {/* Search Box */}
                <div className="search-container">
                    <div className={`search-box${isListening ? " is-listening" : ""}`}>
                        <input
                            className={`search-input${micSupported ? " has-mic" : ""}${isListening ? " listening-active" : ""}`}
                            type="text"
                            placeholder={
                                mode === "search"
                                    ? "Enter a word, phrase, or sentence..."
                                    : "Enter a sentence to rewrite..."
                            }
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            id="search-input"
                        />
                        {/* Audio Waveform Visualizer */}
                        {isListening && (
                            <div className="voice-visualizer" id="voice-visualizer">
                                <div className="voice-wave-bars">
                                    <span className="wave-bar" style={{ animationDelay: "0s" }} />
                                    <span className="wave-bar" style={{ animationDelay: "0.15s" }} />
                                    <span className="wave-bar" style={{ animationDelay: "0.3s" }} />
                                    <span className="wave-bar" style={{ animationDelay: "0.1s" }} />
                                    <span className="wave-bar" style={{ animationDelay: "0.25s" }} />
                                </div>
                                <span className="voice-label">Listening...</span>
                            </div>
                        )}
                        {micSupported && (
                            <button
                                className={`mic-btn${isListening ? " listening" : ""}`}
                                onClick={toggleListening}
                                type="button"
                                title={isListening ? "Stop listening" : "Speak your word or sentence"}
                                id="mic-btn"
                            >
                                {isListening ? <MicOff size={18} /> : <Mic size={18} />}
                            </button>
                        )}
                        <button
                            className="search-btn"
                            onClick={handleSearch}
                            disabled={loading || !input.trim()}
                            id="search-submit-btn"
                        >
                            {loading ? (
                                <>
                                    <span className="loading-spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
                                </>
                            ) : (
                                <>
                                    <Search size={16} />
                                    <span>{mode === "search" ? "Find" : "Rewrite"}</span>
                                </>
                            )}
                        </button>
                    </div>

                    {/* Options */}
                    <div className="options-bar">
                        <div className="option-group">
                            <span className="option-label">Tone</span>
                            <select
                                className="select"
                                value={tone}
                                onChange={(e) => setTone(e.target.value as ToneOption)}
                                id="tone-select"
                            >
                                {toneOptions.map((t) => (
                                    <option key={t} value={t}>
                                        {t.charAt(0).toUpperCase() + t.slice(1)}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {mode === "search" ? (
                            <div className="option-group">
                                <span className="option-label">Intent</span>
                                <select
                                    className="select"
                                    value={intent}
                                    onChange={(e) => setIntent(e.target.value as IntentOption)}
                                    id="intent-select"
                                >
                                    {intentOptions.map((i) => (
                                        <option key={i} value={i}>
                                            {i.charAt(0).toUpperCase() + i.slice(1)}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        ) : (
                            <div className="option-group">
                                <span className="option-label">Goal</span>
                                <div className="rewrite-goals">
                                    {rewriteGoals.map((g) => (
                                        <button
                                            key={g}
                                            className={`goal-chip ${rewriteGoal === g ? "active" : ""}`}
                                            onClick={() => setRewriteGoal(g)}
                                        >
                                            {g}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </section>

            {/* Error */}
            {error && (
                <div className="error-banner" id="error-banner">
                    <span>⚠️ {error}</span>
                    <button className="btn-secondary" onClick={handleSearch} style={{ marginLeft: "auto", padding: "6px 16px", fontSize: "0.85rem" }}>
                        Retry
                    </button>
                </div>
            )}

            {/* Loading */}
            <LoadingOverlay isLoading={loading} />

            {/* Search Results */}
            {searchResult && !loading && (
                <SearchResults
                    result={searchResult.result}
                    searchId={searchResult.search_id}
                    onSaveWord={handleSaveWord}
                    onFeedback={handleFeedback}
                />
            )}

            {/* Rewrite Results */}
            {rewriteResult && !loading && <RewriteResultComp result={rewriteResult} />}

            {/* Save Modal */}
            {saveModal && (
                <SaveWordModal
                    word={saveModal}
                    onSave={handleConfirmSave}
                    onClose={() => setSaveModal(null)}
                />
            )}

            {/* Toasts */}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </div>
    );
}
