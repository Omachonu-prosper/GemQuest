from fastapi import APIRouter, WebSocketDisconnect, WebSocket
from uuid import uuid4
from pydantic import BaseModel

"""Module for all game room related functionality"""

router = APIRouter()
rooms = {}

class RoomDetails(BaseModel):
    category: str
    no_of_questions: int


class RoomManager:
    async def connect(self, websocket: WebSocket, room_id: str) -> bool:
        await websocket.accept()
        if not rooms.get(room_id):
            print('room not found')
            return False
        
        rooms[room_id]['connections'].append(websocket)
        return True

    def disconnect(self, websocket: WebSocket, room_id: str):
        rooms[room_id]['connections'].remove(websocket)

    # async def send_personal_message(self, message: str, websocket: WebSocket):
    #     await websocket.send_text(message)

    async def broadcast(self, room_id: str, message: str):
        for connection in rooms[room_id]['connections']:
            await connection.send_text(message)


@router.post('/gameroom/create',  status_code=201)
async def create_gameroom_route(room_details: RoomDetails):
    # Generate room id
    room_id = str(uuid4())[:8]
    rooms[room_id] = {
        'category': room_details.category,
        'room_id': room_id,
        'game_started': False,
        'no_of_questions': room_details.no_of_questions,
        'connections': []
    }

    print(rooms)
    return {
        'message': 'Room created successfully',
        'room_id': room_id
    }


room_manager = RoomManager()

@router.websocket('/gameroom/{room_id}')
async def gameroom_socket(websocket: WebSocket, room_id: str):
    connect = await room_manager.connect(websocket, room_id)
    if connect:
        print(rooms)
        try:
            await websocket.send_text('Welcome to the game')
            while True:
                data = await websocket.receive_text()
                await room_manager.broadcast(f"Client says: {data}")
        except WebSocketDisconnect:
            room_manager.disconnect(websocket)
            await room_manager.broadcast("Someone left the game")
    else:
        await websocket.close(reason='Room ID not found')