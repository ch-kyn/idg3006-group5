import SocketLayout from '../../layouts/SocketLayout.jsx';
import Invention from '../../components/Invention/Invention';
import NotFound from '../../components/NotFound/NotFound.jsx';

const InventionPage = () => {
    return (
        <SocketLayout namespace="invention" title="Invention 💡">
            {(data) => {
                if (data.error) return (<NotFound country={data.requested} />);
                return <Invention data={data.invention} country={data.country} />;
            }}
        </SocketLayout>
    );
};

export default InventionPage;
