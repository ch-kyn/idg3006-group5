import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import Carousel from '../Carousel/Carousel';

const ArtList = () => {
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
		<div>
			<h1>Explore</h1>
			{data &&
				<Carousel artworks={data} />
			}
			{/* <ul>
				{data && data.map((value, index) => (
					<li key={index}>{value}</li>
				))}
			</ul> */}
		</div>
	);
}

export default ArtList;