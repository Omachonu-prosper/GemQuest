from fastapi import APIRouter, WebSocketDisconnect, WebSocket, status
from fastapi.responses import JSONResponse
from uuid import uuid4
from datetime import datetime
from random_username.generate import generate_username

from app.utils import waitroom_manager
from app.utils.room_details import RoomDetails
from app.utils.db import db

"""Module for all game room related functionality"""

router = APIRouter()


@router.post('/gameroom/create',  status_code=status.HTTP_201_CREATED)
async def create_gameroom_route(room_details: RoomDetails):
    # Generate room id
    room_id = str(uuid4())[:8]
    room = {
        'category': room_details.category,
        'room_id': room_id,
        'game_started': False,
        'no_of_questions': room_details.no_of_questions,
        'users': {},
        'game_state': 'in_waitroom',
        'create_time': datetime.now()
    }
    await db.rooms.insert_one(room)
    waitroom_manager.rooms[room_id] = []
    return JSONResponse(content={
        'message': 'Room created successfully',
        'room_id': room_id
    }, status_code=status.HTTP_201_CREATED)


@router.get('/game/{room_id}/start/', status_code=status.HTTP_200_OK)
async def start_game(room_id: str):
    room = await db.rooms.update_one(
        {'room_id': room_id}, 
        {
            '$set': {
                'game_started': True,
                'game_state': 'game_started'
            }
        }
    )
    if not room.matched_count:
        return JSONResponse(content={
            'message': 'The room_id was not found'
        }, status_code=status.HTTP_404_NOT_FOUND)
    elif not room.modified_count:
        return JSONResponse(content={
            'message': 'The game has already started'
        }, status_code=status.HTTP_409_CONFLICT)
    
    await waitroom_manager.start_game(room_id)
    return JSONResponse(content={
        'message': 'Game started -> connect to the game socket to continue'
    }, status_code=status.HTTP_200_OK)


@router.websocket('/waitroom/{room_id}')
async def waitroom_socket(websocket: WebSocket, room_id: str):
    username = generate_username()[0]
    connect = await waitroom_manager.connect(websocket, room_id, username, False)
    if connect:
        try:
            users = await db.rooms.find_one({'room_id': room_id,}, {'_id': 0, 'users': 1})
            await waitroom_manager.send_json(websocket, {
                'users': users.get('users'),
                'current_user': username
            })
            await waitroom_manager.broadcast_json(room_id, {
                'message': f'{username} joined',
                'action': 'join_chat',
                'username': username,
            }, exclude=websocket)

            while True:
                # Wait for the start game request
                data = await websocket.receive_text()
                await websocket.send_text(data)
        except WebSocketDisconnect:
            print('disconnecting')
            await waitroom_manager.disconnect(websocket, room_id, username)
            await waitroom_manager.broadcast_json(room_id, {
                'message': f"{username} left",
                'action': 'exit_chat',
                'username': username
            }, exclude=websocket)
    else:
        await websocket.close(reason='Room ID not found')


@router.websocket('/gameroom/{room_id}/{username}')
async def gameroom_socket(websocket: WebSocket, room_id: str, username: str):
    # connect = waitroom_manager.connect(websocket, room_id, username)
    await websocket.accept()
    # if connect:
    # print(gameroom_manager.rooms)
    await websocket.send_text('Welcome to the game')
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(data)
    # else:
        # await websocket.close(reason='Room ID not found')