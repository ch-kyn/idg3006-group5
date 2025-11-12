import express from "express";
import http from "http";
import { Server } from "socket.io";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*", // for the prototype; should probably change otherwise
        methods: ["GET", "POST"]
    }
});

// middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// API routes
app.get("/api/inventions", (req, res) => {
    const dataPath = path.join(__dirname, "api", "inventions.json");
    fs.readFile(dataPath, "utf8", (err, data) => {
        if (err) return res.status(500).json({ error: "Could not read inventions data" });
        res.json(JSON.parse(data));
    });
});

app.get("/api/inventions/:country", (req, res) => {
    const country = req.params.country.toLowerCase();
    const dataPath = path.join(__dirname, "api", "inventions.json");
    fs.readFile(dataPath, "utf8", (err, data) => {
        if (err) return res.status(500).json({ error: "Could not read inventions data" });

        const inventions = JSON.parse(data);
        const countryData = inventions.find(item => item.country.toLowerCase() === country);

        if (!countryData) return res.status(404).json({ error: "Country not found" });
        res.json(countryData);
    });
});

// Socket.IO setup
io.on("connection", (socket) => {
    console.log("Client connected");

    socket.on("newData", (data) => {
        console.log("Received from Node-RED:", data);
        io.emit("newData", data); // send to all clients
    });
});

// Start server
server.listen(3000, () => console.log("Server running at http://localhost:3000"));
