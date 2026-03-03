import { useState } from "react";
import { X } from "lucide-react";

interface SaveWordModalProps {
    word: string;
    onSave: (word: string, notes: string, tags: string[]) => void;
    onClose: () => void;
}

export default function SaveWordModal({ word, onSave, onClose }: SaveWordModalProps) {
    const [notes, setNotes] = useState("");
    const [tagsInput, setTagsInput] = useState("");

    const handleSave = () => {
        const tags = tagsInput
            .split(",")
            .map((t) => t.trim())
            .filter(Boolean);
        onSave(word, notes, tags);
    };

    return (
        <div className="modal-overlay" onClick={onClose} id="save-word-modal">
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <h3>
                        Save "<span style={{ color: "var(--accent-primary-light)" }}>{word}</span>"
                    </h3>
                    <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>
                        <X size={18} />
                    </button>
                </div>

                <div className="form-group">
                    <label className="form-label">Notes (optional)</label>
                    <textarea
                        className="input"
                        rows={3}
                        placeholder="Add personal notes about this word..."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        id="save-word-notes"
                    />
                </div>

                <div className="form-group">
                    <label className="form-label">Tags (comma separated)</label>
                    <input
                        className="input"
                        type="text"
                        placeholder="e.g. writing, emotion, professional"
                        value={tagsInput}
                        onChange={(e) => setTagsInput(e.target.value)}
                        id="save-word-tags"
                    />
                </div>

                <div className="modal-actions">
                    <button className="btn btn-secondary" onClick={onClose}>
                        Cancel
                    </button>
                    <button className="btn btn-primary" onClick={handleSave} id="confirm-save-word">
                        Save Word
                    </button>
                </div>
            </div>
        </div>
    );
}
