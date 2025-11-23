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
        origin: "*",
        methods: ["GET", "POST"],
    },
});

// Keep track of which socket requested which type
const clientNamespaces = {}; // socket.id -> type

// middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// API routes
app.get("/api/inventions", (req, res) => {
    const dataPath = path.join(__dirname, "api", "inventions.json");
    fs.readFile(dataPath, "utf8", (err, data) => {
        if (err)
            return res.status(500).json({ error: "Could not read inventions data" });
        res.json(JSON.parse(data));
    });
});

app.get("/api/inventions/:country", (req, res) => {
    const country = req.params.country.toLowerCase();
    const dataPath = path.join(__dirname, "api", "inventions.json");
    fs.readFile(dataPath, "utf8", (err, data) => {
        if (err)
            return res.status(500).json({ error: "Could not read inventions data" });

        const inventions = JSON.parse(data);
        const countryData = inventions.find(
            (item) => item.country.toLowerCase() === country
        );

        if (!countryData)
            return res.status(404).json({ error: "Country not found" });
        res.json(countryData);
    });
});

// Socket.IO
io.on("connection", (socket) => {
    console.log("Client connected:", socket.id);

    // Store requested namespace
    socket.on("requestData", (msg) => {
        const { type } = msg;
        socket.join(type);
        clientNamespaces[socket.id] = type;
        console.log(`Client ${socket.id} requested namespace:`, type);

        io.emit("requestDataToNodeRED", msg);
    });

    socket.on("newData", (data) => {
        console.log("Server got newData:", data);

        // Determine the room to emit to
        const room = data.type || clientNamespaces[socket.id] || null;

        if (room) {
            // Emit only to the room
            io.to(room).emit("newData", data.payload ?? data);
        } else {
            // Fallback: emit to all clients
            io.emit("newData", data.payload ?? data);
        }
    });

    socket.on("disconnect", () => {
        delete clientNamespaces[socket.id];
        console.log("Client disconnected:", socket.id);
    });

    // listen to 'newCoordinates' -> show loading
    socket.on("newCoordinates", (data) => {
        console.log("Server got newCoordinates:", data);

        const room = data.type || clientNamespaces[socket.id] || null;

        if (room) {
            io.to(room).emit("newCoordinates", data);
        } else {
            io.emit("newCoordinates", data);
        }
    });
});

// start server
server.listen(3000, () =>
    console.log("Server running at http://localhost:3000")
);
