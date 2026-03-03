import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import HomePage from "./pages/HomePage";
import WordOfTheDayPage from "./pages/WordOfTheDayPage";
import VocabularyPage from "./pages/VocabularyPage";
import HistoryPage from "./pages/HistoryPage";
import { Analytics } from "@vercel/analytics/react";

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/word-of-the-day" element={<WordOfTheDayPage />} />
          <Route path="/vocabulary" element={<VocabularyPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
        <Footer />
        <Analytics />
      </div>
    </BrowserRouter>
  );
}

export default App;
