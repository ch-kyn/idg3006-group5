import { useState } from 'react';
import QuizItem from '../QuizItem/QuizItem';
import QuizFinish from '../QuizFinish/QuizFinish';
import styles from './Quiz.module.scss';

const Quiz = ({ questions, country }) => {
    const [currentIdx, setCurrentIdx] = useState(0);
    const [selectedOptions, setSelectedOptions] = useState([]);
    const [correctSelected, setCorrectSelected] = useState(false);
    const [firstTryCorrect, setFirstTryCorrect] = useState(0);

    if (currentIdx >= questions.length) {
        return (
            <QuizFinish
                score={firstTryCorrect}
                total={questions.length}
                country={country}
            />
        );
    }

    const currentQuestion = questions[currentIdx];
    const correctAnswerObj = currentQuestion.answers.find(a => a.correct);

    const handleSelect = (option) => {
        setSelectedOptions(prev => [...prev, option.answer]);

        // Count first-try correct
        if (!correctSelected && selectedOptions.length === 0 && option.correct) {
            setFirstTryCorrect(prev => prev + 1);
        }

        // If correct answer clicked, disable all
        if (option.correct) {
            setCorrectSelected(true);
        }
    };

    const handleNext = () => {
        setCurrentIdx(prev => prev + 1);
        setSelectedOptions([]);
        setCorrectSelected(false);
    };

    const letters = ["A", "B", "C", "D"];

    return (
        <div className={styles.cont}>
            <h2 className={styles.title}>{currentQuestion.question}</h2>

            <div className={styles.answers}>
                {currentQuestion.answers.map((option, i) => (
                    <QuizItem
                        key={i}
                        option={option}
                        selectedOptions={selectedOptions}
                        correctSelected={correctSelected}
                        onSelect={handleSelect}
                        letter={letters[i]}
                    />
                ))}
            </div>

            {correctSelected && <div className={styles.explanation}>{correctAnswerObj.explanation}</div>}

            <button className={styles.nextButton} onClick={handleNext} disabled={!correctSelected}>
                {currentIdx === questions.length - 1 ? "Complete Quiz" : "Next Question"}
            </button>
        </div>
    );
};

export default Quiz;
