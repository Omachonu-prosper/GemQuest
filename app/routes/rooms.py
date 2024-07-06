from fastapi import APIRouter, WebSocketDisconnect, WebSocket
from uuid import uuid4
from pydantic import BaseModel
from random_username.generate import generate_username

"""Module for all game room related functionality"""

router = APIRouter()
rooms = {}

class RoomDetails(BaseModel):
    category: str
    no_of_questions: int


class RoomManager:
    async def connect(self, websocket: WebSocket, room_id: str, username: str) -> bool:
        await websocket.accept()
        if not rooms.get(room_id):
            print('room not found')
            return False
        
        rooms[room_id]['connections'].append((username, websocket))
        return True

    def disconnect(self, websocket: WebSocket, room_id: str):
        rooms[room_id]['connections'].remove(websocket)

    # async def send_personal_message(self, message: str, websocket: WebSocket):
    #     await websocket.send_text(message)

    async def broadcast_json(self, room_id: str, data: dict):
        for connection in rooms[room_id]['connections']:
            await connection[1].send_json(data)

    async def close_room(self, room_id: str):
        for connection in rooms[room_id]['connections']:
            await connection[1].close(reason='Room Closed')


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


waitingroom_manager = RoomManager()
gameroom_manager = RoomManager()

@router.websocket('/waitingroom/{room_id}')
async def waitingroom_socket(websocket: WebSocket, room_id: str):
    username = generate_username()[0]
    connect = await waitingroom_manager.connect(websocket, room_id, username)
    if connect:
        try:
            while True:
                data = await websocket.receive_json()
                user_role = data.get('user_role')
                action = data.get('action')
                if user_role.lower() == 'admin' and action.lower() == 'start_game':
                    await waitingroom_manager.broadcast_json(
                        room_id, {
                            'username': username,
                            'room_id': room_id,
                            'action': 'start_game'
                        }
                    )
                    await waitingroom_manager.close_room(room_id)
        except WebSocketDisconnect:
            waitingroom_manager.disconnect(websocket)
    else:
        await websocket.close(reason='Room ID not found')


@router.websocket('/gameroom/{room_id}/{username}')
async def gameroom_socket(websocket: WebSocket, room_id: str, username: str):
    # connect = gameroom_manager.connect(websocket, room_id, username)
    await websocket.accept()
    # if connect:
    print(rooms)
    await websocket.send_text('Welcome to the game')
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(data)
    # else:
        # await websocket.close(reason='Room ID not found')