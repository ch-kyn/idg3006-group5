import { useState } from "react";
import styles from "./Carousel.module.scss";

const Carousel = ({ artworks }) => {
	const [currentIndex, setCurrentIndex] = useState(0);

	if (!artworks || artworks.length === 0) return null;

	const prevSlide = () => {
		setCurrentIndex((prev) => (prev === 0 ? artworks.length - 1 : prev - 1));
	};

	const nextSlide = () => {
		setCurrentIndex((prev) => (prev === artworks.length - 1 ? 0 : prev + 1));
	};

	return (
		<div className={styles.cont}>
			{/* slides */}
			<div className={styles.slide}>
				<img
					src={artworks[currentIndex].primaryImageSmall}
					alt={artworks[currentIndex].title}
				/>
				<div className={styles.caption}>
					<h3>{artworks[currentIndex].title}</h3>
					{/* {artworks[currentIndex].description && (
            <p>{artworks[currentIndex].description}</p>
          )} */}
				</div>
			</div>

			{/* controls */}
			<button
				className={`${styles.control} ${styles.control__left}`}
				onClick={prevSlide}
			>
				&#10094;
			</button>
			<button
				className={`${styles.control} ${styles.control__right}`}
				onClick={nextSlide}
			>
				&#10095;
			</button>

			<div className={styles.indicators}>
				{artworks.map((_, idx) => (
					<span
						key={idx}
						className={idx === currentIndex ? "active" : ""}
						onClick={() => setCurrentIndex(idx)}
					></span>
				))}
			</div>
		</div>
	);
};

export default Carousel;
