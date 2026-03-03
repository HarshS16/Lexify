export interface LocalHistoryItem {
    id: string;
    input_text: string;
    tone: string;
    intent: string;
    best_fit_word: string | null;
    created_at: string;
}

const STORAGE_KEY = "lexify-history";
const MAX_ITEMS = 100;

export function getHistory(): LocalHistoryItem[] {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
}

export function addToHistory(item: Omit<LocalHistoryItem, "id" | "created_at">): void {
    const history = getHistory();
    const newItem: LocalHistoryItem = {
        ...item,
        id: crypto.randomUUID(),
        created_at: new Date().toISOString(),
    };
    // Prepend (newest first), cap at MAX_ITEMS
    history.unshift(newItem);
    if (history.length > MAX_ITEMS) history.pop();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

export function clearHistory(): void {
    localStorage.removeItem(STORAGE_KEY);
}
