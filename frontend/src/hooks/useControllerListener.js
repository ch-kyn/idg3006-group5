import { useEffect, useRef } from "react";
import { io } from "socket.io-client";

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL;

export default function useControllerListener(ready = true) {
    const focusIndex = useRef(0);
    const elements = useRef([]);
    const socketRef = useRef(null);
    const isThrottled = useRef(false);

    // track elements and observe DOM changes
    useEffect(() => {
        if (!ready) return;

        const updateElements = () => {
            const newEls = Array.from(document.querySelectorAll(".controller-target"));
            elements.current = newEls;

            if (newEls.length > 0) {
                focusIndex.current = 0;
                newEls[0].focus();
            }
        };

        updateElements();

        // observe when elements with 'controller-target' changes
        const observer = new MutationObserver(updateElements);
        observer.observe(document.body, { childList: true, subtree: true });

        return () => observer.disconnect();
    }, [ready]);


    // attach socket listener once
    useEffect(() => {
        if (!ready) return;

        if (!socketRef.current) {
            socketRef.current = io(SOCKET_URL);
        }
        const socket = socketRef.current;

        const moveFocus = (direction) => {
            const els = elements.current;
            if (!els || els.length === 0) return;

            const currentEl = els[focusIndex.current];
            const allowed = currentEl.dataset.nav?.split(" ") || [];

            if (!allowed.includes(direction)) return;

            let nextIndex = focusIndex.current;
            const len = els.length;

            do {
                if (direction === "up" || direction === "left") {
                    nextIndex = (nextIndex - 1 + len) % len;
                } else if (direction === "down" || direction === "right") {
                    nextIndex = (nextIndex + 1) % len;
                }

                if (nextIndex === focusIndex.current) return; // full loop, stop
            } while (!(els[nextIndex].dataset.nav?.split(" ")?.includes(direction)));

            focusIndex.current = nextIndex;
            els[focusIndex.current].focus();
        };

        const handleControl = ({ action }) => {
            // handle navigation actions immediately
            if (action === "invention") {
                window.location.href = "/invention";
                return;
            }

            if (action === "quiz") {
                window.location.href = "/quiz";
                return;
            }
            if (action === "about") {
                window.location.href = "/about";
                return;
            }

            // throttle movement/select actions
            if (isThrottled.current) return;
            isThrottled.current = true;
            setTimeout(() => (isThrottled.current = false), 150);

            const els = elements.current;
            if (!els || els.length === 0) return;

            switch (action) {
                case "up":
                case "down":
                case "left":
                case "right":
                    moveFocus(action);
                    break;

                case "select": {
                    // click the currently focused element
                    const el = els[focusIndex.current];
                    if (el && !el.disabled) el.click();
                    break;
                }

                case "A":
                case "B":
                case "C":
                case "D": {
                    // click on btn with the corresponding value in 'data-action'
                    const btns = Array.from(document.querySelectorAll(".controller-target-answer"));
                    const targetBtn = btns.find(el => el.dataset.action === action);
                    if (targetBtn) {
                        targetBtn.click();
                    } else {
                        console.warn("No button found for action:", action);
                    }
                    break;
                }
                
                default:
                    console.warn("Unknown action:", action);
            }
        };

        socket.on("control", handleControl);

        return () => {
            socket.off("control", handleControl);
        };
    }, [ready]);
}
