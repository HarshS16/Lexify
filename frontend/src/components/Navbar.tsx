import { Link, useLocation } from "react-router-dom";
import { Search, BookOpen, Clock, Sun, Moon } from "lucide-react";
import { useTheme } from "../hooks/useTheme";

export default function Navbar() {
    const location = useLocation();
    const { theme, toggle } = useTheme();
    const isActive = (path: string) => location.pathname === path;

    return (
        <nav className="navbar">
            <div className="navbar-inner">
                <Link to="/" className="navbar-logo">
                    <div className="logo-icon">✦</div>
                    <span className="logo-text-gradient">Lexify</span>
                </Link>

                <div className="navbar-nav">
                    <Link to="/" className={`nav-link ${isActive("/") ? "active" : ""}`}>
                        <Search size={15} />
                        <span>Search</span>
                    </Link>
                    <Link to="/vocabulary" className={`nav-link ${isActive("/vocabulary") ? "active" : ""}`}>
                        <BookOpen size={15} />
                        <span>Vocabulary</span>
                    </Link>
                    <Link to="/history" className={`nav-link ${isActive("/history") ? "active" : ""}`}>
                        <Clock size={15} />
                        <span>History</span>
                    </Link>

                    <button
                        className="theme-toggle"
                        onClick={toggle}
                        title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
                        aria-label="Toggle theme"
                    >
                        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                </div>
            </div>
        </nav>
    );
}
