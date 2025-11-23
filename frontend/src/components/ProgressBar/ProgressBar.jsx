import styles from './ProgressBar.module.scss';

const ProgressBar = ({ length = 1, current = 1, country }) => {
    const percentage = Math.min((current / length) * 100, 100);

    return (
        <div className={styles.cont}>
            <span className={styles.text}>
                {`${country} Trivia - Question ${current}/${length}`}
            </span>

            <div className={styles.progressContainer}>
                <div
                    className={styles.progressBar}
                    style={{ width: `${percentage}%` }}
                ></div>
            </div>
        </div>
    );
};

export default ProgressBar;
