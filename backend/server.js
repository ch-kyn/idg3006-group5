import express from "express";
import http from "http";
import { Server } from "socket.io";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";
import os from "os";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: { origin: "*", methods: ["GET","POST"] },
    transports: ["polling", "websocket"]
});

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

/* -------------------------------------------------------------------------------------- */
// Socket.IO
io.on("connection", (socket) => {
    console.log("Client connected:", socket.id);

    // just forward the request to Node-RED
    socket.on("requestData", (msg) => {
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

    socket.on("coords", (data) => {
        io.emit("coords", data.payload ?? data);
    });

    socket.on("start", (data) => {
        io.emit("start", data.payload ?? data);
    });

    socket.on("stableCoordinatesSent", (data) => {
        // forward the stable coordinates
        io.emit("stableCoordinatesSent", data.payload ?? data);

        // reset Start to false
        io.emit("start", { "start": false });
    });

    socket.on("disconnect", () => {
        console.log("Client disconnected:", socket.id);
    });
});

/* -------------------------------------------------------------------------------------- */
function getLocalIP() {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
        for (const iface of interfaces[name]) {
            if (iface.family === "IPv4" && !iface.internal) {
                return iface.address;
            }
        }
    }
    return "localhost";
}

const port = 3000;
const localIP = getLocalIP();

//  display the local machine's IP address for LAN access and localhost
server.listen(port, '0.0.0.0', () => {
    console.log("Server running at:");
    console.log(`  Local:   http://localhost:${port}`);
    console.log(`  Network: http://${localIP}:${port}`);
});
