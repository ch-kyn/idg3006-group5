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
            className={`${styles.cont} controller-target`}
            onClick={handleClick}
            disabled={correctSelected || selectedOptions.includes(option.answer)}
        >
            <span className={styles.option}>
                <span className={styles.letter}>{letter}</span>. {option.answer}
            </span>
            <span className={styles.symbol} style={{ fontSize: '1.4rem', visibility: symbol ? 'visible' : 'hidden' }}>
                {symbol || '✔'} {/* placeholder, won't be seen if hidden */}
            </span>
        </button>
    );
};

export default QuizItem;
