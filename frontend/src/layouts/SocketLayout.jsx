import { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';
import Spinner from '../components/Spinner/Spinner';

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
        socketRef.current = io("http://localhost:3000");

        const handleIncoming = (incomingData) => {
            if (!incomingData) return;

            // show spinner immediately if Node-RED signals loading via newCoordinates
            if (incomingData.loading) {
                setLoading(true);
                return;
            }

            // update data when real payload arrives
            if (incomingData.type === namespace) {
                setData(incomingData.payload ?? incomingData);
                setLoading(false); // hide spinner
            }
        };

        // listen for actual data and loading events
        socketRef.current.on("newData", handleIncoming);
        socketRef.current.on("newCoordinates", handleIncoming);

        // request initial data
        socketRef.current.emit("requestData", { type: namespace });
        setLoading(true);

        return () => {
            socketRef.current.off("newData", handleIncoming);
            socketRef.current.off("newCoordinates", handleIncoming);
            socketRef.current.disconnect();
        };
    }, [namespace]);

    if (loading) return <Spinner />;

    return <>{children(data)}</>;
};

export default SocketLayout;

