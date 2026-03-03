import { Loader2, Brain, Lightbulb, BookOpen } from "lucide-react";
import { useState, useEffect } from "react";

interface LoadingOverlayProps {
    isLoading: boolean;
}

const steps = [
    { label: "Analyzing emotion & context", icon: Brain },
    { label: "Generating precise words", icon: Lightbulb },
    { label: "Explaining & categorizing", icon: BookOpen },
];

export default function LoadingOverlay({ isLoading }: LoadingOverlayProps) {
    const [activeStep, setActiveStep] = useState(0);

    useEffect(() => {
        if (!isLoading) {
            setActiveStep(0);
            return;
        }

        const interval = setInterval(() => {
            setActiveStep((prev) => {
                if (prev < steps.length - 1) return prev + 1;
                return prev;
            });
        }, 1200);

        return () => clearInterval(interval);
    }, [isLoading]);

    if (!isLoading) return null;

    return (
        <div className="loading-container">
            <div className="loading-spinner" />
            <p className="loading-text">Finding the perfect words for you...</p>
            <div className="loading-steps">
                {steps.map((step, i) => {
                    const Icon = step.icon;
                    let className = "loading-step";
                    if (i < activeStep) className += " done";
                    else if (i === activeStep) className += " active";

                    return (
                        <div key={i} className={className}>
                            {i < activeStep ? (
                                <span className="loading-step-icon">✓</span>
                            ) : i === activeStep ? (
                                <Loader2 size={18} className="loading-step-icon" style={{ animation: "spin 0.8s linear infinite" }} />
                            ) : (
                                <Icon size={18} className="loading-step-icon" />
                            )}
                            <span>{step.label}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
