import styles from './QuizFinish.module.scss';

const QuizFinish = ({ score, total, country }) => {
    let message = '';

    const percentage = total > 0 ? score / total : 0;

    // customizable message
    if (score === 0) {
        message = "Let's try again! 😅";
    } else if (percentage <= 0.5) {
        message = "Nice try! 👍";
    } else if (percentage > 0.5 && score < total) {
        message = "You almost got it! 🤏✨";
    } else if (score === total) {
        message = "Woah... You must be an expert! 🏆🎉";
    }

    return (
        <div className={styles.cont}>
            <h2 className={styles.title}>{message}</h2>
            <p className={styles.score}>
                You answered <strong>{score}</strong> out of <strong>{total}</strong> questions correctly on the first try.
            </p>

        {/* make the reload less abrupt */}
        <button
            tabIndex={0} 
            data-nav="select" 
            className={`${styles.restartButton} controller-target`}
            onClick={() => {
                const quizContainer = document.querySelector(`.${styles.cont}`);
                if (quizContainer) {
                    quizContainer.style.transition = 'opacity 0.5s';
                    quizContainer.style.opacity = '0';
                }
                setTimeout(() => {
                    window.location.reload();
                }, 200);
            }}
        >
            Try another {country} quiz?
        </button>

        </div>
    );
};

export default QuizFinish;
