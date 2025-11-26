import { useState, useEffect } from 'react';
import QuizItem from '../QuizItem/QuizItem';
import QuizFinish from '../QuizFinish/QuizFinish';
import styles from './Quiz.module.scss';

const Quiz = ({ questions, country, onProgress }) => {
    const [currentIdx, setCurrentIdx] = useState(0);
    const [selectedOptions, setSelectedOptions] = useState([]);
    const [correctSelected, setCorrectSelected] = useState(false);
    const [firstTryCorrect, setFirstTryCorrect] = useState(0);

    // focus Next button when correct answer selected
    // useEffect(() => {
    //     if (correctSelected) {
    //         const nextBtn = document.querySelector("#nextButton");
    //         nextBtn?.focus();
    //     }
    // }, [correctSelected]);

    // const tabbable = Array.from(document.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'))
    // .filter(el => !el.disabled && el.offsetParent !== null); // visible & not disabled

    // tabbable.forEach((el, i) => console.log(i, el));

    // safely update progress for parent
    useEffect(() => {
        if (onProgress) {
            onProgress(currentIdx + 1); // 1-based
        }
    }, [currentIdx, onProgress]);

    if (!questions || questions.length === 0) return null;

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
        if (selectedOptions.includes(option.answer)) return;

        setSelectedOptions(prev => [...prev, option.answer]);

        // count first-try correct
        if (!correctSelected && selectedOptions.length === 0 && option.correct) {
            setFirstTryCorrect(prev => prev + 1);
        }

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
            <h2 className={styles.title}>
                {currentQuestion.question}
            </h2>

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

            {correctSelected && (
                <div className={styles.explanation}>
                    {correctAnswerObj.explanation}
                </div>
            )}

            <button
                tabIndex={0}
                id="nextButton"
                className={`${styles.nextButton} controller-target`}
                onClick={handleNext}
                disabled={!correctSelected}
                data-nav="select" 
            >
                {currentIdx === questions.length - 1
                    ? "Complete Quiz"
                    : "Next Question"}
            </button>
        </div>
    );
};

export default Quiz;
