import styles from './Invention.module.scss';
import InfoSlider from '../InfoSlider/InfoSlider';
import Logo from '../Logo/Logo';

const Invention = ({ data, country }) => {
    return (
        data && (
            <div className={styles.main}>
                <section className={styles.main__cont}>
                    <img src={`${import.meta.env.VITE_SOCKET_URL}${data.image}`} alt={data.name} className={styles.img}/>
                </section>
                
                <section className={styles.main__cont}>
                    <div className={styles.info}>
                        <Logo />
                        <InfoSlider data={data} />
                        <div className={styles.text__cont}>
                               <div className={styles.card}>
                                    <h1 className={styles.title}>{data.name}</h1>
                                    
                                    <div className={styles.details}>
                                        <p className={styles.text}><span className={styles.label}>Country:</span> {country}</p>
                                        <p className={styles.text}><span className={styles.label}>Inventor:</span> {data.inventor}</p>
                                        <p className={styles.text}><span className={styles.label}>Year:</span> {data.year}</p>
                                    </div>
                                </div>
                        </div>
                    </div>
                </section>
            </div>
        )
    );
};

export default Invention;
