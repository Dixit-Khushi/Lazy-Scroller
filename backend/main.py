from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .gesture_engine import GestureEngine
from .controller import InputController
import cv2
import asyncio
import json
import uvicorn
import os

app = FastAPI()

# Mount Frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if not os.path.exists(frontend_path):
    os.makedirs(frontend_path)

app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))


# Global Instances (Lazy load to avoid startup issues)
gesture_engine = None
input_controller = None

# Global State
active_mode = "HUB" 

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Broadcast JSON message
        txt = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(txt)
            except:
                pass # Handle dead connections

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    global active_mode
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages (e.g. mode switch)
            try:
                msg = json.loads(data)
                if msg.get("type") == "SET_MODE":
                    active_mode = msg.get("mode")
                    print(f"Mode switched to: {active_mode}")
            except:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")

async def video_loop():
    global gesture_engine, input_controller, active_mode
    
    # Initialize
    if gesture_engine is None:
        gesture_engine = GestureEngine()
    if input_controller is None:
        input_controller = InputController()
        
    cap = cv2.VideoCapture(0)
    print("Camera Started")
    
    while True:
        try:
            success, frame = cap.read()
            if not success:
                await asyncio.sleep(0.1)
                continue
                
            frame = cv2.flip(frame, 1) # Mirror
            
            # Process
            data = gesture_engine.process_frame(frame)
            
            if data:
                # Add system state
                data["active_mode"] = active_mode
                
                # Logic Routing based on Mode
                if active_mode == "SCROLLER" or active_mode == "HUB":
                    # OS Control (Mouse) enabled for Navigation and Scrolling
                    if data["scroll_delta"] != 0:
                        input_controller.scroll(data["scroll_delta"])
                    
                    if data.get("click_triggered"):
                        input_controller.click()
                        
                    # Cursor Movement:
                    # In HUB: Always move cursor to allow clicking buttons.
                    # In SCROLLER: Move cursor when not scrolling (pinched).
                    if not data["is_pinched"] and data["cursor"]:
                         input_controller.move_mouse(data["cursor"]["x"], data["cursor"]["y"])

                # Broadcast to Frontend (for Visualization / 3D / AirDraw)
                await manager.broadcast(data)
            
            # 60 FPS cap approx
            await asyncio.sleep(0.016)
            
        except Exception as e:
            print(f"Error in video loop: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def start_video_task():
    asyncio.create_task(video_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
