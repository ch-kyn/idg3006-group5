import { useState, useEffect } from "react";
import styles from "./Spinner.module.scss";
import funFacts from './funFact.json';

const Spinner = () => {
	const [fact, setFact] = useState("");

	useEffect(() => {
		const randomIndex = Math.floor(Math.random() * funFacts.length);
		setFact(funFacts[randomIndex]);
	}, []);

	return (
		<div className={styles.wrapper}>
			<div className={styles.earth}>
				<div className={styles.continents}></div>
			</div>

			<p className={styles.text}>Did you know...</p>
			<p className={styles.fact}>{fact}</p>
		</div>
	);
};

export default Spinner;
