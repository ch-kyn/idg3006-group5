import SocketLayout from "../../layouts/SocketLayout";
import Logo from '../../components/Logo/Logo';
import Quiz from "../../components/Quiz/Quiz";
import ProgressBar from "../../components/ProgressBar/ProgressBar";
import NotFound from "../../components/NotFound/NotFound";
import styles from "./QuizPage.module.scss";
import { useState } from "react";

const QuizPage = () => {
    const [current, setCurrent] = useState(1);

    return (
        <SocketLayout namespace="quiz" title="Quiz 📝">
            {(data) => {
                const questions = data?.questions || [];
                if (data?.error || questions.length === 0) return (<NotFound />);

                const country = data?.country;

                return (
                    <div className={styles.cont}>
                        <div>
                            <Logo />
                            <ProgressBar
                                length={questions.length}
                                current={Math.min(current, questions.length)}
                                country={country}
                            />
                        </div>

                        <div className={styles.quiz}>
                            <Quiz
                                questions={questions}
                                country={country}
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
