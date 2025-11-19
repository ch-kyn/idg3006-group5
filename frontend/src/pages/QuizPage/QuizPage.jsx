import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import Quiz from '../Quiz/Quiz';
import ProgressBar from '../ProgressBar/ProgressBar';
import styles from './QuizPage.module.scss';

const QuizPage = () => {
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
            <h1>Quiz</h1>
            <ProgressBar length={data.length} />
            <Quiz questions={data} />
        </div>
    );
}

export default QuizPage;