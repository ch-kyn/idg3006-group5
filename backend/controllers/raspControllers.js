import dotenv from "dotenv";
dotenv.config();

export const recieveCoordinates = async (req, res) => {
    try{
        const { lat, lon, token } = req.body;

        //lat check
        if(lat === undefined){
            return res.status(400).json({message: "Latitude is not provided"});    
        }
        //lon check
        if(lon === undefined){
            return res.status(400).json({message: "Longitude is not provided"});
        }

        //check if authenticated
        if(token != process.env.TOKEN){
            return res.status(403).json({message: "Permission denied"});
        }

        return res.status(200).json({
            message: "Coordinates recieved",
            lat: lat,
            lon: lon
        })
    }catch(err){
        return res.status(500).json({ error: err.message });
    }
}