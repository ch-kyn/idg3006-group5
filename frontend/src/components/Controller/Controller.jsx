// import { io } from "socket.io-client";
// import styles from "./Controller.module.scss";

// const socket = io("http://YOUR-IP:3000");

// const Controller = () => {
//     const send = (action) => {
//         socket.emit("control", { action });
//     };

//     return (
//         <div className={styles.wrapper}>
//             <button onClick={() => send("up")}>⬆️</button>

//             <div className={styles.middle}>
//                 <button onClick={() => send("left")}>⬅️</button>
//                 <button onClick={() => send("down")}>⬇️</button>
//                 <button onClick={() => send("right")}>➡️</button>
//             </div>

//             <div className={styles.nav}>
//                 <button onClick={() => send("inventions")}>Inventions</button>
//                 <button onClick={() => send("info")}>Info</button>
//                 <button onClick={() => send("quiz")}>Quiz</button>
//             </div>
//         </div>
//     );
// };

// export default Controller;
