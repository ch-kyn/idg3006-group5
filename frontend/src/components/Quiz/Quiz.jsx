import { useState } from 'react';
import QuizItem from '../QuizItem/QuizItem';
import styles from './Quiz.module.scss';

const Quiz = ({ questions }) => {
    const [currentIdx, setCurrentIdx] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState(null);

    const currentQuestion = questions[currentIdx];

    const handleSelect = (option) => {
        if (selectedAnswer) return; // prevent double click
        setSelectedAnswer(option);

        // automatically move to next question after 5 seconds
        setTimeout(() => {
            setSelectedAnswer(null);
            setCurrentIdx((prev) => prev + 1);
        }, 5000);
    };

    const letters = ["A", "B", "C", "D"];

    if (!questions || questions.length === 0) {
        return <p>Loading quiz...</p>; // prevent rendering before data arrives
    }

    return (
        <div className={styles.cont}>
            <h2 className={styles.title}>{currentQuestion.question}</h2>
            <div className={styles.answers}>
            {currentQuestion.answers.map((option, i) => (
                <QuizItem
                    key={i}
                    option={option}
                    correct={currentQuestion.correct}
                    selected={selectedAnswer}
                    onSelect={handleSelect}
                    letter={letters[i]}
                />
            ))}
            </div>
        </div>
    );
};

export default Quiz;

