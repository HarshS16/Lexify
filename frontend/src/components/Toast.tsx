import { useState, useEffect } from "react";
import { CheckCircle, XCircle, X } from "lucide-react";

export interface Toast {
    id: string;
    message: string;
    type: "success" | "error";
}

interface ToastContainerProps {
    toasts: Toast[];
    onRemove: (id: string) => void;
}

export function useToast() {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = (message: string, type: "success" | "error" = "success") => {
        const id = Date.now().toString();
        setToasts((prev) => [...prev, { id, message, type }]);
    };

    const removeToast = (id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    return { toasts, addToast, removeToast };
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
    return (
        <div className="toast-container">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
            ))}
        </div>
    );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
    useEffect(() => {
        const timeout = setTimeout(() => onRemove(toast.id), 3000);
        return () => clearTimeout(timeout);
    }, [toast.id, onRemove]);

    return (
        <div className={`toast toast-${toast.type}`}>
            {toast.type === "success" ? (
                <CheckCircle size={16} style={{ color: "var(--accent-secondary-light)" }} />
            ) : (
                <XCircle size={16} style={{ color: "var(--accent-warm)" }} />
            )}
            <span>{toast.message}</span>
            <button
                className="btn btn-ghost btn-sm btn-icon"
                onClick={() => onRemove(toast.id)}
                style={{ marginLeft: "auto" }}
            >
                <X size={14} />
            </button>
        </div>
    );
}
