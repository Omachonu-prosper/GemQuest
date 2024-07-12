from fastapi import WebSocket
from app.utils.db import db


class RoomManager:
    def __init__(self) -> None:
        self.rooms = dict()


    async def connect(
            self, 
            websocket: WebSocket,
            room_id: str, 
            username: str,
            game_started: bool
        ) -> bool:
        """
        Initiate a client connect to a room

        - websocket: The socket connection instance
        - room_id: The id of the room the user wants to join
        - username: The username generated for the client
        - game_started: Boolean value that will be True if the game has started 
            (If this is false the client is added to a wait room and if true the client is added to a game room)
        """
        await websocket.accept()
        room_in_memory = self.rooms.get(room_id)
        if room_in_memory is None:
            return False
        
        room_in_memory.append(websocket)
        room_in_db = await db.rooms.find_one_and_update(
            {'room_id': room_id, 'game_started': game_started},
            {'$set': {f'users.{username}': {
                'status': 'connected',
                }}
            }
        )
        if not room_in_db:
            return False
        return True


    async def disconnect(self, websocket: WebSocket, room_id: str, username: str):
        self.rooms.get(room_id).remove(websocket)
        await db.rooms.update_one(
            {'room_id': room_id},
            {'$unset': {f'users.{username}': ""}}
        )


    async def broadcast_json(self, room_id: str, data: dict, exclude: WebSocket = None):
        for connection in self.rooms.get(room_id):
            if exclude:
                if connection != exclude:
                    await connection.send_json(data)
            else:
                await connection.send_json(data)


    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)