import { ThumbsUp, ThumbsDown, Bookmark } from "lucide-react";
import type { WordSuggestionResult } from "../types";

interface SearchResultsProps {
    result: WordSuggestionResult;
    searchId: string;
    onSaveWord: (word: string) => void;
    onFeedback: (word: string, rating: -1 | 1) => void;
}

function getCategoryClass(cat: string): string {
    const map: Record<string, string> = {
        emotional: "badge-emotional",
        professional: "badge-professional",
        creative: "badge-creative",
        formal: "badge-formal",
        informal: "badge-informal",
    };
    return map[cat.toLowerCase()] || "badge-professional";
}

function getStrengthClass(strength: string): string {
    return `strength-${strength.toLowerCase()}`;
}

function getIntensityClass(intensity: string): string {
    return `intensity-${intensity.toLowerCase()}`;
}

export default function SearchResults({ result, onSaveWord, onFeedback }: SearchResultsProps) {
    const { best_fit, best_fit_explanation, best_fit_example_sentence, best_fit_categories, alternatives, analysis } = result;

    return (
        <div className="results-section" id="search-results">
            {/* Emotion Analysis Bar */}
            <div className="emotion-bar">
                <div className="emotion-item">
                    <span className="emotion-label">Primary:</span>
                    <span className="emotion-value">{analysis.primary_emotion}</span>
                </div>
                {analysis.secondary_emotion && (
                    <div className="emotion-item">
                        <span className="emotion-label">Secondary:</span>
                        <span className="emotion-value">{analysis.secondary_emotion}</span>
                    </div>
                )}
                <div className="emotion-item">
                    <span className="emotion-label">Intensity:</span>
                    <span className={`emotion-value ${getIntensityClass(analysis.intensity)}`}>
                        {analysis.intensity}
                    </span>
                </div>
                <div className="emotion-item" style={{ flex: 1 }}>
                    <span className="emotion-label">Context:</span>
                    <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                        {analysis.context_summary}
                    </span>
                </div>
            </div>

            {/* Best Fit Card */}
            <div className="best-fit-card" id="best-fit-word">
                <div className="best-fit-label">✦ Best Fit Word</div>
                <div className="best-fit-word">{best_fit}</div>
                {best_fit_explanation && (
                    <div className="best-fit-explanation">{best_fit_explanation}</div>
                )}
                {best_fit_example_sentence && (
                    <div className="example-sentence" id="best-fit-example">
                        <span className="example-sentence-icon">❝</span>
                        <p className="example-sentence-text">{best_fit_example_sentence}</p>
                    </div>
                )}
                {best_fit_categories && best_fit_categories.length > 0 && (
                    <div className="best-fit-categories">
                        {best_fit_categories.map((cat) => (
                            <span key={cat} className={`badge ${getCategoryClass(cat)}`}>
                                {cat}
                            </span>
                        ))}
                    </div>
                )}
                <div className="best-fit-actions">
                    <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onSaveWord(best_fit)}
                        title="Save to vocabulary"
                        id="save-best-fit-btn"
                    >
                        <Bookmark size={14} />
                        Save
                    </button>
                    <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => onFeedback(best_fit, 1)}
                        title="Like"
                    >
                        <ThumbsUp size={14} />
                    </button>
                    <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => onFeedback(best_fit, -1)}
                        title="Dislike"
                    >
                        <ThumbsDown size={14} />
                    </button>
                </div>
            </div>

            {/* Alternatives */}
            <h3 className="alternatives-header">Alternatives</h3>
            <div className="alternatives-grid" id="alternatives-grid">
                {alternatives.map((alt, i) => (
                    <div
                        key={alt.word}
                        className="alt-card fade-in"
                        style={{ animationDelay: `${i * 0.08}s`, animationFillMode: "both" }}
                    >
                        <div className="alt-card-top">
                            <span className="alt-word">{alt.word}</span>
                            <span className={`alt-strength ${getStrengthClass(alt.strength)}`}>
                                {alt.strength}
                            </span>
                        </div>
                        {alt.explanation && (
                            <p className="alt-explanation">{alt.explanation}</p>
                        )}
                        {alt.example_sentence && (
                            <div className="example-sentence example-sentence-alt">
                                <span className="example-sentence-icon">❝</span>
                                <p className="example-sentence-text">{alt.example_sentence}</p>
                            </div>
                        )}
                        {alt.categories && alt.categories.length > 0 && (
                            <div className="alt-categories">
                                {alt.categories.map((cat) => (
                                    <span key={cat} className={`badge ${getCategoryClass(cat)}`}>
                                        {cat}
                                    </span>
                                ))}
                            </div>
                        )}
                        <div className="alt-actions">
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={() => onSaveWord(alt.word)}
                            >
                                <Bookmark size={12} />
                                Save
                            </button>
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={() => onFeedback(alt.word, 1)}
                            >
                                <ThumbsUp size={12} />
                            </button>
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={() => onFeedback(alt.word, -1)}
                            >
                                <ThumbsDown size={12} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
