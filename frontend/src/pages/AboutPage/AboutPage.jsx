import SocketLayout from '../../layouts/SocketLayout.jsx';
import Logo from '../../components/Logo/Logo';
import AboutCard from '../../components/AboutCard/AboutCard.jsx';
import styles from './AboutPage.module.scss';


const AboutPage = () => {
    return (
        <SocketLayout namespace="about" title="About 🏳️">
            {(data) => {
                const info = data.information;
                const gdp = info.gdp_total_usd;

                return (
                    <div className={styles.cont}>
                        <Logo />
                        <div className={styles.about}>
                            <div className={`${styles.col} ${styles.col__left}`}>
                                <h1>{data.country}</h1>
                                <div className={styles.images}>
                                    <img src={`http://localhost:3000/${info.images['flag']}`} alt={`${data.country} flag`} className={styles.img} width={100} />
                                    <img src={`http://localhost:3000/${info.images['map']}`} alt={`${data.country} on the world map`} className={`${styles.img} ${styles.border}`} width={100} />
                                </div>

                                 <div className={styles.general}>
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

                            <div className={`${styles.col} ${styles.col__right}`}>
                                <AboutCard title="Popular Dishes" dataArr={info.popular_dishes} image={`http://localhost:3000/${info.images['food']}`} />
                                <AboutCard title="Famous People" dataArr={info.famous_people} />
                                <AboutCard title="Heritage Places" dataArr={info.places_heritage} image={`http://localhost:3000/${info.images['place']}`} />
                                <AboutCard title="Exports" dataArr={info.exports} />
                            </div>
                        </div>
                    </div>
                );
            }}
        </SocketLayout>
    );
}

export default AboutPage;
