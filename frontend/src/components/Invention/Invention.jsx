// import { useState } from 'react';
import styles from './Invention.module.scss';

const Invention = ({ data, country }) => {
    return (
        data && (
            <div className={styles.main}>
                <section className={styles.main__cont}>
                    <img src={`http://localhost:3000/${data.image}`} alt={data.name} className={styles.img}/>
                </section>
                
                <section className={styles.main__cont}>
                    <div className={styles.info}>
                        <h1>{data.name}</h1>
                        <div className={styles.text}>
                            <span>Country: {country}</span>
                            <span>Inventor: {data.inventor}</span>
                            <span>Year: {data.year}</span>
                        </div>
                        <div className={styles.box__cont}>
                            <div className={styles.box}>
                                <p>{data.information?.general}</p>
                            </div>
                            <div className={styles.box}>
                                <p>{data.information?.description}</p>
                            </div>
                            <div className={styles.box}>
                                <p>{data.information?.extra}</p>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        )
    );
};

export default Invention;
