import styles from './QuizAnswer.module.scss';

const QuizAnswer = ({ option, correct, selected, onSelect, letter }) => {
	if (!option) return null; 

	const handleClick = () => {
		if (onSelect) onSelect(option);
	};

	return (
		<button className={styles.cont} onClick={handleClick}>
			<span className={styles.letter}>{letter}</span>. {option.answer}
		</button>
	);
};

export default QuizAnswer;
