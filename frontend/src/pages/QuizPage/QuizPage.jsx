import { useEffect, useState } from 'react';
import SocketLayout from "../../layouts/SocketLayout";
import Logo from '../../components/Logo/Logo';
import Quiz from "../../components/Quiz/Quiz";
import ProgressBar from "../../components/ProgressBar/ProgressBar";
import styles from "./QuizPage.module.scss";

const QuizPage = () => {
    const [current, setCurrent] = useState(1);

    useEffect(() => {
        document.title = 'Quiz 📝';
    }, []);
    

    return (
        <SocketLayout namespace="quiz">
            {(data) => {                
                const questions = data?.questions || [];

                return (
                    <div className={styles.cont}>
                        <div>
                            <Logo />
                            <ProgressBar 
                                length={questions.length} 
                                current={Math.min(current, questions.length)} 
                                country={data.country}
                            />
                        </div>

                        <div className={styles.quiz}>
                            <Quiz 
                                questions={questions} 
                                country={data.country}
                                onProgress={setCurrent} 
                            />
                        </div>
                    </div>
                );
            }}
        </SocketLayout>
    );
};

export default QuizPage;
