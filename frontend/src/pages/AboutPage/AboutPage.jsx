import SocketLayout from '../../layouts/SocketLayout.jsx';
import Logo from '../../components/Logo/Logo';
import AboutCard from '../../components/AboutCard/AboutCard.jsx';
import NotFound from '../../components/NotFound/NotFound.jsx';
import styles from './AboutPage.module.scss';


const AboutPage = () => {
    return (
        <SocketLayout namespace="about" title="About 🏳️">
            {(data) => {
                console.log(data);
                if (data.error) return (<NotFound country={data.requested} />);

                const info = data.information;
                const gdp = info.gdp_total_usd;

                return (
                    <div className={styles.cont}>
                        <Logo />
                        <div className={styles.about}>
                            <div className={`${styles.col} ${styles.col__left}`}>
                                 <div className={styles.general}>
                                    <div className={styles.images}>
                                        <img src={`${import.meta.env.VITE_SOCKET_URL}${info.images['flag']}`} alt={`${data.country} flag`} className={styles.img} width={100} />
                                        <img src={`${import.meta.env.VITE_SOCKET_URL}${info.images['map']}`} alt={`${data.country} on the world map`} className={`${styles.img} ${styles.border}`} width={100} />
                                    </div>
                                    <h1>{data.country}</h1>
                                    <div className={styles.general__text}>
                                        <p className={styles.text}><span className={styles.label}>Capital:</span> {info.capital}</p>
                                        <p className={styles.text}><span className={styles.label}>Population:</span> {info.population.toLocaleString()}</p>
                                        <p className={styles.text}><span className={styles.label}>Area:</span> {info.area_km2.toLocaleString()} km²</p>
                                        <p className={styles.text}><span className={styles.label}>National Day:</span> {info.national_day}</p>
                                        <p className={styles.text}><span className={styles.label}>National Animal:</span> {info.national_animal}</p>
                                        <br />
                                        <p className={styles.text}><span className={styles.label}>Currency:</span> {info.currency}</p>
                                        <p className={styles.text}><span className={styles.label}>Total GDP:</span> {gdp.toLocaleString()} USD</p>
                                        <p className={styles.text}><span className={styles.label}>GDP per capita:</span> {(gdp / info.population).toFixed(2)} USD</p>
                                    </div>
                                </div>
                            </div>

                            <div className={`${styles.col} ${styles.col__right}`}>
                                <AboutCard title="Popular Dishes" dataArr={info.popular_dishes} image={`${import.meta.env.VITE_SOCKET_URL}${info.images['food']}`} />
                                <AboutCard title="Famous People" dataArr={info.famous_people} />
                            </div>
                            <div className={`${styles.col} ${styles.col__right}`}>
                                <AboutCard title="Exports" dataArr={info.exports} />
                                <AboutCard title="Heritage Places" dataArr={info.places_heritage} image={`${import.meta.env.VITE_SOCKET_URL}${info.images['place']}`} />
                            </div>
                        </div>
                    </div>
                );
            }}
        </SocketLayout>
    );
}

export default AboutPage;
