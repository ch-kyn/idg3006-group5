import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import InventionPage from "./pages/InventionPage/InventionPage";
import QuizPage from "./pages/QuizPage/QuizPage";
import HomePage from "./pages/HomePage/HomePage";
import './styles/main.scss';

export default function App() {
  return (
    <Router>
      <main className="cont">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/inventions" element={<InventionPage />} />
          <Route path="/quiz" element={<QuizPage />} />
        </Routes>
      </main>
    </Router>
  );
}
