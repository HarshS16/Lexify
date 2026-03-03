import { useState, useEffect } from "react";
import { Clock, Trash2 } from "lucide-react";
import { getHistory, clearHistory, type LocalHistoryItem } from "../services/history";

export default function HistoryPage() {
    const [items, setItems] = useState<LocalHistoryItem[]>([]);

    useEffect(() => {
        setItems(getHistory());
    }, []);

    const handleClear = () => {
        if (window.confirm("Clear all search history?")) {
            clearHistory();
            setItems([]);
        }
    };

    const formatDate = (iso: string) => {
        const d = new Date(iso);
        return d.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    return (
        <div className="main-content">
            <div className="page-header" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                    <h1>Search History</h1>
                    <p>Your recent word searches on this device.</p>
                </div>
                {items.length > 0 && (
                    <button className="btn-secondary" onClick={handleClear} style={{ display: "flex", alignItems: "center", gap: "6px", padding: "8px 16px", borderRadius: "10px", background: "var(--bg-glass)", border: "1px solid var(--border-medium)", color: "var(--text-secondary)", cursor: "pointer", fontSize: "0.85rem" }}>
                        <Trash2 size={14} />
                        Clear
                    </button>
                )}
            </div>

            {items.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">
                        <Clock size={48} />
                    </div>
                    <h3 className="empty-title">No history yet</h3>
                    <p className="empty-text">Your searches will appear here.</p>
                </div>
            ) : (
                <div className="history-list">
                    {items.map((item) => (
                        <div key={item.id} className="history-item">
                            <span className="history-input">{item.input_text}</span>
                            {item.best_fit_word && (
                                <span className="history-result">{item.best_fit_word}</span>
                            )}
                            <div className="history-meta">
                                {item.tone && <span>{item.tone}</span>}
                                {item.intent && <span>{item.intent}</span>}
                            </div>
                            <span className="history-date">{formatDate(item.created_at)}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
