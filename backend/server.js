import express from "express";
import http from "http";
import { Server } from "socket.io";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*", // allow all origins (for prototyping)
        methods: ["GET", "POST"]
    }
});

io.on("connection", (socket) => {
    console.log("Client connected");

    console.log('Hi?')

    socket.on("newData", (data) => {
        console.log("Received from Node-RED:", data);
        io.emit("newData", data); // send to all connected frontends
    });
});

server.listen(3000, () => console.log("Server running at http://localhost:3000"));
