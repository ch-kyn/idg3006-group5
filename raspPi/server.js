import { Server } from "socket.io";


// Listen on port 8765
const io = new Server(8765, {
  cors: {
    origin: "*", // Allow all origins (adjust for production!)
  }
});

io.on("connection", (socket) => {
  console.log(`✅ Client connected: ${socket.id}`);

  // Listen for "coords" event
  socket.on("coords", (data) => {
    console.log(`Received from ${socket.id}: lat=${data.lat}, lon=${data.lon}`);
  });

  socket.on("disconnect", () => {
    console.log(`❌ Client disconnected: ${socket.id}`);
  });
});

console.log("Socket.IO server running on port 8765...");
