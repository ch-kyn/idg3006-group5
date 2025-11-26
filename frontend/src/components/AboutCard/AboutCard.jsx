import styles from './AboutCard.module.scss';

const AboutCard = ({ title, dataArr, bgColor, image }) => {
    return (
        <div
            className={styles.card}
            style={{ backgroundColor: bgColor || 'transparent' }}
        >
            {image && (
                <div className={styles.imageContainer}>
                    <img src={image} alt={title} className={styles.image} />
                </div>
            )}
            <div className={styles.content}>
                <h2 className={styles.title}>{title}</h2>
                <ul className={styles.list}>
                    {dataArr.map((item, idx) => (
                        <li key={idx}>{item}</li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default AboutCard;

