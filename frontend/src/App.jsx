import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import InventionPage from "./pages/InventionPage/InventionPage";
import QuizPage from "./pages/QuizPage/QuizPage";
import AboutPage from "./pages/AboutPage/AboutPage";
import HomePage from "./pages/HomePage/HomePage";
import ControllerPage from "./pages/ControllerPage/ControllerPage";
import NotFound from "./components/NotFound/NotFound";
import "./styles/main.scss";

export default function App() {
    return (
        <Router>
            <main className="cont">
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/invention" element={<InventionPage />} />
                    <Route path="/quiz" element={<QuizPage />} />
                    <Route path="/about" element={<AboutPage />} />
                    <Route path="/controller" element={<ControllerPage />} />
                    {/* <Route path="*" element={<NotFound />} /> */}
                </Routes>
            </main>
        </Router>
    );
}
