import { useEffect, useState, useRef } from "react";
import { io } from "socket.io-client";
import useControllerListener from "../hooks/useControllerListener";
import Spinner from "../components/Spinner/Spinner";

const SocketLayout = ({ namespace, title, children }) => {
	const [data, setData] = useState(null);
	const [loading, setLoading] = useState(true);
	const socketRef = useRef(null);

	// set page title
	useEffect(() => {
		if (title) {
			document.title = title;
		}
	}, [title]);

	useEffect(() => {
		console.log("Initializing socket for namespace:", namespace);
		const socket = io("http://localhost:3000", { autoConnect: true });
		socketRef.current = socket;

		// normalize incoming payload
		const normalize = (msg) => msg.payload ?? msg;

		// handle incoming newData / loading
		const handleIncoming = (incomingData) => {
			if (!incomingData) return;

			const msg = normalize(incomingData);

			// only handle events for this namespace
			if (msg.type !== namespace) return;

			if (msg.loading) {
				console.log(`[${namespace}] Loading started`);
				setLoading(true);
				return;
			}

			console.log(`[${namespace}] Data received`, msg);
			setData(msg);
			setLoading(false);
		};

		// listen for events
		socket.on("newData", handleIncoming);
		socket.on("loading", handleIncoming);

		socket.on("connect", () => {
			console.log("Socket connected! ID:", socket.id);
			if (namespace) {
				socket.emit("requestData", { type: namespace });
				setLoading(true);
			}
		});

		socket.on("disconnect", (reason) =>
			console.warn("Socket disconnected:", reason)
		);
		socket.on("connect_error", (err) =>
			console.error("Socket connection error:", err)
		);

		// dleanup on unmount or namespace change
		return () => {
			socket.off("newData", handleIncoming);
			socket.off("loading", handleIncoming);
			socket.disconnect();
		};
	}, [namespace]);

	// activate controller listener only when not loading
	useControllerListener(!loading);

	if (loading) return <Spinner />;
	return <>{children(data)}</>;
};

export default SocketLayout;

