from fastapi import WebSocket
from app.utils.db import db


class RoomManager:
    def __init__(self) -> None:
        self.rooms = dict()

    async def connect(self, websocket: WebSocket, room_id: str, username: str) -> bool:
        try:
            await websocket.accept()
            self.rooms[room_id].append(websocket)
            room = await db.rooms.find_one_and_update(
                {'room_id': room_id},
                {'$set': {f'users.{username}': {
                    'status': 'connected',
                    }}
                }
            )
            if not room:
                return False
            return True
        except KeyError:
            return False


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