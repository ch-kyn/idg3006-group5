import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import Invention from '../../components/Invention/Invention';
import styles from './InventionPage.module.scss';

const InventionPage = () => {
    const [data, setData] = useState([]);

    useEffect(() => {
        const socket = io('http://localhost:3000');

        socket.on('newData', (data) => {
            console.log('Received from Node-RED:', data);
            setData(data);
        });

        return () => socket.disconnect();
    }, []);

    return (
        <div className={styles.cont}>
            <Invention data={data.invention} country={data.country} />
        </div>
    );
}

export default InventionPage;