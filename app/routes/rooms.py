from fastapi import APIRouter, WebSocketDisconnect, WebSocket, status, WebSocketException
from fastapi.responses import JSONResponse
from uuid import uuid4
from datetime import datetime
from random_username.generate import generate_username

from app.utils import waitroom_manager, gameroom_manager
from app.utils.models import RoomDetails, ModeratorDetails
from app.utils.gemini import generate_questions, evaluate_user_response
from app.utils.db import db

"""Module for all game room related functionality"""

router = APIRouter()


@router.post('/gameroom/create',  status_code=status.HTTP_201_CREATED)
async def create_gameroom_route(room_details: RoomDetails):
    # Generate room id
    room_id = str(uuid4())[:8]
    token = waitroom_manager.gen_moderator_token()
    room = {
        'category': room_details.category,
        'room_id': room_id,
        'game_started': False,
        'no_of_questions': room_details.no_of_questions,
        'users': {},
        'game_state': 'in_waitroom',
        'create_time': datetime.now(),
        'moderator_token': token
    }
    await db.rooms.insert_one(room)
    waitroom_manager.rooms[room_id] = []
    return JSONResponse(content={
        'message': 'Room created successfully',
        'room_id': room_id,
        'moderator_token': token
    }, status_code=status.HTTP_201_CREATED)


@router.post('/game/{room_id}/start/', status_code=status.HTTP_200_OK)
async def start_game(room_id: str, moderator_details: ModeratorDetails):
    is_moderator = await waitroom_manager.verify_moderator_token(moderator_details.moderator_token, room_id)
    if not is_moderator:
        return JSONResponse(content={
            'message': 'Invalid moderator token for the given room id'
        }, status_code=status.HTTP_401_UNAUTHORIZED)

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
            'message': 'The game has already started or ended'
        }, status_code=status.HTTP_409_CONFLICT)
    
    # Start the game, initialize the gameroom and create questions for that room
    await waitroom_manager.start_game(room_id)
    gameroom_manager.rooms[room_id] = []
    await gameroom_manager.create_room_questions('Technology', 5, room_id)
    return JSONResponse(content={
        'message': 'Game started -> connect to the game socket to continue'
    }, status_code=status.HTTP_200_OK)


@router.websocket('/waitroom/{room_id}')
async def waitroom_socket(websocket: WebSocket, room_id: str):
    username = generate_username()[0]
    connect = await waitroom_manager.connect(websocket, room_id, username, False)
    if connect:
        try:
            # Send the full list of users in the room at the point of entry
            users = await db.rooms.find_one({'room_id': room_id,}, {'_id': 0, 'users': 1})
            await waitroom_manager.send_json(websocket, {
                'users': users.get('users'),
                'current_user': username
            })
            await waitroom_manager.broadcast_json(room_id, {
                'message': f'{username} joined',
                'action': 'join_room',
                'username': username,
            }, exclude=websocket)

            while True:
                # Wait for the start game request
                data = await websocket.receive_text()
                # Sit tight and wait for the game to start
        except WebSocketDisconnect:
            await waitroom_manager.disconnect(websocket, room_id, username)
            await waitroom_manager.broadcast_json(room_id, {
                'message': f"{username} left",
                'action': 'exit_room',
                'username': username
            }, exclude=websocket)
    else:
        await websocket.close(reason='Room not found')


@router.websocket('/gameroom/{room_id}/{username}')
async def gameroom_socket(
        websocket: WebSocket,
        room_id: str,
        username: str,
        moderator_token: str = None
    ):
    connect = await gameroom_manager.connect(websocket, room_id, username, True)
    if connect:
        moderator = False
        if moderator_token:
            moderator = await gameroom_manager.verify_moderator_token(moderator_token, room_id)
            if not moderator:
                # The moderator token is present but invalid
                raise WebSocketException(code=status.WS_1007_INVALID_FRAME_PAYLOAD_DATA)
        
        try:
            question = None

            while True:
                data = await websocket.receive_json()
                
                # Wait for a request to generate a new question
                if moderator and data.get('action') == 'gen_question':
                    # Call the question generation function
                    print('Generating Question')
                    question = generate_question("Computer Science")
                    # Broadcast question
                    # Store question details
                    print(question + "From line 136")
                    await gameroom_manager.broadcast_json(room_id, {
                        'message': 'New question',
                        'question': question
                    })

                # Wait for a client to provide the answer to a question
                if data.get('action') == 'ans_question':
                    # Evaluate answer
                    user_response = data.get('answer')
                    evaluated_response = evaluate_user_response(question, user_response)
                    print("A question was answered")
                    # Send evaluation
                    await gameroom_manager.send_json(websocket, {
                        'message': evaluated_response 
                    })

                    # Store answer
                    pass

                if moderator and data.get('action') == 'game_over':
                    # Braodcast leaderboard
                    await gameroom_manager.broadcast_json(room_id, {'message': 'Game over'})
                    await gameroom_manager.end_game(room_id)
                    break

        except WebSocketDisconnect:
            await gameroom_manager.disconnect(websocket, room_id, username)
    else:
        await websocket.close(reason='Room not found')