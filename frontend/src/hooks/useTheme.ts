import { useState, useEffect } from "react";

type Theme = "dark" | "light";

export function useTheme() {
    const [theme, setTheme] = useState<Theme>(() => {
        // Check localStorage first, default to dark
        const saved = localStorage.getItem("lexify-theme") as Theme | null;
        return saved || "dark";
    });

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("lexify-theme", theme);
    }, [theme]);

    const toggle = () => {
        setTheme((prev) => (prev === "dark" ? "light" : "dark"));
    };

    return { theme, toggle };
}
