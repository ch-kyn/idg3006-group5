import { useRef, useEffect } from "react";
import { io } from "socket.io-client";
import InfoButton from "../InfoButton/InfoButton";
import styles from "./ControllerPage.module.scss";

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL;

const ControllerPage = () => {
    const socketRef = useRef(null);
    console.log("DOES .ENV WORK OMG: ", import.meta.env.VITE_SOCKET_URL);
    // create socket once
    if (!socketRef.current) {
        socketRef.current = io(SOCKET_URL, { transports: ["polling", "websocket"] });
    }

    const socket = socketRef.current;

    // connect and handle socket events (optional logging)
    useEffect(() => {
        socket.on("connect", () => console.log("Connected:", socket.id));
        socket.on("connect_error", (err) => console.error("Socket error:", err));

        return () => {
            socket.disconnect();
        };
    }, [socket]);

    // send controller action to server
    const send = (action) => {
        socket.emit("control", { action });
    };

    return (
        <div className={styles.cont}>
            <InfoButton />

            <div className={styles.main}>
                <div className={styles.top}>
                    <div className={styles.quizButtons}>
                        <button
                            aria-label="Answer A, Red"
                            className={`${styles.quizButton} ${styles.quizRed}`}
                            onClick={() => send("A")}
                        >
                            A
                        </button>
                        <button
                            aria-label="Answer B, Green"
                            className={`${styles.quizButton} ${styles.quizGreen}`}
                            onClick={() => send("B")}
                        >
                            B
                        </button>
                        <button
                            aria-label="Answer C, Yellow"
                            className={`${styles.quizButton} ${styles.quizYellow}`}
                            onClick={() => send("C")}
                        >
                            C
                        </button>
                        <button
                            aria-label="Answer D, Blue"
                            className={`${styles.quizButton} ${styles.quizBlue}`}
                            onClick={() => send("D")}
                        >
                            D
                        </button>
                    </div>
                </div>
                <div className={styles.btm}>
                    <div className={styles.arrows}>
                        {/* <div className={styles.row}>
                            <button className={styles.arrow} onClick={() => send("up")}>
                                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M440-160v-487L216-423l-56-57 320-320 320 320-56 57-224-224v487h-80Z" /></svg>
                            </button>
                        </div>
                        <div className={styles.row}>
                            <button className={styles.arrow} onClick={() => send("left")}>
                                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="m313-440 224 224-57 56-320-320 320-320 57 56-224 224h487v80H313Z" /></svg>
                            </button>
                            <div className={styles.spacer} />
                            <button className={styles.arrow} onClick={() => send("right")}>
                                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M647-440H160v-80h487L423-744l57-56 320 320-320 320-57-56 224-224Z" /></svg>
                            </button>
                        </div>
                        <div className={styles.row}>
                            <button className={styles.arrow} onClick={() => send("down")}>
                                <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M440-800v487L216-537l-56 57 320 320 320-320-56-57-224 224v-487h-80Z" /></svg>
                            </button>
                        </div> */}
                        <button className={styles.select} onClick={() => send("select")}>CONTINUE</button>
                    </div>

                    <div className={styles.nav}>
                        <button className={styles.nav__btn} onClick={() => send("invention")}>
                            Invention
                        </button>
                        <button className={styles.nav__btn} onClick={() => send("quiz")}>
                            Quiz
                        </button>
                        <button className={styles.nav__btn} onClick={() => send("about")}>
                            About
                        </button>
                    </div>
                </div>

                <div className={styles.calibrateBox}>
                    <p>
                        Please click <strong>Start</strong> before spinning the globe to find a country. <br />
                    </p>
                    <button className={styles.calibrateBtn} onClick={() => socket.emit("start", { "start": true })}>
                        Start
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ControllerPage;
