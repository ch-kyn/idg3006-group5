import { useEffect } from 'react';
import SocketLayout from '../../layouts/SocketLayout.jsx';
import Invention from '../../components/Invention/Invention';

const InventionPage = () => {
    useEffect(() => {
        document.title = 'Inventions 💡';
    }, []);

    return (
        <SocketLayout namespace="invention">
            {(data) => <Invention data={data.invention} country={data.country} />}
        </SocketLayout>
    );
};

export default InventionPage;
