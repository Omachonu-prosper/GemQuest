from fastapi import APIRouter, WebSocketDisconnect, WebSocket
from uuid import uuid4
from datetime import datetime
from random_username.generate import generate_username

from app.utils.room_manager import RoomManager
from app.utils.room_details import RoomDetails

"""Module for all game room related functionality"""

router = APIRouter()
waitingroom_manager = RoomManager()
# gameroom_manager = RoomManager()


@router.post('/gameroom/create',  status_code=201)
async def create_gameroom_route(room_details: RoomDetails):
    # Generate room id
    room_id = str(uuid4())[:8]
    waitingroom_manager.rooms[room_id] = {
        'category': room_details.category,
        'room_id': room_id,
        'game_started': False,
        'no_of_questions': room_details.no_of_questions,
        'connections': [],
        'create_time': datetime.now()
    }

    print(waitingroom_manager.rooms)
    return {
        'message': 'Room created successfully',
        'room_id': room_id
    }


@router.websocket('/waitingroom/{room_id}')
async def waitingroom_socket(websocket: WebSocket, room_id: str):
    username = generate_username()[0]
    connect = await waitingroom_manager.connect(websocket, room_id, username)
    if connect:
        try:
            await waitingroom_manager.broadcast_json(room_id, {
                'message': f"{username} joined",
                'action': 'join_chat',
                'username': username
            })
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
            waitingroom_manager.disconnect(websocket, room_id)
            await waitingroom_manager.broadcast_json(room_id, {
                'message': f"{username} left",
                'action': 'exit_chat',
                'username': username
            })
    else:
        await websocket.close(reason='Room ID not found')


@router.websocket('/gameroom/{room_id}/{username}')
async def gameroom_socket(websocket: WebSocket, room_id: str, username: str):
    # connect = gameroom_manager.connect(websocket, room_id, username)
    await websocket.accept()
    # if connect:
    print(waitingroom_manager.rooms)
    await websocket.send_text('Welcome to the game')
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(data)
    # else:
        # await websocket.close(reason='Room ID not found')