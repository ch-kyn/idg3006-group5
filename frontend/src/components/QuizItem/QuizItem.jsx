import styles from './QuizItem.module.scss';

const QuizItem = ({ option, correct, selected, onSelect, letter }) => {
    const handleClick = () => onSelect(option);

    let className = styles.option;
    if (selected) {
        if (option === correct) className = styles.correct;
        else if (option === selected) className = styles.wrong;
    }

	return (
		<button className={styles.cont} onClick={handleClick}>
			<span className={styles.letter}>{letter}</span>. {option.answer}
		</button>
	);
};

export default QuizItem;

// const QuizItem = ({ option, correct, selected, onSelect, letter }) => {
//     const handleClick = () => onSelect(option);

//     let className = styles.option;
//     if (selected) {
//         if (option === correct) className = styles.correct;
//         else if (option === selected) className = styles.wrong;
//     }

//     return (
//         <button className={className} onClick={handleClick}>
//             <span>{letter}. {option.answer || option}</span>
//         </button>
//     );
// };

