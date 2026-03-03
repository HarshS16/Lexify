import { ArrowRight } from "lucide-react";
import type { RewriteResult as RewriteResultType } from "../types";

interface RewriteResultProps {
    result: RewriteResultType;
}

export default function RewriteResult({ result }: RewriteResultProps) {
    return (
        <div className="rewrite-result" id="rewrite-results">
            <div className="rewrite-comparison">
                <div className="rewrite-box original">
                    <div className="rewrite-box-label">Original</div>
                    <p>{result.original}</p>
                </div>
                <div className="rewrite-box rewritten">
                    <div className="rewrite-box-label">Rewritten — {result.goal}</div>
                    <p>{result.rewritten}</p>
                </div>
            </div>

            {result.changes && result.changes.length > 0 && (
                <>
                    <h3 className="alternatives-header">Word Changes</h3>
                    <ul className="changes-list">
                        {result.changes.map((change, i) => (
                            <li
                                key={i}
                                className="change-item fade-in"
                                style={{ animationDelay: `${i * 0.1}s`, animationFillMode: "both" }}
                            >
                                <div className="change-words">
                                    <span className="change-original">{change.original_word}</span>
                                    <ArrowRight size={14} className="change-arrow" />
                                    <span className="change-new">{change.new_word}</span>
                                </div>
                                <span className="change-reason">{change.reason}</span>
                            </li>
                        ))}
                    </ul>
                </>
            )}
        </div>
    );
}
