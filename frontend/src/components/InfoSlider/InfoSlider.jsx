import { useState, useRef, useEffect } from "react";
import styles from './InfoSlider.module.scss';

const InfoSlider = ({ data }) => {
    const originalSlides = [
        data.information?.general,
        data.information?.description,
        data.information?.extra,
    ];

    const slides = [
        originalSlides[originalSlides.length - 1],
        ...originalSlides,
        originalSlides[0],
    ];

    const [index, setIndex] = useState(1); // real first slide
    const [transition, setTransition] = useState(true);
    const [isSliding, setIsSliding] = useState(false); // block fast clicks
    const timeoutRef = useRef(null);

    const nextSlide = () => {
        if (isSliding) return;
        setIsSliding(true);
        setIndex(prev => prev + 1);
    };

    const prevSlide = () => {
        if (isSliding) return;
        setIsSliding(true);
        setIndex(prev => prev - 1);
    };

    useEffect(() => {
        if (index === slides.length - 1) {
            timeoutRef.current = setTimeout(() => {
                setTransition(false);
                setIndex(1);
            }, 300);
        } else if (index === 0) {
            timeoutRef.current = setTimeout(() => {
                setTransition(false);
                setIndex(slides.length - 2);
            }, 300);
        }

        // allow next click after normal transition
        const t = setTimeout(() => setIsSliding(false), 300);

        return () => {
            clearTimeout(timeoutRef.current);
            clearTimeout(t);
        };
    }, [index, slides.length]);

    useEffect(() => {
        if (!transition) requestAnimationFrame(() => setTransition(true));
    }, [transition]);

    const getDotIndex = (idx) => {
        if (idx === 0) return originalSlides.length - 1;
        if (idx === slides.length - 1) return 0;
        return idx - 1;
    };

    return (
        <div className={styles.sliderWrapper}>

            <button className={`${styles.arrow} ${styles.right} controller-target`} data-nav="select" onClick={nextSlide}>
                &#10095;
            </button>

            <div className={styles.sliderViewport}>
                <div
                    className={styles.box__cont}
                    style={{
                        transform: `translateX(-${index * 100}%)`,
                        transition: transition ? "transform 0.5ßs ease" : "none",
                    }}
                >
                    {slides.map((text, i) => (
                        <div key={i} className={styles.box}>
                            <p>{text}</p>
                        </div>
                    ))}
                </div>
            </div>

            <button className={`${styles.arrow} ${styles.left} controller-target`} data-nav="select" onClick={prevSlide}>
                &#10094;
            </button>

            <div className={styles.dots}>
                {originalSlides.map((_, i) => (
                    <span
                        key={i}
                        className={`${styles.dot} ${i === getDotIndex(index) ? styles.active : ""}`}
                        onClick={() => !isSliding && setIndex(i + 1)}
                    />
                ))}
            </div>
        </div>
    );
};

export default InfoSlider;
