import { Link } from "react-router-dom";
import styles from './Menu.module.scss';

const Menu = () => {
	return (
		<ul className={styles.menu}>
			<li>
				<Link to="/inventions" className={styles.menu__btn}>💡 Inventions</Link>
			</li>
			<li>
				<Link to="/quiz" className={styles.menu__btn}>📝 Quiz</Link>
			</li>
			<li>
				<Link to="/info" className={styles.menu__btn}>🏳️ About</Link>
			</li>
		</ul>
	);
};

export default Menu;
