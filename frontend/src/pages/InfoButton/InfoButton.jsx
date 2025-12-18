import { useState, useEffect } from "react";
import styles from "./InfoButton.module.scss";

export default function InfoButton() {
    const [showInfo, setShowInfo] = useState(false);

    // close with ESC key
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === "Escape") {
                setShowInfo(false);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, []);

    return (
        <>
            <button
                className={styles.infoBtn}
                onClick={() => setShowInfo(true)}
                aria-label="Open controller guide"
            >
                <svg xmlns="http://www.w3.org/2000/svg" height="26px" viewBox="0 -960 960 960" width="26px" fill="#e3e3e3">
                    <path d="M440-280h80v-240h-80v240Zm40-320q17 0 
                    28.5-11.5T520-640q0-17-11.5-28.5T480-680q-17 
                    0-28.5 11.5T440-640q0 17 11.5 28.5T480-600Zm0
                    520q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480
                    q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83
                    0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5
                    156T763-197q-54 54-127 85.5T480-80Z" />
                </svg>
            </button>

            {/* for modal */}
            {showInfo && (
                <div
                    className={styles.overlay}
                    onClick={() => setShowInfo(false)}
                >
                    <div
                        className={styles.modal}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h2>Controller Guide</h2>

                        <div className={styles.section}>
                            <h3>Continue</h3>
                            <p>Confirms the currently highlighted option</p>
                        </div>

                        <div className={styles.section}>
                            <h3>A / B / C / D</h3>
                            <p>Answer quiz questions</p>
                        </div>

                        <div className={styles.section}>
                            <h3>Navigation Buttons</h3>
                            <ul className={styles.list}>
                                <li><strong>Invention</strong> — View inventions from the selected country</li>
                                <li><strong>Quiz</strong> — Start a new quiz for the selected country</li>
                                <li><strong>About</strong> — Learn more about the selected country</li>
                            </ul>
                        </div>

                        <button
                            className={styles.closeBtn}
                            onClick={() => setShowInfo(false)}
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </>
    );
}
