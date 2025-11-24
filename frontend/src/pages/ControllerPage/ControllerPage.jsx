import { useEffect, useRef } from "react";
import { io } from "socket.io-client";
import styles from "./ControllerPage.module.scss";

const SOCKET_URL = "http://192.168.10.134:3000";

const ControllerPage = () => {
    const socketRef = useRef(null);
    const buttonRefs = useRef([]);
    const focusIndex = useRef(0);

    // create socket once
    if (!socketRef.current) {
        socketRef.current = io(SOCKET_URL, { transports: ["websocket"] });
    }

    const socket = socketRef.current;

    useEffect(() => {
        const focusButton = () => {
            if (buttonRefs.current.length > 0) {
                buttonRefs.current[focusIndex.current]?.focus();
            }
        };

        const handleControl = ({ action }) => {
            if (buttonRefs.current.length === 0) return;

            switch (action) {
                case "up":
                case "left":
                    focusIndex.current =
                        (focusIndex.current - 1 + buttonRefs.current.length) %
                        buttonRefs.current.length;
                    break;
                case "down":
                case "right":
                    focusIndex.current =
                        (focusIndex.current + 1) % buttonRefs.current.length;
                    break;
                case "select":
                    buttonRefs.current[focusIndex.current]?.click();
                    break;
                default:
                    console.warn("Unknown action:", action);
            }

            focusButton();
        };

        socket.on("connect", () => console.log("Connected:", socket.id));
        socket.on("connect_error", (err) => console.error("Socket error:", err));
        socket.on("control", handleControl);

        focusButton();

        return () => {
            socket.off("control", handleControl);
            socket.disconnect();
        };
    }, [socket]);

    const send = (action) => socket.emit("control", { action });

    return (
        <div className={styles.wrapper}>
            <button ref={(el) => (buttonRefs.current[0] = el)} onClick={() => send("up")}>
                ⬆️
            </button>

            <div className={styles.middle}>
                <button ref={(el) => (buttonRefs.current[1] = el)} onClick={() => send("left")}>
                    ⬅️
                </button>
                <button ref={(el) => (buttonRefs.current[2] = el)} onClick={() => send("down")}>
                    ⬇️
                </button>
                <button ref={(el) => (buttonRefs.current[3] = el)} onClick={() => send("right")}>
                    ➡️
                </button>
            </div>

            <button ref={(el) => (buttonRefs.current[4] = el)} onClick={() => send("select")}>✅ SELECT</button>

            <div className={styles.nav}>
                <button ref={(el) => (buttonRefs.current[5] = el)} onClick={() => send("invention")}>
                    Invention
                </button>
                <button ref={(el) => (buttonRefs.current[6] = el)} onClick={() => send("about")}>
                    About
                </button>
                <button ref={(el) => (buttonRefs.current[7] = el)} onClick={() => send("quiz")}>
                    Quiz
                </button>
            </div>
        </div>
    );
};

export default ControllerPage;
