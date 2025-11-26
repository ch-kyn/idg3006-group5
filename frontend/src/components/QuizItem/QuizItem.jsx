import styles from './QuizItem.module.scss';

const QuizItem = ({ option, selectedOptions, correctSelected, onSelect, letter }) => {
    const handleClick = () => {
        if (!correctSelected && !selectedOptions.includes(option.answer)) {
            onSelect(option);
        }
    };

    let symbol = null;

    if (selectedOptions.includes(option.answer) || (correctSelected && option.correct)) {
        symbol = option.correct ? '✔' : (selectedOptions.includes(option.answer) ? '✖' : null);
    }

    return (
        <button
            className={`${styles.cont} controller-target-answer`}
            onClick={handleClick}
            disabled={correctSelected || selectedOptions.includes(option.answer)}
            data-action={letter}
            tabIndex={-1}
        >
            <span className={styles.option}>
                <span className={styles.letter}>{letter}</span>. {option.answer}
            </span>
            <span className={styles.symbol} style={{ fontSize: '1.4rem', visibility: symbol ? 'visible' : 'hidden' }}>
                {symbol || '✔'}
            </span>
        </button>
    );
};

export default QuizItem;

