import { useState, useRef, useCallback, useEffect } from "react";
import { api } from "../services/api";

// ── Type definitions for Web Speech API ──────────────────────

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

function isBraveBrowser(): boolean {
    const nav = navigator as unknown as Record<string, unknown>;
    return !!nav.brave;
}

// ── Hook interface ───────────────────────────────────────────

interface UseSpeechRecognitionOptions {
    onResult: (text: string) => void;
    onError?: (error: string) => void;
    lang?: string;
}

interface UseSpeechRecognitionReturn {
    isSupported: boolean;
    isListening: boolean;
    toggleListening: () => void;
}

// ── Hook implementation ──────────────────────────────────────

export function useSpeechRecognition({
    onResult,
    onError,
    lang = "en-US",
}: UseSpeechRecognitionOptions): UseSpeechRecognitionReturn {
    const brave = isBraveBrowser();
    // Supported if: browser has SpeechRecognition (non-Brave) OR has MediaRecorder (Brave fallback)
    const isSupported = brave
        ? typeof MediaRecorder !== "undefined"
        : !!getSpeechRecognition();

    const [isListening, setIsListening] = useState(false);

    // Refs for Web Speech API path
    const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
    const retriesRef = useRef(0);
    const MAX_RETRIES = 3;
    const RETRY_DELAY_MS = 300;

    // Refs for MediaRecorder (Brave) path
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    // Clean up on unmount
    useEffect(() => {
        return () => {
            recognitionRef.current?.abort();
            mediaRecorderRef.current?.stop();
            mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
        };
    }, []);

    // ── Brave path: MediaRecorder → backend Whisper ──────────

    const startBraveListening = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;
            chunksRef.current = [];

            const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
            mediaRecorderRef.current = recorder;

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            recorder.onstop = async () => {
                // Release mic immediately
                stream.getTracks().forEach((t) => t.stop());
                mediaStreamRef.current = null;

                const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
                chunksRef.current = [];

                if (audioBlob.size === 0) {
                    setIsListening(false);
                    onError?.("No audio captured. Please try again.");
                    return;
                }

                // Send to backend for transcription
                try {
                    const { text } = await api.transcribe(audioBlob);
                    onResult(text);
                } catch (err) {
                    const msg = err instanceof Error ? err.message : "Transcription failed.";
                    onError?.(msg);
                } finally {
                    setIsListening(false);
                }
            };

            recorder.onerror = () => {
                stream.getTracks().forEach((t) => t.stop());
                setIsListening(false);
                onError?.("Audio recording failed. Please try again.");
            };

            recorder.start();
            setIsListening(true);
        } catch {
            setIsListening(false);
            onError?.("Microphone access was denied. Please allow it in your browser settings.");
        }
    }, [onResult, onError]);

    const stopBraveListening = useCallback(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
            mediaRecorderRef.current.stop(); // triggers onstop → transcription
        } else {
            mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
            setIsListening(false);
        }
    }, []);

    // ── Standard path: Web Speech API ────────────────────────

    const startWebSpeechListening = useCallback((isRetry = false) => {
        const SpeechRecognition = getSpeechRecognition();
        if (!SpeechRecognition) return;

        if (recognitionRef.current) {
            recognitionRef.current.abort();
        }

        if (!isRetry) {
            retriesRef.current = 0;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = lang;
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => setIsListening(true);

        recognition.onresult = (event: SpeechRecognitionEvent) => {
            retriesRef.current = 0;
            const transcript = event.results[0]?.[0]?.transcript?.trim();
            if (transcript) onResult(transcript);
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            if (event.error === "aborted") return;

            if (event.error === "network" && retriesRef.current < MAX_RETRIES) {
                retriesRef.current++;
                setTimeout(() => startWebSpeechListening(true), RETRY_DELAY_MS);
                return;
            }

            setIsListening(false);
            const messages: Record<string, string> = {
                "not-allowed": "Microphone access was denied. Please allow it in your browser settings.",
                "no-speech": "No speech detected. Please try again.",
                network: "Speech recognition is unavailable. Please try Chrome or Edge.",
            };
            onError?.(messages[event.error] ?? `Speech recognition error: ${event.error}`);
        };

        recognition.onend = () => {
            if (retriesRef.current > 0 && retriesRef.current <= MAX_RETRIES) return;
            setIsListening(false);
            recognitionRef.current = null;
        };

        recognitionRef.current = recognition;
        recognition.start();
    }, [lang, onResult, onError]);

    const stopWebSpeechListening = useCallback(() => {
        retriesRef.current = MAX_RETRIES + 1;
        if (recognitionRef.current) {
            recognitionRef.current.stop();
            recognitionRef.current = null;
        }
        setIsListening(false);
    }, []);

    // ── Unified toggle ───────────────────────────────────────

    const toggleListening = useCallback(() => {
        if (isListening) {
            brave ? stopBraveListening() : stopWebSpeechListening();
        } else {
            brave ? startBraveListening() : startWebSpeechListening();
        }
    }, [isListening, brave, startBraveListening, stopBraveListening, startWebSpeechListening, stopWebSpeechListening]);

    return { isSupported, isListening, toggleListening };
}
