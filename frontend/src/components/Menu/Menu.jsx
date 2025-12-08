import { Link } from "react-router-dom";
import styles from './Menu.module.scss';

const Menu = () => {
	return (
		<ul className={styles.menu}>
			<li>
				<Link to="/invention" className={`${styles.menu__btn} controller-target`} data-nav="select">💡 Invention</Link>
			</li>
			<li>
				<Link to="/quiz" className={`${styles.menu__btn} controller-target`} data-nav="select">📝 Quiz</Link>
			</li>
			<li>
				<Link to="/about" className={`${styles.menu__btn} controller-target`} data-nav="select">🏳️ About</Link>
			</li>
		</ul>
	);
};

export default Menu;
