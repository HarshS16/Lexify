import { Heart } from "lucide-react";

export default function Footer() {
    return (
        <footer className="footer">
            <div className="footer-inner">
                <span className="footer-text">
                    Built with <Heart size={14} className="footer-heart" /> by{" "}
                    <a
                        href="https://x.com/Harsh_jsx/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="footer-link"
                    >
                        @Harsh_jsx
                    </a>
                </span>
            </div>
        </footer>
    );
}
