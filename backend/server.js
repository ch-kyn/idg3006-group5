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
    cors: { origin: "*", methods: ["GET","POST"] }
});

// Track requested namespaces
const clientNamespaces = {};

app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// API routes
// for "Invention"
app.get("/api/inventions", (req, res) => {
    const dataPath = path.join(__dirname, "api", "inventions.json");
    fs.readFile(dataPath, "utf8", (err, data) => {
        if (err) return res.status(500).json({ error: "Could not read 'inventions' data" });
        res.json(JSON.parse(data));
    });
});

app.get("/api/inventions/:country", (req, res) => {
    const country = req.params.country.toLowerCase();
    const dataPath = path.join(__dirname, "api", "inventions.json");
    fs.readFile(dataPath, "utf8", (err, data) => {
        if (err) return res.status(500).json({ error: "Could not read 'inventions' data" });

        const inventions = JSON.parse(data);
        const countryData = inventions.find(item => item.country.toLowerCase() === country);

        if (!countryData) {
            return res.status(404).json({
                error: "Inventions not found",
                requested: country
            });
        }
        
        res.json(countryData);
    });
});


// for "About"
app.get("/api/countries", (req, res) => {
    const dataPath = path.join(__dirname, "api", "countries.json");
    fs.readFile(dataPath, "utf8", (err, data) => {
        if (err) return res.status(500).json({ error: "Could not read 'countries' data" });
        res.json(JSON.parse(data));
    });
});

app.get("/api/countries/:country", (req, res) => {
    const country = req.params.country.toLowerCase();
    const dataPath = path.join(__dirname, "api", "countries.json");
    fs.readFile(dataPath, "utf8", (err, data) => {
        if (err) return res.status(500).json({ error: "Could not read 'countries' data" });

        const inventions = JSON.parse(data);
        const countryData = inventions.find(item => item.country.toLowerCase() === country);
        
        if (!countryData) {
            return res.status(404).json({
                error: "Country not found",
                requested: country
            });
        }


        res.json(countryData);
    });
});

// Socket.IO
io.on("connection", (socket) => {
    console.log("Client connected:", socket.id);

    socket.on("requestData", (msg) => {
        // just forward the request to Node-RED
        io.emit("requestData", msg);
    });

    socket.on("control", (data) => {
        console.log("Control received:", data);
        io.emit("control", data); // send to all, including sender
    });

    socket.on("newData", (data) => {
        // Emit to all clients without rooms
        io.emit("newData", data.payload ?? data);
    });

    socket.on("loading", (data) => {
        io.emit("loading", data.payload ?? data);
    });

    socket.on("disconnect", () => {
        console.log("Client disconnected:", socket.id);
    });
});

server.listen(3000, '0.0.0.0', () => console.log("Server running at http://localhost:3000"));
