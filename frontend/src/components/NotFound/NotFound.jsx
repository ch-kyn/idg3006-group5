import { Link } from "react-router-dom";
import { titleCase } from "../../utils/titleCase";
import styles from './NotFound.module.scss';

const NotFound = (country = null) => {
    // some fallback options...
    const options = [
        { imageUrl: "images/other/dolphin.webp", extra: "Anyways... here is a dolphin. 🐬✨" },
        { imageUrl: "images/other/turtle.webp", extra: "Who knows what adventures await there? 🐢" },
        { imageUrl: "images/other/fish.webp", extra: "Sometimes you just have to go with the flow. 🌊🐟" },
        { imageUrl: "images/other/norway.webp", extra: "Maybe it's time to head back to Norway? 🇳🇴❄️" },
        { imageUrl: "images/other/sun.webp", extra: "Guess the sun found you first! ☀️" },
        { imageUrl: "images/other/space.webp", extra: "Keep looking up... who knows what you’ll find! 🌌" },
    ];

    // pick a random option
    const randomOption = options[Math.floor(Math.random() * options.length)];
    console.log(country);

    return (
        <div className={styles.cont}>
            <img
                src={`${import.meta.env.VITE_SOCKET_URL}${randomOption.imageUrl}`}
                alt="Fallback illustration"
                className={styles.img}
            />

            <div className={styles.info}>
                <h1 className={styles.title}>404 - Country Not Found</h1>
                <p className={styles.text}> 
                {country.country
                    ? <>Sorry, <strong>{titleCase(country.country)}</strong> is not currently available for <strong>Invention</strong> or <strong>About</strong> mode.</>
                    : 'Sorry, this location appears to be in the ocean or an unmapped area.'} {randomOption.extra}
                </p>
                <Link to="/" className={`${styles.btn} controller-target`} data-nav="select">Go back home</Link>
            </div>
        </div>
    );
};

export default NotFound;
