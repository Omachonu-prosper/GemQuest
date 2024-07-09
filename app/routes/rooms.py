from fastapi import APIRouter, WebSocketDisconnect, WebSocket
from uuid import uuid4
from datetime import datetime
from random_username.generate import generate_username

from app.utils import gameroom_manager
from app.utils.room_details import RoomDetails
from app.utils.db import db

"""Module for all game room related functionality"""

router = APIRouter()
# waitingroom_manager = RoomManager()
# gameroom_manager = RoomManager()


@router.post('/gameroom/create',  status_code=201)
async def create_gameroom_route(room_details: RoomDetails):
    # Generate room id
    room_id = str(uuid4())[:8]
    room = {
        'category': room_details.category,
        'room_id': room_id,
        'game_started': False,
        'no_of_questions': room_details.no_of_questions,
        'users': {},
        'game_state': 'in_waitingroom',
        'create_time': datetime.now()
    }
    await db.rooms.insert_one(room)
    gameroom_manager.rooms[room_id] = []
    return {
        'message': 'Room created successfully',
        'room_id': room_id
    }


@router.get('/game/{room_id}/start/', status_code=200)
async def start_game(room_id: str):
    room = db.rooms.find_one_and_update(
        {'room_id': room_id}, 
        {
            '$set': {
                'game_started': True,
                'game_state': 'game_started'
            }
        }
    )
    if not room:
        return {'message': 'The room_id was not found'}
    
    await gameroom_manager.close_room(room_id)
    return {'message': 'Game started -> connect to the game socket to continue'}


@router.websocket('/waitingroom/{room_id}')
async def waitingroom_socket(websocket: WebSocket, room_id: str):
    username = generate_username()[0]
    connect = await gameroom_manager.connect(websocket, room_id, username)
    if connect:
        try:
            users = await db.rooms.find_one({'room_id': room_id,}, {'_id': 0, 'users': 1})
            await gameroom_manager.send_json(websocket, {
                'users': users.get('users'),
                'current_user': username
            })
            await gameroom_manager.broadcast_json(room_id, {
                'message': f'{username} joined',
                'action': 'join_chat',
                'username': username,
            }, exclude=websocket)

            while True:
                # Wait for the start game request
                data = await websocket.receive_text()
                await websocket.send_text(data)
        except WebSocketDisconnect:
            await gameroom_manager.disconnect(websocket, room_id, username)
            await gameroom_manager.broadcast_json(room_id, {
                'message': f"{username} left",
                'action': 'exit_chat',
                'username': username
            }, exclude=websocket)
    else:
        await websocket.close(reason='Room ID not found')


@router.websocket('/gameroom/{room_id}/{username}')
async def gameroom_socket(websocket: WebSocket, room_id: str, username: str):
    # connect = gameroom_manager.connect(websocket, room_id, username)
    await websocket.accept()
    # if connect:
    print(gameroom_manager.rooms)
    await websocket.send_text('Welcome to the game')
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(data)
    # else:
        # await websocket.close(reason='Room ID not found')