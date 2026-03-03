import { Link, useLocation } from "react-router-dom";
import { Search, BookOpen, Clock, Sparkles } from "lucide-react";

export default function Navbar() {
    const location = useLocation();

    const links = [
        { to: "/", icon: Search, label: "Search" },
        { to: "/word-of-the-day", icon: Sparkles, label: "Word of the Day" },
        { to: "/vocabulary", icon: BookOpen, label: "Vocabulary" },
        { to: "/history", icon: Clock, label: "History" },
    ];

    return (
        <nav className="navbar" id="main-navbar">
            <div className="navbar-inner">
                <Link to="/" className="navbar-logo">
                    <div className="logo-icon">✦</div>
                    <span className="logo-text-gradient">Lexify</span>
                </Link>

                <div className="navbar-nav">
                    {links.map(({ to, icon: Icon, label }) => (
                        <Link
                            key={to}
                            to={to}
                            className={`nav-link ${location.pathname === to ? "active" : ""}`}
                            id={`nav-${label.toLowerCase().replace(/\s+/g, "-")}`}
                        >
                            <Icon size={16} />
                            <span>{label}</span>
                        </Link>
                    ))}
                </div>
            </div>
        </nav>
    );
}
