import { useEffect, useRef } from "react";
import { io } from "socket.io-client";
import { useLocation } from "react-router-dom";

const SOCKET_URL = "http://192.168.10.134:3000/";

export default function useControllerListener(ready = true) {
    const location = useLocation();
    const focusIndex = useRef(0);
    const elements = useRef([]);
    const socketRef = useRef(null);
    const isThrottled = useRef(false);

    // re-query elements whenever location changes
    useEffect(() => {
        if (!ready) return;

        elements.current = Array.from(document.querySelectorAll(".controller-target"));
        if (elements.current.length > 0) {
            focusIndex.current = 0;
            elements.current[focusIndex.current].focus();
        }
    }, [location.pathname, ready]);

    // attach socket listener
    useEffect(() => {
        if (!ready) return;

        socketRef.current = io(SOCKET_URL);

        const moveFocus = (direction) => {
            const els = elements.current;
            if (!els || els.length === 0) return;

            const currentEl = els[focusIndex.current];
            const allowed = currentEl.dataset.nav?.split(" ") || [];

            // only move if direction is allowed for the current element
            if (!allowed.includes(direction)) return;

            let nextIndex = focusIndex.current;
            const len = els.length;

            do {
                if (direction === "up" || direction === "left") {
                    nextIndex = (nextIndex - 1 + len) % len;
                } else if (direction === "down" || direction === "right") {
                    nextIndex = (nextIndex + 1) % len;
                }

                if (nextIndex === focusIndex.current) return;
            } while (!(els[nextIndex].dataset.nav?.split(" ")?.includes(direction)));

            focusIndex.current = nextIndex;
            els[focusIndex.current].focus();
        };

        const handleControl = ({ action }) => {
            if (isThrottled.current) return;
            const els = elements.current;
            if (!els || els.length === 0) return;

            isThrottled.current = true;
            setTimeout(() => (isThrottled.current = false), 150);

            switch (action) {
                case "up":
                case "down":
                case "left":
                case "right":
                    moveFocus(action);
                    break;

                case "select":
                    els[focusIndex.current].click();
                    break;

                case "inventions":
                    window.location.href = "/invention";
                    break;
                case "quiz":
                    window.location.href = "/quiz";
                    break;
                case "about":
                    window.location.href = "/about";
                    break;

                default:
                    console.warn("Unknown action:", action);
            }
        };

        socketRef.current.on("control", handleControl);

        return () => {
            if (socketRef.current) {
                socketRef.current.off("control", handleControl);
                socketRef.current.disconnect();
            }
        };
    }, [ready]);
}
