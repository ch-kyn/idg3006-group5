import SocketLayout from '../../layouts/SocketLayout.jsx';
import Invention from '../../components/Invention/Invention';

const InventionPage = () => {
    return (
        <SocketLayout namespace="invention" title="Invention 💡">
            {(data) => <Invention data={data.invention} country={data.country} />}
        </SocketLayout>
    );
};

export default InventionPage;
