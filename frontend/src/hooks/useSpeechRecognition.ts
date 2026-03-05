import { useState, useRef, useCallback, useEffect } from "react";

// Extend Window to include vendor-prefixed SpeechRecognition
interface SpeechRecognitionEvent extends Event {
    results: SpeechRecognitionResultList;
    resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
    error: string;
    message?: string;
}

interface SpeechRecognitionInstance extends EventTarget {
    lang: string;
    continuous: boolean;
    interimResults: boolean;
    start(): void;
    stop(): void;
    abort(): void;
    onresult: ((event: SpeechRecognitionEvent) => void) | null;
    onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
    onend: (() => void) | null;
    onstart: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

function getSpeechRecognition(): SpeechRecognitionConstructor | null {
    const w = window as unknown as Record<string, unknown>;
    return (
        (w.SpeechRecognition as SpeechRecognitionConstructor) ??
        (w.webkitSpeechRecognition as SpeechRecognitionConstructor) ??
        null
    );
}

interface UseSpeechRecognitionOptions {
    /** Called with the final transcript when speech ends */
    onResult: (text: string) => void;
    /** Called when an error occurs */
    onError?: (error: string) => void;
    /** BCP-47 language tag, default "en-US" */
    lang?: string;
}

interface UseSpeechRecognitionReturn {
    /** Whether the browser supports the Web Speech API */
    isSupported: boolean;
    /** Whether the microphone is currently listening */
    isListening: boolean;
    /** Toggle listening on/off */
    toggleListening: () => void;
}

export function useSpeechRecognition({
    onResult,
    onError,
    lang = "en-US",
}: UseSpeechRecognitionOptions): UseSpeechRecognitionReturn {
    const isSupported = !!getSpeechRecognition();
    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

    // Clean up on unmount
    useEffect(() => {
        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.abort();
                recognitionRef.current = null;
            }
        };
    }, []);

    const startListening = useCallback(() => {
        const SpeechRecognition = getSpeechRecognition();
        if (!SpeechRecognition) return;

        // Stop any existing session
        if (recognitionRef.current) {
            recognitionRef.current.abort();
        }

        const recognition = new SpeechRecognition();
        recognition.lang = lang;
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            setIsListening(true);
        };

        recognition.onresult = (event: SpeechRecognitionEvent) => {
            const transcript = event.results[0]?.[0]?.transcript?.trim();
            if (transcript) {
                onResult(transcript);
            }
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            setIsListening(false);
            // "aborted" happens when we manually stop — don't surface it
            if (event.error !== "aborted") {
                const messages: Record<string, string> = {
                    "not-allowed": "Microphone access was denied. Please allow it in your browser settings.",
                    "no-speech": "No speech detected. Please try again.",
                    network: "Network error. Check your connection and try again.",
                };
                const msg = messages[event.error] ?? `Speech recognition error: ${event.error}`;
                onError?.(msg);
            }
        };

        recognition.onend = () => {
            setIsListening(false);
            recognitionRef.current = null;
        };

        recognitionRef.current = recognition;
        recognition.start();
    }, [lang, onResult, onError]);

    const stopListening = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
            recognitionRef.current = null;
        }
        setIsListening(false);
    }, []);

    const toggleListening = useCallback(() => {
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    }, [isListening, startListening, stopListening]);

    return { isSupported, isListening, toggleListening };
}
