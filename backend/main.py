import os
import pickle
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sklearn.feature_extraction.text import TfidfVectorizer
from deep_translator import MyMemoryTranslator
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

app = FastAPI()

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the model and stopwords
model = pickle.load(open("LinearSVC.pkl", 'rb'))
with open("stopwords.txt", "r") as my_file:
    content_list = my_file.read().split("\n")

tfidf_vector = TfidfVectorizer(
    stop_words=content_list, 
    lowercase=True, 
    vocabulary=pickle.load(open("tfidf_vector_vocabulary.pkl", "rb"))
)

def is_bullying(text: str) -> bool:
    # Normalize text to catch evasions
    replacements = {'@': 'a', '$': 's', '1': 'i', '0': 'o', '!': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b'}
    for symbol, letter in replacements.items():
        text = text.replace(symbol, letter)
        
    candidates_to_check = [text.lower()]
        
    # Translate Devanagari to English
    if re.search(r'[\u0900-\u097F]', text):
        try:
            translated = MyMemoryTranslator(source='hi-IN', target='en-GB').translate(text)
            candidates_to_check.append(translated.lower())
        except:
            pass
            
        try:
            transliterated = transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
            candidates_to_check.append(transliterated.lower())
        except:
            pass
            
    for candidate in candidates_to_check:
        data_2 = tfidf_vector.fit_transform([candidate])
        pred = model.predict(data_2)
        if pred[0] == 1:
            return True
            
    return False

class ConnectionManager:
    def __init__(self):
        # Maps room_id to list of active WebSockets
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)

    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            # We expect a JSON object like {"username": "deepak", "text": "hello"}
            data = await websocket.receive_json()
            username = data.get("username", "Unknown")
            text = data.get("text", "")
            
            # Predict bullying
            if is_bullying(text):
                # Send error ONLY to the sender
                await websocket.send_json({
                    "type": "alert",
                    "message": "Stop bullying people and behave decently."
                })
            else:
                # Broadcast valid message to the room
                await manager.broadcast({
                    "type": "message",
                    "username": username,
                    "text": text
                }, room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
