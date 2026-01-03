
import os
import glob
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from agent import agent_loop

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (videos) from current directory
# We might want to serve from a specific subdirectory, but agent runs in CWD.
# Warning: Serves everything in CWD. In production this is bad, for this demo it's fine.
app.mount("/videos", StaticFiles(directory="."), name="videos")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Wait for a message (prompt)
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "prompt":
                    prompt = msg.get("content")
                    
                    # Define callback to send updates to WS
                    # Since agent_loop is synchronous (it uses subprocess.run), 
                    # we might block the event loop.
                    # Ideally agent_loop should be async or run in a thread.
                    # For simplicity, we'll run it in a thread executor.
                    
                    queue = asyncio.Queue()
                    
                    def callback(type_, content):
                        # This logs from the agent thread
                        # We need to put it in a queue or use run_coroutine_threadsafe if we were in the loop
                        # But since we are inside an async function, we can't await here directly if called from sync code.
                        # We'll use the queue approach.
                        asyncio.run_coroutine_threadsafe(queue.put({"type": type_, "content": content}), loop)

                    loop = asyncio.get_running_loop()
                    
                    # Start agent in a separate thread
                    await websocket.send_json({"type": "status", "content": "Agent started..."})
                    
                    # We need a task to consume the queue and send to WS
                    async def sender():
                        while True:
                            item = await queue.get()
                            if item is None: break
                            await websocket.send_json(item)
                            
                    sender_task = asyncio.create_task(sender())
                    
                    await asyncio.to_thread(agent_loop, prompt, callback=callback)
                    
                    # Signal sender to stop
                    await queue.put(None)
                    await sender_task
                    
                    # After agent finishes, check for new videos
                    # We look for the most recently modified mp4 file
                    list_of_files = glob.glob('*.mp4')
                    if list_of_files:
                        latest_file = max(list_of_files, key=os.path.getctime)
                        await websocket.send_json({"type": "video", "url": f"http://localhost:8000/videos/{latest_file}"})
                        await websocket.send_json({"type": "status", "content": f"Video created: {latest_file}"})
                    else:
                        await websocket.send_json({"type": "status", "content": "No video found."})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})
            except Exception as e:
                await websocket.send_json({"type": "error", "content": f"Server Error: {str(e)}"})

    except WebSocketDisconnect:
        print("Client disconnected")
